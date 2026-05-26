#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/build_release.py" --platform macos
echo "Build macOS completo en dist/pinyin_app_release/macos"
