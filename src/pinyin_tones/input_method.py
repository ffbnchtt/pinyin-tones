"""Detect input methods that conflict with numeric pinyin conversion."""

from __future__ import annotations

import ctypes
import platform
from typing import Optional


# Primary language identifiers used by Windows for candidate-based CJK input.
# The primary language occupies the low 10 bits of a LANGID.
SPECIAL_INPUT_PRIMARY_LANGUAGE_IDS = frozenset({
    0x04,  # Chinese
    0x11,  # Japanese
    0x12,  # Korean
})
PRIMARY_LANGUAGE_MASK = 0x03FF


def is_detection_supported() -> bool:
    """Return whether active input-language detection is available."""
    return platform.system() == "Windows"


def is_special_input_language(language_id: Optional[int]) -> bool:
    """Return whether a Windows LANGID belongs to a protected CJK language."""
    if language_id is None:
        return False
    return (language_id & PRIMARY_LANGUAGE_MASK) in SPECIAL_INPUT_PRIMARY_LANGUAGE_IDS


def get_active_input_language_id() -> Optional[int]:
    """Return the LANGID used by the foreground window on Windows.

    Detection fails open so unsupported platforms or transient Win32 failures do
    not unexpectedly disable conversion.
    """
    if not is_detection_supported():
        return None

    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetForegroundWindow.restype = ctypes.c_void_p
        user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        user32.GetWindowThreadProcessId.restype = ctypes.c_uint32
        user32.GetKeyboardLayout.argtypes = [ctypes.c_uint32]
        user32.GetKeyboardLayout.restype = ctypes.c_void_p

        foreground_window = user32.GetForegroundWindow()
        if not foreground_window:
            return None
        thread_id = user32.GetWindowThreadProcessId(foreground_window, None)
        if not thread_id:
            return None
        keyboard_layout = user32.GetKeyboardLayout(thread_id)
        if not keyboard_layout:
            return None
        return int(keyboard_layout) & 0xFFFF
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def is_special_input_method_active() -> Optional[bool]:
    """Return the protected-input state, or ``None`` if it cannot be observed."""
    language_id = get_active_input_language_id()
    if language_id is None:
        return None
    return is_special_input_language(language_id)
