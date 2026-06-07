"""Configuration storage helpers for the app."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any, Dict


logger = logging.getLogger("pinyin_app")


def load_config(config_path: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Load the config file and merge it with defaults."""
    try:
        with open(config_path, 'r', encoding='utf-8') as handle:
            cfg = json.load(handle)
        return {**defaults, **cfg}
    except FileNotFoundError:
        return dict(defaults)
    except Exception:
        logger.exception("Failed to load config from %s; using defaults", config_path)
        return dict(defaults)


def save_config(config_path: str, cfg: Dict[str, Any]) -> None:
    """Persist the config to disk."""
    temp_path = None
    try:
        directory = os.path.dirname(os.path.abspath(config_path))
        os.makedirs(directory, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            'w',
            encoding='utf-8',
            dir=directory,
            delete=False,
            prefix='.config-',
            suffix='.tmp',
        ) as handle:
            json.dump(cfg, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            temp_path = handle.name
        os.replace(temp_path, config_path)
    except Exception as exc:
        logger.exception("Failed to save config to %s", config_path)
        print('Error saving config:', exc)
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass
