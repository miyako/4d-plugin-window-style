"""Classify only this project's proven generated outputs for final publication."""

from pathlib import Path


PRODUCT = "Window Style"
BUNDLE = Path("test/Plugins") / (PRODUCT + ".bundle")
FILES = tuple(BUNDLE / relative for relative in (
    f"Contents/MacOS/{PRODUCT}",
    "Contents/Info.plist",
    "Contents/Resources/English.lproj/InfoPlist.strings",
))
DIRECTORIES = (
    BUNDLE / "Contents/_CodeSignature",
    Path("build/Window Style.build"),
    Path("build/Default/Window Style.build"),
    Path("test/Plugins/Window Style.build"),
    Path("test/Plugins/Default/Window Style.build"),
)


def generated(path):
    return (path in set(map(str, FILES))
            or any(path.startswith(str(directory) + "/") for directory in DIRECTORIES))
