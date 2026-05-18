# Architecture

## Runtime flow
- `pinyin_app/src/pinyin_live.py` starts the global keyboard listeners and the tray icon.
- `pinyin_app/src/pinyin_converter.py` converts tokens like `ni3` or `hao3` to tone-marked output.
- The live listener keeps a small buffer, detects the configured hotkey, and replaces the last token using clipboard-based paste for Unicode reliability.

## Components
- Tray icon: shows active/inactive state and opens the settings dialog using the shared app badge.
- Settings dialog: captures the hotkey directly from pressed keys and stores it in `pinyin_app/config.json`.
- The dialog keeps the CTA buttons aligned to the right and uses a readonly preview so the user records shortcuts instead of typing them manually.
- Logging: writes to `pinyin_app/pinyin_app.log` for debugging.
- Quitting from the tray signals the main loop to exit cleanly.

## Design goals
- Minimal dependencies.
- Cross-platform behavior on Windows, macOS, and Linux where `pynput` supports it.
- Fast live replacement with low interruption to typing.
