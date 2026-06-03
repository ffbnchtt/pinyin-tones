"""Configuration storage helpers for the app."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict


logger = logging.getLogger("pinyin_app")


def load_config(config_path: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Load the config file and merge it with defaults."""
    try:
        with open(config_path, 'r', encoding='utf-8') as handle:
            cfg = json.load(handle)
        return {**defaults, **cfg}
    except Exception:
        logger.exception("Failed to load config from %s; using defaults", config_path)
        return dict(defaults)


def save_config(config_path: str, cfg: Dict[str, Any]) -> None:
    """Persist the config to disk."""
    try:
        with open(config_path, 'w', encoding='utf-8') as handle:
            json.dump(cfg, handle, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.exception("Failed to save config to %s", config_path)
        print('Error saving config:', exc)
