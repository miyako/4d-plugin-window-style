"""Read-only immutable-history checks; standard library only."""

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
BASE = "0381474c54fc218cb9a6eb1ff92ff00b50984e7f"
CHANGED = {
    "4D Plugin API/Classes/ARRAY_TEXT.h",
    "4D Plugin API/Classes/C_BLOB.h",
    "4D Plugin API/Classes/C_BLOB.cpp",
    "support/4DPlugin-JSON.cpp",
    "4DPlugin-Window-Style.cpp",
    "README.md",
}


def original(path):
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{BASE}:{path}"])


class PreservationTests(unittest.TestCase):
    def test_all_other_baseline_files_unchanged(self):
        paths = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", "-z", BASE]
        ).decode().split("\0")
        for path in filter(None, paths):
            if path not in CHANGED:
                with self.subTest(path=path):
                    self.assertEqual((ROOT / path).read_bytes(), original(path))

    def test_complete_native_inventory(self):
        paths = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", BASE]
        ).decode().splitlines()
        actual = {p for p in paths if Path(p).suffix in (".c", ".cpp", ".mm", ".m")}
        expected = {
            "4D Plugin API/4DPluginAPI.c", "4DPlugin-Window-Style.cpp",
            "support/4DPlugin-JSON.cpp",
            *("4D Plugin API/Classes/" + n + ".cpp"
              for n in ("ARRAY_TEXT", "C_BLOB", "C_LONGINT", "C_TEXT")),
        }
        self.assertEqual(actual, expected)

    def test_both_manifests_identical_to_baseline(self):
        for path in ("manifest.json", "test/Plugins/Window Style.bundle/Contents/Resources/manifest.json"):
            manifest = json.loads((ROOT / path).read_bytes())
            self.assertEqual(manifest, json.loads(original(path)))
            self.assertEqual(len(manifest["commands"]), 1)
            self.assertEqual(manifest["commands"][0]["syntax"], "SET WINDOW STYLE(&L;&J)")

    def test_narrow_unsigned_workflow(self):
        self.assertEqual((ROOT / ".github/workflows/ownership.yml").read_text(),
                         """name: Ownership

on:
  push:
    branches:
      - miyako-window-style-ownership
      - main
    paths:
      - '4D Plugin API/**'
      - '4DPlugin-Window-Style.*'
      - 'support/**'
      - '.github/tests/**'
      - '.github/workflows/ownership.yml'

permissions:
  contents: read

jobs:
  synthetic-ownership:
    runs-on: macos-latest
    env:
      PYTHONDONTWRITEBYTECODE: '1'
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.sha }}
          fetch-depth: 0
      - name: Complete actual sources, synthetic boundaries, ASan and UBSan
        run: python3 .github/tests/test_ownership.py
      - name: Immutable baseline with identical final harness
        run: python3 .github/tests/test_ownership_baseline.py
      - name: Protect SDK, release automation, manifests and binaries
        run: python3 .github/tests/test_ownership_preservation.py
""")

    def test_existing_workflows_and_scripts_unchanged(self):
        for directory in (".github/workflows", ".github/scripts", ".github/hooks"):
            paths = subprocess.check_output(
                ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", BASE, directory]
            ).decode().splitlines()
            for path in paths:
                with self.subTest(path=path):
                    self.assertEqual((ROOT / path).read_bytes(), original(path))

    def test_sdk_and_build_memberships_unchanged(self):
        paths = [
            "4D Plugin API/" + name for name in (
                "4DPluginAPI.c", "4DPluginAPI.h", "4DPluginAPI.def",
                "EntryPoints.h", "Flags.h", "PrivateTypes.h", "PublicTypes.h",
            )
        ] + ["Window Style.vcxproj", "Window Style.vcxproj.filters",
             "Window Style.sln", "Window Style.xcodeproj/project.pbxproj",
             "Window Style.xcodeproj/xcshareddata/xcschemes/Window Style.xcscheme"]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(), original(path))


if __name__ == "__main__":
    unittest.main()
