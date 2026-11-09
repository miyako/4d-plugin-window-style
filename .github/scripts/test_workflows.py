from pathlib import Path
import re
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
INTAKE = "095b5f82d37a1fcdd333f3d2be19c7350b010a5a"


def original(path):
    return subprocess.check_output(["git", "show", f"{INTAKE}:{path}"], cwd=ROOT)


def workflow(name):
    return yaml.load((ROOT / ".github/workflows" / name).read_bytes(), Loader=yaml.BaseLoader)


class WorkflowTests(unittest.TestCase):
    def test_manual_ui_and_independence(self):
        bump, build = workflow("bump-version.yml"), workflow("release.yml")
        self.assertEqual(bump["name"], "Bump version")
        self.assertEqual(list(bump["on"]), ["workflow_dispatch"])
        inputs = bump["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(list(inputs), ["mode"])
        self.assertEqual(inputs["mode"]["type"], "choice")
        self.assertEqual(inputs["mode"]["options"], ["patch", "minor", "major"])
        self.assertEqual(inputs["mode"]["default"], "patch")
        self.assertEqual(inputs["mode"]["required"], "true")
        self.assertEqual(build["name"], "Build")
        self.assertEqual(build["on"], {"workflow_dispatch": ""})
        bump_run = "\n".join(step.get("run", "") for step in bump["jobs"]["bump"]["steps"])
        self.assertEqual(bump_run, '\npython3 .github/scripts/bump.py "$MODE" --sha "$EVENT_SHA" --ref "$EVENT_REF"')
        self.assertNotRegex(bump_run, r"release|dispatch|native|tag")
        build_run = "\n".join(step.get("run", "")
                              for job in build["jobs"].values() for step in job["steps"])
        self.assertNotIn("bump.py", build_run)
        self.assertNotIn("softprops", str(build))
        self.assertNotIn("inputs.", str(build))

    def test_every_checkout_uses_event_sha(self):
        for name in ("bump-version.yml", "release.yml"):
            for job in workflow(name)["jobs"].values():
                checkouts = [step for step in job["steps"]
                             if step.get("uses", "").startswith("actions/checkout@")]
                self.assertEqual(len(checkouts), 1)
                self.assertEqual(checkouts[0]["with"]["ref"], "${{ github.sha }}")
                self.assertNotIn("if", job)

    def test_cross_ref_publication_concurrency(self):
        concurrency = workflow("release.yml")["concurrency"]
        self.assertEqual(concurrency["cancel-in-progress"], "false")
        self.assertNotIn("${{", concurrency["group"])
        self.assertNotEqual(concurrency["group"],
                            workflow("bump-version.yml")["concurrency"]["group"])

    def test_actual_original_topology_preserved(self):
        before = yaml.load(original(".github/workflows/release.yml"), Loader=yaml.BaseLoader)
        after = workflow("release.yml")
        self.assertEqual(list(before["jobs"]), list(after["jobs"]))
        for job in before["jobs"]:
            self.assertEqual(before["jobs"][job]["runs-on"], after["jobs"][job]["runs-on"])
            self.assertEqual(before["jobs"][job].get("needs"), after["jobs"][job].get("needs"))
        self.assertEqual(before["env"]["MACOS_DEPLOYMENT_TARGET"],
                         after["env"]["MACOS_DEPLOYMENT_TARGET"])
        self.assertEqual(after["env"]["PRODUCT_NAME"], "Window Style")
        self.assertEqual(after["env"]["XCODE_PROJECT"], "Window Style.xcodeproj")
        self.assertNotIn("VCX_SOLUTION", after["env"])
        self.assertEqual(set(before["on"]), {"push", "workflow_dispatch"})
        self.assertEqual(before["on"]["push"]["tags"], ["v*.*.*"])
        self.assertEqual(set(before["on"]["workflow_dispatch"]["inputs"]), {"tag"})
        self.assertEqual(set(before["jobs"]), {"version", "build-macos"})

    def test_preflight_precedes_every_native_operation_and_final_publish_is_last(self):
        steps = workflow("release.yml")["jobs"]["build-macos"]["steps"]
        runs = [step["run"] for step in steps if "run" in step]
        self.assertIn("release.py preflight", runs[0])
        self.assertIn("release.py publish", runs[-1])
        self.assertEqual([run for run in runs if "native.sh" in run], [
            "bash .github/scripts/native.sh import-certificate",
            "bash .github/scripts/native.sh store-credentials",
            "bash .github/scripts/native.sh build",
            'bash .github/scripts/native.sh verify\npython3 .github/scripts/source_version.py --verify-bundle "test/Plugins/Window Style.bundle"\n',
            "bash .github/scripts/native.sh sign",
            "bash .github/scripts/native.sh package",
        ])
        for run in runs:
            self.assertNotIn("${{", run)
        self.assertEqual(steps[1]["env"]["GH_TOKEN"], "${{ github.token }}")
        self.assertEqual(steps[-1]["env"]["GH_TOKEN"], "${{ github.token }}")

    def test_original_native_project_unchanged_except_proven_source_versions(self):
        path = "Window Style.xcodeproj/project.pbxproj"
        normalize = lambda data: re.sub(
            rb"((?:MARKETING_VERSION|CURRENT_PROJECT_VERSION)\s*=\s*)[0-9.]+;",
            rb"\g<1>VERSION;", data)
        self.assertEqual(normalize(original(path)), normalize((ROOT / path).read_bytes()))
        for path in ("Window Style.vcxproj", "Info.plist", "constants.xlf", "manifest.json",
                     "a/libjsoncpp.a", "lib/windows/jsoncpp.lib", "lib/windows64/jsoncpp.lib"):
            with self.subTest(path=path):
                self.assertEqual(original(path), (ROOT / path).read_bytes())

    def test_prebuilt_bundle_is_not_migration_source(self):
        paths = (
            "Contents/Info.plist",
            "Contents/Resources/English.lproj/InfoPlist.strings",
            "Contents/MacOS/Window Style",
            "Contents/Windows64/Window Style.4DX",
            "Contents/Resources/constants.xlf", "Contents/Resources/manifest.json",
            "Contents/QuickLook/Thumbnail.png", "Contents/_CodeSignature/CodeResources",
        )
        for suffix in paths:
            path = "test/Plugins/Window Style.bundle/" + suffix
            with self.subTest(path=path):
                self.assertEqual(original(path), (ROOT / path).read_bytes())


if __name__ == "__main__":
    unittest.main()
