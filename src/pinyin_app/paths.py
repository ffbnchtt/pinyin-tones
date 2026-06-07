"""Runtime path helpers for source and packaged executions."""

from __future__ import annotations

import os
import platform
import sys
import tempfile
from pathlib import Path


APP_DATA_DIR_NAME = "Pinyin Tones"


def get_app_root() -> str:
    """Return the project root in source mode or executable folder when frozen."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(Path(__file__).resolve().parents[2])


def get_user_data_dir(app_name: str = APP_DATA_DIR_NAME) -> str:
    """Return a per-user writable directory for app state."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, app_name)


def is_writable_dir(path: str) -> bool:
    """Return True when a directory exists or can be created and written to."""
    try:
        os.makedirs(path, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".write-test-", dir=path, delete=True):
            pass
        return True
    except OSError:
        return False


def get_state_dir(app_root: str | None = None) -> str:
    """Prefer portable app-root state, falling back to per-user state."""
    root = app_root or get_app_root()
    if is_writable_dir(root):
        return root
    state_dir = get_user_data_dir()
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

