import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/native.sh"
BUNDLE = Path("test/Plugins/Window Style.bundle")


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "tools"
        self.bin.mkdir()
        for command, path in {
            "python3": sys.executable,
            "grep": "/usr/bin/grep",
            "head": "/usr/bin/head",
            "sed": "/usr/bin/sed",
        }.items():
            (self.bin / command).symlink_to(path)
        self.env = {
            **os.environ,
            "PATH": str(self.bin),
            "PRODUCT_NAME": "Window Style",
            "XCODE_PROJECT": "Window Style.xcodeproj",
            "MACOS_DEPLOYMENT_TARGET": "11.0",
            "KEYCHAIN_PATH": "fake.keychain",
            "VERSION": "2.0.4",
            "BUNDLE_PATH": str(BUNDLE),
            "GITHUB_ENV": str(self.root / "env"),
            "CALL_LOG": str(self.root / "calls"),
            "RUNNER_TEMP": str(self.root),
            "CERT_BASE64": "synthetic-certificate",
            "CERT_PASSWORD": "synthetic-password",
            "KEYCHAIN_PASSWORD": "synthetic-keychain-password",
            "APPLE_ID": "synthetic@example.invalid",
            "TEAM_ID": "SYNTHETIC",
            "APP_PASSWORD": "synthetic-notary-password",
        }
        self.stub("xcodebuild", """
import pathlib, sys
args = sys.argv[1:]
assert "-configuration" in args and args[args.index("-configuration")+1] == "Default"
assert "ARCHS=arm64 x86_64" in args
assert "ONLY_ACTIVE_ARCH=NO" in args
assert "MACOSX_DEPLOYMENT_TARGET=11.0" in args
assert "CONFIGURATION_BUILD_DIR=" + str(pathlib.Path.cwd() / "test/Plugins") in args
p = pathlib.Path("test/Plugins/Window Style.bundle/Contents/MacOS/Window Style")
assert not p.exists(), "stale executable survived"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_bytes(b"fresh executable")
""")
        self.stub("lipo", 'import os\nprint(os.environ.get("ARCHS_RESULT", "arm64 x86_64"))')
        self.stub("security", 'print(\'1) FAKE "Developer ID Application: Fixture"\')')
        self.stub("base64", """
import pathlib,sys
assert sys.argv[1:3] == ["--decode", "-o"]
assert sys.stdin.read() == "synthetic-certificate"
pathlib.Path(sys.argv[3]).write_bytes(b"synthetic-p12")
""")
        self.stub("codesign", """
import os, sys
if "--verify" in sys.argv and os.environ.get("BAD_SIGN"):
    sys.exit(1)
""")
        self.stub("ditto", 'import pathlib,sys\npathlib.Path(sys.argv[-1]).write_bytes(b"zip")')
        self.stub("hdiutil", 'import pathlib,sys\npathlib.Path(sys.argv[-1]).write_bytes(b"dmg")')
        self.stub("xcrun", """
import json,os,sys
if sys.argv[1] == "notarytool":
    if sys.argv[2] == "store-credentials":
        sys.exit(0)
    print(json.dumps({"status": os.environ.get("NOTARY_STATUS", "Accepted")}))
    sys.exit(int(os.environ.get("NOTARY_EXIT", "0")))
if sys.argv[1] == "stapler":
    sys.exit(int(os.environ.get("STAPLE_EXIT", "0")))
raise AssertionError(sys.argv)
""")

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(
            f"#!{sys.executable}\n"
            "import os,sys\n"
            "with open(os.environ['CALL_LOG'],'a') as log:\n"
            "    log.write(repr(sys.argv)+'\\n')\n" + body
        )
        path.chmod(0o755)

    def run_phase(self, phase, success=True, **extra):
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT), phase],
            cwd=self.root, env={**self.env, **extra}, capture_output=True, text=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def write(self, relative, data=b"keep"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_build_freshness_and_resource_preservation(self):
        self.write(BUNDLE / "Contents/MacOS/Window Style", b"stale")
        self.write(BUNDLE / "Contents/Info.plist", b"stale")
        self.write(BUNDLE / "Contents/Resources/English.lproj/InfoPlist.strings", b"stale")
        self.write(BUNDLE / "Contents/_CodeSignature/CodeResources", b"stale")
        self.write(Path("build/Default/Window Style.build/stale.o"))
        preserved = [
            self.write(BUNDLE / "Contents/Windows64/Window Style.4DX"),
            self.write(BUNDLE / "Contents/QuickLook/Thumbnail.png"),
            self.write(BUNDLE / "Contents/Resources/constants.xlf"),
            self.write(BUNDLE / "Contents/Resources/manifest.json"),
            self.write(Path("a/libjsoncpp.a")),
            self.write(Path("build/dependency/keep.o")),
            self.write(Path("test/Plugins/Other.bundle/keep")),
        ]
        self.run_phase("build")
        self.assertEqual((self.root / BUNDLE / "Contents/MacOS/Window Style").read_bytes(),
                         b"fresh executable")
        for path in preserved:
            self.assertEqual(path.read_bytes(), b"keep")
        self.assertFalse((self.root / BUNDLE / "Contents/Info.plist").exists())
        self.assertFalse((self.root / "build/Default/Window Style.build").exists())

    def test_certificate_and_credentials_use_isolated_keychain(self):
        self.run_phase("import-certificate")
        self.run_phase("store-credentials")
        self.assertEqual((self.root / "certificate.p12").read_bytes(), b"synthetic-p12")
        self.assertIn("build.keychain-db", (self.root / "env").read_text())
        log = (self.root / "calls").read_text()
        self.assertIn("'set-key-partition-list'", log)
        self.assertIn("'store-credentials', 'notarytool-profile'", log)

    def test_cleanup_failure_stops_before_native(self):
        self.write(BUNDLE / "Contents/Info.plist/invalid")
        self.run_phase("build", success=False)
        self.assertFalse((self.root / "calls").exists())

    def test_symlink_cleanup_rejected(self):
        target = self.root / "unrelated"
        target.mkdir()
        path = self.root / BUNDLE
        path.parent.mkdir(parents=True)
        path.symlink_to(target, target_is_directory=True)
        self.run_phase("build", success=False)
        self.assertFalse((self.root / "calls").exists())

    def test_architecture_tokens(self):
        self.write(BUNDLE / "Contents/MacOS/Window Style")
        self.run_phase("verify")
        self.run_phase("verify", ARCHS_RESULT="i386 x86_64 arm64 arm64e")
        for arches in ("arm64e x86_64", "arm64 x86_64h", "x86_64", ""):
            with self.subTest(arches=arches):
                self.run_phase("verify", success=False, ARCHS_RESULT=arches)

    def test_signing_requires_strict_verification(self):
        self.run_phase("sign")
        log = (self.root / "calls").read_text()
        self.assertIn("--options=runtime", log)
        self.assertIn("--strict", log)
        self.run_phase("sign", success=False, BAD_SIGN="1")

    def test_package_acceptance(self):
        self.run_phase("package")
        log = (self.root / "calls").read_text()
        self.assertEqual(log.count("'submit'"), 2)
        self.assertIn("'stapler', 'staple'", log)
        self.assertIn("--strict", log)
        self.assertIn("ZIP_PATH=Window Style-2.0.4.zip", (self.root / "env").read_text())

    def test_notary_and_staple_fail_closed(self):
        for extra in (
            {"NOTARY_STATUS": "Invalid"}, {"NOTARY_STATUS": "In Progress"},
            {"NOTARY_EXIT": "1"}, {"STAPLE_EXIT": "1"}, {"BAD_SIGN": "1"},
        ):
            with self.subTest(extra=extra):
                for suffix in ("zip", "dmg"):
                    (self.root / f"Window Style-2.0.4.{suffix}").unlink(missing_ok=True)
                self.run_phase("package", success=False, **extra)
                self.assertFalse((self.root / "env").exists())

    def test_malformed_notary_json_fails(self):
        self.stub("xcrun", 'print("not json")')
        self.run_phase("package", success=False)


if __name__ == "__main__":
    unittest.main()
