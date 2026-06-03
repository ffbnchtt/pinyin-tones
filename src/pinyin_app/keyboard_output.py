"""Keyboard output helpers built on pynput."""

from __future__ import annotations

import platform
import time

from pynput.keyboard import Controller, Key

KEYBOARD = Controller()

# Small delay required between modifier down, V press and modifier up.
# Without it some applications receive a literal "v" instead of
# interpreting the sequence as a paste shortcut.
KEY_COMBO_DELAY = 0.05


def press_backspace(presses: int) -> None:
    """Press backspace one or more times."""
    for _ in range(max(1, presses)):
        KEYBOARD.press(Key.backspace)
        KEYBOARD.release(Key.backspace)


def paste_shortcut() -> None:
    """Emit the platform-specific paste shortcut."""
    modifier = Key.cmd if platform.system() == "Darwin" else Key.ctrl
    KEYBOARD.press(modifier)
    time.sleep(KEY_COMBO_DELAY)
    try:
        KEYBOARD.press("v")
        KEYBOARD.release("v")
        time.sleep(KEY_COMBO_DELAY)
    finally:
        KEYBOARD.release(modifier)


def type_text(text: str) -> None:
    """Type text into the focused application."""
    if not text:
        return
    KEYBOARD.type(text)
