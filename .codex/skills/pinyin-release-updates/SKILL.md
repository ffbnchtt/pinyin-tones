---
name: pinyin-release-updates
description: Handle packaging, executable builds, release payloads, version helpers, GitHub release update checks, update downloads, update dialogs, and release documentation. Use when editing tools/build_release.py, tools/build_*.sh, tools/build_windows.bat, src/pinyin_tones/update_check.py, src/pinyin_tones/update_dialog.py, src/pinyin_tones/version.py, pyproject.toml, or release docs/tests.
---

# Pinyin Release Updates

## Workflow

1. Read `docs/BUILD.md`, `docs/DOWNLOAD.md`, and the relevant tests before changing release behavior.
2. Keep asset names stable unless the user explicitly asks for a release contract change: `pinyin-tones-windows.zip`, `pinyin-tones-macos.zip`, `pinyin-tones-linux.zip`.
3. Keep update checks defensive: short timeouts, clear error states, no UI blocking, and no assumption that a compatible asset exists.
4. Avoid changing PyInstaller flags casually; platform differences are covered by tests.
5. Update docs when release commands, asset names, permissions, or install/update expectations change.
6. Run `python tools/run_tests.py` when possible; for narrow release work, verify `tests/test_build_release.py` and `tests/test_update_check.py`.

## Scope

- Build and packaging scripts in `tools/`.
- Version comparison in `src/pinyin_tones/version.py`.
- Update discovery/download in `src/pinyin_tones/update_check.py`.
- User-facing update prompt in `src/pinyin_tones/update_dialog.py` and `pinyin_live.PinyinApp`.
- Build/download docs under `docs/` and release notes expectations in `README.md`.

## Reference

Read `references/release-update-map.md` for release contracts, platform behavior, and validation targets.
