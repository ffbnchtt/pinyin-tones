"""Development shim for running the src-layout package from the repo root."""

from __future__ import annotations

from pathlib import Path

SRC_PACKAGE_DIR = Path(__file__).resolve().parents[1] / "src" / "pinyin_app"

if SRC_PACKAGE_DIR.exists():
    src_package_path = str(SRC_PACKAGE_DIR)
    if src_package_path not in __path__:
        __path__.append(src_package_path)

from .version import __version__

__all__ = ["__version__"]
