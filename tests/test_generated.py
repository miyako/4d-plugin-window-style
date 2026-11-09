"""The final publication exemption is smaller than the bundle or build roots."""

import unittest

from helper_support import source
import native


class GeneratedOutputTests(unittest.TestCase):
    def test_exact_native_files_and_controlled_directory_descendants(self):
        expected = (
            "test/Plugins/Window Style.bundle/Contents/MacOS/Window Style",
            "test/Plugins/Window Style.bundle/Contents/Info.plist",
            "test/Plugins/Window Style.bundle/Contents/Resources/English.lproj/InfoPlist.strings",
            "test/Plugins/Window Style.bundle/Contents/_CodeSignature/CodeResources",
            "build/Window Style.build/Objects-normal/arm64/main.o",
            "build/Default/Window Style.build/build.db",
            "test/Plugins/Window Style.build/Objects/file.o",
            "test/Plugins/Default/Window Style.build/Objects/file.o",
        )
        for path in expected:
            with self.subTest(path=path):
                self.assertTrue(native.generated(path))

    def test_every_resource_source_or_unproven_output_stays_protected(self):
        excluded = (
            "test/Plugins/Window Style.bundle/Contents/MacOS/runtime.dylib",
            "test/Plugins/Window Style.bundle/Contents/Windows64/Window Style.4DX",
            "test/Plugins/Window Style.bundle/Contents/Resources/manifest.json",
            "test/Plugins/Window Style.bundle/Contents/QuickLook/Thumbnail.png",
            "test/Plugins/Default/Window Style.bundle/Contents/Info.plist",
            "test/Plugins/Default/keep", "build/XCBuildData/build.db",
            "build/Window Style.build-evil/injected.cpp",
            "test/Plugins/Window Style.bundle/Contents/_CodeSignature-evil/file",
            "test/Plugins/Window Style.bundle/Contents/Info.plist.backup",
            *map(str, source.SOURCE_PATHS),
        )
        for path in excluded:
            with self.subTest(path=path):
                self.assertFalse(native.generated(path))
