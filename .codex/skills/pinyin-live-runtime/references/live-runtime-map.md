# Live Runtime Map

## Runtime Flow

1. `pinyin_live.PinyinApp` loads config, builds keyboard listeners, starts update checks, and runs the tray icon.
2. `pinyin_live.on_type` ignores input while suppressed, while the settings/update dialog is open, or while conversion is inactive.
3. `buffer.handle_alpha_char` and `buffer.handle_digit_char` maintain the token buffer.
4. `buffer.process_buffer` converts the token, suppresses synthetic input, deletes the source token, pastes the converted text, then resets the buffer.
5. `clipboard.paste_text` uses clipboard copy/paste when possible and falls back to direct typing.

## Shared State

- `pinyin_live.ACTIVE`, `ACTIVE_LOCK`, `PRESSED_KEYS`, `CONFIG_DIALOG_OPEN`, `SETTINGS_REQUESTED`, `UPDATE_DIALOG_REQUESTED`, `STOP_REQUESTED`.
- `buffer.BUFFER`, `BUFFER_LOCK`, `SUPPRESS_UNTIL`, `SUPPRESS_LOCK`.
- `clipboard.CLIPBOARD_BASELINE`, `CLIPBOARD_RESTORE_TIMER`, `CLIPBOARD_RESTORE_LOCK`.

## Platform Risks

- Windows autostart commands must stay compact enough for Run entry limits.
- macOS requires accessibility/input permissions for global listening and injection.
- Linux works best on X11; Wayland may block global capture or injection.
- Use `cmd`/`ctrl` paste differences through `keyboard_output.paste_shortcut`.

## Test Targets

- `tests/test_live_flow.py` covers replacement, buffer reset, suppression, hotkey capture, config dialog gating, autostart helpers, and update menu state.
- Prefer mocks for `pyperclip`, keyboard primitives, platform detection, timers, message boxes, and filesystem effects.
- Reset global state in `setUp` or scoped contexts before asserting runtime behavior.
