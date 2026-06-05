---
name: pinyin-live-runtime
description: Work on the live desktop runtime for Pinyin Tones. Use when changing global keyboard listeners, token buffering, synthetic input suppression, clipboard paste/restore, hotkey capture, tray menu state, settings UI, config persistence, autostart behavior, or tests in tests/test_live_flow.py.
---

# Pinyin Live Runtime

## Workflow

1. Read `docs/ARCHITECTURE.md`, then inspect the specific runtime modules involved.
2. Keep pure conversion in `pinyin_converter.py`; runtime code should call it through `buffer.process_buffer`.
3. Treat global listener state as shared mutable state. Reset or isolate globals in tests when adding scenarios.
4. Preserve the short synthetic-input suppression window around replacement so generated backspace/paste events do not re-enter the listener.
5. Prefer test doubles over live keyboard, clipboard, registry, launch agent, or tray interactions in automated tests.
6. Run `python tools/run_tests.py` when possible; for narrow runtime changes, verify `tests/test_live_flow.py`.

## Module Boundaries

- `pinyin_live.py`: application controller, listener lifecycle, tray integration, update prompts, compatibility re-exports.
- `buffer.py`: small token buffer, backspace deletion, conversion trigger, suppression timing.
- `clipboard.py`: clipboard synchronization, fallback to direct typing, delayed restore.
- `keyboard_output.py`: platform keyboard primitives.
- `hotkeys.py`: hotkey parsing and normalization.
- `settings_ui.py` and `tray_ui.py`: Tk settings dialog and tray icon/menu presentation.
- `config_store.py`: JSON config load/save and defaults interaction.
- `autostart.py`: Windows/macOS/Linux autostart commands and files.

## Reference

Read `references/live-runtime-map.md` for runtime invariants, platform risks, and test targets.
