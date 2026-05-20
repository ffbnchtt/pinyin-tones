"""Clipboard helpers for copying/pasting with synchronization."""

from __future__ import annotations

import threading
import time
import logging

try:
    import pyperclip
except Exception:  # pragma: no cover - optional dep
    pyperclip = None

try:
    import pyautogui
except Exception:  # pragma: no cover - optional dep
    pyautogui = None

logger = logging.getLogger('pinyin_app')

CLIPBOARD_RESTORE_DELAY = 0.15
CLIPBOARD_SYNC_TIMEOUT = 0.01
CLIPBOARD_SYNC_POLL = 0.001
CLIPBOARD_BASELINE = None
CLIPBOARD_RESTORE_TIMER = None
CLIPBOARD_RESTORE_LOCK = threading.Lock()


def sync_clipboard_text(expected_text: str) -> None:
    """Wait briefly until the clipboard contains expected_text.

    Returns early if `pyperclip` is not available.
    """
    if pyperclip is None:
        return
    deadline = time.monotonic() + CLIPBOARD_SYNC_TIMEOUT
    while time.monotonic() < deadline:
        try:
            if pyperclip.paste() == expected_text:
                return
        except Exception:
            return
        time.sleep(CLIPBOARD_SYNC_POLL)


def restore_clipboard_baseline() -> None:
    """Restore clipboard to previously recorded baseline value."""
    global CLIPBOARD_BASELINE, CLIPBOARD_RESTORE_TIMER
    if pyperclip is None:
        return
    with CLIPBOARD_RESTORE_LOCK:
        baseline = CLIPBOARD_BASELINE
        CLIPBOARD_BASELINE = None
        CLIPBOARD_RESTORE_TIMER = None
    if baseline is None:
        return
    try:
        pyperclip.copy(baseline)
    except Exception:
        logger.exception('Failed to restore clipboard baseline')


def schedule_clipboard_restore() -> None:
    """Schedule a delayed restore of the clipboard baseline."""
    global CLIPBOARD_RESTORE_TIMER
    if pyperclip is None:
        return
    with CLIPBOARD_RESTORE_LOCK:
        if CLIPBOARD_RESTORE_TIMER is not None:
            try:
                CLIPBOARD_RESTORE_TIMER.cancel()
            except Exception:
                pass
            CLIPBOARD_RESTORE_TIMER = None
        if CLIPBOARD_BASELINE is None:
            return
        timer = threading.Timer(CLIPBOARD_RESTORE_DELAY, restore_clipboard_baseline)
        timer.daemon = True
        CLIPBOARD_RESTORE_TIMER = timer
        timer.start()


def paste_text(text: str) -> None:
    """Paste text into focused application.

    Uses the clipboard if `pyperclip` is available, otherwise falls back to
    `pyautogui.write`.
    """
    global CLIPBOARD_BASELINE
    if pyperclip is None or pyautogui is None:
        logger.info('pyperclip/pyautogui not available; falling back to typing')
        if pyautogui is not None:
            pyautogui.write(text, interval=0.01)
        return
    try:
        previous_clipboard = pyperclip.paste()
    except Exception:
        previous_clipboard = None
    if CLIPBOARD_BASELINE is None and previous_clipboard is not None:
        CLIPBOARD_BASELINE = previous_clipboard
        
    try:
        pyperclip.copy(text)
        sync_clipboard_text(text)
        pyautogui.hotkey('ctrl', 'v')
    finally:
        schedule_clipboard_restore()
