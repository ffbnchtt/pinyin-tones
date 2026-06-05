# QA And Docs Map

## Documentation

- `README.md`: quick start, source install, basic usage, config, tests, release asset naming.
- `docs/USER_GUIDE.md`: end-user behavior, troubleshooting, uninstall flow, release package contents.
- `docs/BUILD.md`: source execution, PyInstaller commands, platform permissions.
- `docs/DOWNLOAD.md`: release download/install expectations.
- `CONTRIBUTING.md`: issue/PR process and test expectations.
- `SECURITY.md`: vulnerability reporting.

## Tests

- `tests/test_converter.py`: pure token conversion behavior.
- `tests/test_live_flow.py`: runtime flow, hotkeys, clipboard, config dialog gating, autostart, update-controller UI decisions.
- `tests/test_update_check.py`: semver helpers, GitHub release parsing, asset selection, download helpers.
- `tests/test_build_release.py`: PyInstaller command assembly, icon generation, release payload contents.

## Review Checklist

- Match changed behavior to a test file.
- Keep docs and code names consistent for config keys, shortcuts, asset names, and platform warnings.
- Do not claim live OS behavior was verified unless the app was actually run on that platform.
- Prefer small focused tests using mocks for filesystem, network, clipboard, keyboard, and tray operations.
