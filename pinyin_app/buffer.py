"""Buffer and token processing for live pinyin conversion."""

from __future__ import annotations

import threading
import logging

try:
    import pyautogui
except Exception:  # pragma: no cover - optional dep
    pyautogui = None

from pinyin_app.pinyin_converter import convert_pinyin_token
from pinyin_app.clipboard import paste_text

logger = logging.getLogger('pinyin_app')

BUFFER: list[str] = []
BUFFER_LOCK = threading.Lock()


def reset_buffer() -> None:
    """Clear the typing buffer."""
    with BUFFER_LOCK:
        BUFFER.clear()


def delete_last_token() -> None:
    """Delete the characters in the current buffer from the focused app."""
    with BUFFER_LOCK:
        presses = max(1, len(BUFFER))
    if pyautogui is not None:
        pyautogui.press('backspace', presses=presses, interval=0)


def process_buffer() -> None:
    """Convert the buffered token and replace it in the active app."""
    with BUFFER_LOCK:
        if not BUFFER:
            return
        current = ''.join(BUFFER)
    converted = convert_pinyin_token(current)
    if converted == current:
        logger.info(f"No convertible token found for buffer: {current}")
        return
    logger.info(f"Converting token '{current}' -> '{converted}'")
    try:
        # synthetic input suppression is handled by the caller
        delete_last_token()
        paste_text(converted)
    finally:
        reset_buffer()


def handle_alpha_char(char: str) -> None:
    """Append a letter to buffer and trigger conversion if a tone digit follows."""
    with BUFFER_LOCK:
        BUFFER.append(char)
        current = ''.join(BUFFER)
    
    if len(current) >= 2 and current[-1].isdigit() and current[-1] in '12345':
        process_buffer()


def handle_digit_char(char: str) -> None:
    """Append a digit to the buffer and process conversion if valid."""
    with BUFFER_LOCK:
        if BUFFER and BUFFER[-1].isalpha():
            BUFFER.append(char)
            current = ''.join(BUFFER)
        else:
            
            BUFFER.clear()
            return
    
    process_buffer()
