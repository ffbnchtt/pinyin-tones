# Release And Update Map

## Release Contract

- Stable asset names:
  - `pinyin-tones-windows.zip`
  - `pinyin-tones-macos.zip`
  - `pinyin-tones-linux.zip`
- Build entrypoint: `python tools/build_release.py --platform windows|macos|linux`.
- Release payload should include the executable or bundle plus `LICENSE`, `USER_GUIDE.md`, and icon assets where applicable.

## Update Check Contract

- Default repo: `ffbnchtt/pinyin-tones`.
- API endpoint: latest GitHub release.
- Compatible asset is selected by current platform slug.
- Update status values include `idle`, `checking`, `available`, `up_to_date`, `no_release`, and `error`.
- Network failures should become `UpdateState(status="error", last_error=...)`, not uncaught UI-blocking failures.
- Downloads are stored under `downloads/` relative to the app root.

## Versioning

- Public version is in `src/pinyin_app/version.py` and `pyproject.toml`.
- Tags may include a leading `v`; comparisons should normalize before SemVer tuple comparison.

## Test Targets

- `tests/test_build_release.py`: platform normalization, PyInstaller flags, icon asset generation, release payload contents.
- `tests/test_update_check.py`: asset selection, GitHub JSON parsing, intervals, existing downloads, downloads, and error states.
- `tests/test_live_flow.py`: update-controller menu labels and dialog decisions in `PinyinApp`.
