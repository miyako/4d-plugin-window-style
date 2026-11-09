#!/bin/bash
set -euo pipefail

case "$1" in
  import-certificate)
    KEYCHAIN_PATH="$RUNNER_TEMP/build.keychain-db"
    CERT_PATH="$RUNNER_TEMP/certificate.p12"
    printf '%s' "$CERT_BASE64" | base64 --decode -o "$CERT_PATH"
    security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
    security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
    security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
    security import "$CERT_PATH" -P "$CERT_PASSWORD" -A -t cert -f pkcs12 -k "$KEYCHAIN_PATH"
    security list-keychain -d user -s "$KEYCHAIN_PATH" login.keychain
    security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
    echo "KEYCHAIN_PATH=$KEYCHAIN_PATH" >> "$GITHUB_ENV"
    ;;
  store-credentials)
    xcrun notarytool store-credentials "notarytool-profile" \
      --apple-id "$APPLE_ID" \
      --team-id "$TEAM_ID" \
      --password "$APP_PASSWORD" \
      --keychain "$KEYCHAIN_PATH"
    ;;
  build)
    python3 - <<'PY'
from pathlib import Path
import shutil

bundle = Path("test/Plugins/Window Style.bundle")
files = [
    bundle / "Contents/MacOS/Window Style",
    bundle / "Contents/Info.plist",
    bundle / "Contents/Resources/English.lproj/InfoPlist.strings",
]
directories = [
    bundle / "Contents/_CodeSignature",
    Path("build/Window Style.build"),
    Path("build/Default/Window Style.build"),
    Path("test/Plugins/Window Style.build"),
    Path("test/Plugins/Default/Window Style.build"),
]
for path in files + directories:
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise SystemExit(f"Refusing symlink cleanup: {path}")
for path in files:
    path.unlink(missing_ok=True)
for path in directories:
    if path.exists():
        shutil.rmtree(path)
PY
    xcodebuild -project "$XCODE_PROJECT" \
      -target "$PRODUCT_NAME" \
      -configuration Default \
      ARCHS="arm64 x86_64" \
      ONLY_ACTIVE_ARCH=NO \
      MACOSX_DEPLOYMENT_TARGET="$MACOS_DEPLOYMENT_TARGET" \
      CONFIGURATION_BUILD_DIR="$PWD/test/Plugins" \
      build
    ;;
  verify)
    BIN="test/Plugins/Window Style.bundle/Contents/MacOS/Window Style"
    test -s "$BIN"
    ARCHITECTURES=$(lipo -archs "$BIN")
    arm=false
    intel=false
    for architecture in $ARCHITECTURES; do
      case "$architecture" in
        arm64) arm=true ;;
        x86_64) intel=true ;;
      esac
    done
    if [ "$arm" != true ] || [ "$intel" != true ]; then
      echo "Required exact arm64 and x86_64 architectures: $ARCHITECTURES" >&2
      exit 1
    fi
    echo "BUNDLE_PATH=test/Plugins/Window Style.bundle" >> "$GITHUB_ENV"
    ;;
  sign)
    IDENTITY=$(security find-identity -v -p codesigning "$KEYCHAIN_PATH" \
      | grep "Developer ID Application" | head -1 | sed -E 's/.*"(.*)".*/\1/')
    test -n "$IDENTITY"
    codesign --verbose --deep --timestamp --force --options=runtime \
      --sign "$IDENTITY" "$BUNDLE_PATH"
    codesign --verify --deep --strict --verbose=2 "$BUNDLE_PATH"
    ;;
  package)
    ZIP_PATH="${PRODUCT_NAME}-${VERSION}.zip"
    DMG_PATH="${PRODUCT_NAME}-${VERSION}.dmg"
    test ! -e "$ZIP_PATH"
    test ! -e "$DMG_PATH"
    ditto -c -k --keepParent "$BUNDLE_PATH" "$ZIP_PATH"
    hdiutil create -format UDBZ -volname "$PRODUCT_NAME" -srcfolder "$BUNDLE_PATH" "$DMG_PATH"
    for artifact in "$ZIP_PATH" "$DMG_PATH"; do
      response=$(xcrun notarytool submit "$artifact" \
        --keychain-profile "notarytool-profile" --keychain "$KEYCHAIN_PATH" \
        --wait --output-format json)
      printf '%s' "$response" | python3 -c \
        'import json,sys; result=json.load(sys.stdin); sys.exit(0 if isinstance(result,dict) and result.get("status") == "Accepted" else "Notarization was not Accepted: " + repr(result))'
    done
    xcrun stapler staple "$DMG_PATH"
    codesign --verify --deep --strict --verbose=2 "$BUNDLE_PATH"
    echo "ZIP_PATH=$ZIP_PATH" >> "$GITHUB_ENV"
    echo "DMG_PATH=$DMG_PATH" >> "$GITHUB_ENV"
    ;;
  *)
    echo "Unknown native phase: $1" >&2
    exit 1
    ;;
esac
