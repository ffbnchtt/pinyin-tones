"""Buffer and token processing for live pinyin conversion."""

from __future__ import annotations

import threading
import logging
import time

from pinyin_app.pinyin_converter import convert_pinyin_token
from pinyin_app.clipboard import paste_text
from pinyin_app.keyboard_output import press_backspace

logger = logging.getLogger("pinyin_app")

BUFFER: list[str] = []
BUFFER_LOCK = threading.Lock()
SUPPRESS_LOCK = threading.Lock()
SUPPRESS_UNTIL = 0.0
SUPPRESS_DURATION = 0.25
REPLACEMENT_DELAY = 0


def suppress_input_for(duration: float) -> None:
    """Suppress synthetic key handling briefly after programmatic input."""
    if duration <= 0:
        return
    deadline = time.monotonic() + duration
    with SUPPRESS_LOCK:
        global SUPPRESS_UNTIL
        if deadline > SUPPRESS_UNTIL:
            SUPPRESS_UNTIL = deadline


def is_input_suppressed() -> bool:
    """Return True while synthetic input suppression window is active."""
    with SUPPRESS_LOCK:
        return time.monotonic() < SUPPRESS_UNTIL


def reset_buffer() -> None:
    """Clear the typing buffer."""
    logger.info("BUFFER RESET FROM %r", BUFFER.copy())
    with BUFFER_LOCK:
        BUFFER.clear()


def delete_last_token() -> None:
    """Delete the characters in the current buffer from the focused app."""
    with BUFFER_LOCK:
        presses = max(1, len(BUFFER))
    logger.info("Deleting token: buffer=%r presses=%d", "".join(BUFFER), presses)
    press_backspace(presses)


def process_buffer() -> None:
    """Convert the buffered token and replace it in the active app."""
    with BUFFER_LOCK:
        if not BUFFER:
            return
        current = "".join(BUFFER)

    logger.info("Buffer snapshot before conversion: %r", BUFFER.copy())
    converted = convert_pinyin_token(current)
    if converted == current:
        logger.info(f"No convertible token found for buffer: {current}")
        return
    logger.info(f"Converting token '{current}' -> '{converted}'")
    try:
        if REPLACEMENT_DELAY > 0:
            time.sleep(REPLACEMENT_DELAY)
        suppress_input_for(SUPPRESS_DURATION)
        delete_last_token()
        paste_text(converted)
    finally:
        reset_buffer()


def handle_alpha_char(char: str) -> None:
    """Append a letter to buffer and trigger conversion if a tone digit follows."""

    logger.info("BUFFER APPEND ALPHA: %r -> %r", char, BUFFER)

    with BUFFER_LOCK:
        BUFFER.append(char)
        current = "".join(BUFFER)

    if len(current) >= 2 and current[-1].isdigit() and current[-1] in "12345":
        process_buffer()


def handle_digit_char(char: str) -> None:
    """Append a digit to the buffer and process conversion if valid."""
    logger.info("BUFFER APPEND DIGIT: %r -> %r", char, BUFFER)
    with BUFFER_LOCK:
        if BUFFER and BUFFER[-1].isalpha():
            BUFFER.append(char)
        else:

            BUFFER.clear()
            return

    process_buffer()
