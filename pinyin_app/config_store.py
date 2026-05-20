"""Configuration storage helpers for the app."""

from __future__ import annotations

import json
from typing import Any, Dict


def load_config(config_path: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Load the config file and merge it with defaults."""
    try:
        with open(config_path, 'r', encoding='utf-8') as handle:
            cfg = json.load(handle)
        return {**defaults, **cfg}
    except Exception:
        return dict(defaults)


def save_config(config_path: str, cfg: Dict[str, Any]) -> None:
    """Persist the config to disk."""
    try:
        with open(config_path, 'w', encoding='utf-8') as handle:
            json.dump(cfg, handle, ensure_ascii=False, indent=2)
    except Exception as exc:
        print('Error saving config:', exc)
