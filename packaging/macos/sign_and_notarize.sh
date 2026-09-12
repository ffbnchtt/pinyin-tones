#!/usr/bin/env bash
set -euo pipefail

# Required environment variables are supplied as GitHub Actions secrets.
: "${MACOS_CERTIFICATE_P12_BASE64:?Missing signing certificate}"
: "${MACOS_CERTIFICATE_PASSWORD:?Missing certificate password}"
: "${MACOS_SIGNING_IDENTITY:?Missing signing identity}"
: "${APPLE_API_KEY_P8_BASE64:?Missing App Store Connect API key}"
: "${APPLE_API_KEY_ID:?Missing App Store Connect key ID}"
: "${APPLE_API_ISSUER_ID:?Missing App Store Connect issuer ID}"

architecture="${1:?Usage: sign_and_notarize.sh x64|arm64}"
root_dir="$(cd "$(dirname "$0")/../.." && pwd)"
payload_dir="$root_dir/dist/pinyin_tones_release/macos/$architecture"
app_bundle="$(find "$payload_dir" -maxdepth 1 -type d -name '*.app' -print -quit)"

if [[ -z "$app_bundle" ]]; then
  echo "No macOS app bundle found in $payload_dir" >&2
  exit 1
fi

keychain="$RUNNER_TEMP/pinyin-tones-signing.keychain-db"
certificate="$RUNNER_TEMP/pinyin-tones.p12"
api_key="$RUNNER_TEMP/AuthKey_${APPLE_API_KEY_ID}.p8"
printf '%s' "$MACOS_CERTIFICATE_P12_BASE64" | base64 -D > "$certificate"
printf '%s' "$APPLE_API_KEY_P8_BASE64" | base64 -D > "$api_key"

security create-keychain -p '' "$keychain"
security set-keychain-settings -lut 21600 "$keychain"
security unlock-keychain -p '' "$keychain"
security import "$certificate" -k "$keychain" -P "$MACOS_CERTIFICATE_PASSWORD" -T /usr/bin/codesign
security list-keychain -d user -s "$keychain"
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k '' "$keychain"

codesign --force --deep --options runtime --timestamp \
  --entitlements "$root_dir/packaging/macos/entitlements.plist" \
  --sign "$MACOS_SIGNING_IDENTITY" "$app_bundle"
codesign --verify --deep --strict --verbose=2 "$app_bundle"

python3 "$root_dir/tools/build_release.py" \
  --platform macos --arch "$architecture" --formats portable,dmg --package-from-payload

dmg="$root_dir/dist/pinyin-tones-macos-$architecture.dmg"
codesign --force --timestamp --sign "$MACOS_SIGNING_IDENTITY" "$dmg"
xcrun notarytool submit "$dmg" --key "$api_key" --key-id "$APPLE_API_KEY_ID" \
  --issuer "$APPLE_API_ISSUER_ID" --wait
xcrun stapler staple "$dmg"
spctl --assess --type open --context context:primary-signature -vv "$dmg"
