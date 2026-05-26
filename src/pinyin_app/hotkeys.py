"""Hotkey parsing and normalization helpers."""

from __future__ import annotations

from typing import Optional, Set, Tuple

HOTKEY_MODIFIER_ORDER = ('ctrl', 'alt', 'shift', 'cmd')
ALLOWED_TRIGGER_KEYS = set('abcdefghijklmnopqrstuvwxyz')
TK_MODIFIER_KEYS = {
    'control_l': 'ctrl',
    'control_r': 'ctrl',
    'control': 'ctrl',
    'shift_l': 'shift',
    'shift_r': 'shift',
    'shift': 'shift',
    'alt_l': 'alt',
    'alt_r': 'alt',
    'alt': 'alt',
    'option': 'alt',
    'super_l': 'cmd',
    'super_r': 'cmd',
    'super': 'cmd',
    'meta_l': 'cmd',
    'meta_r': 'cmd',
    'meta': 'cmd',
    'command': 'cmd',
    'cmd': 'cmd',
}


def parse_hotkey(hotkey: str) -> Tuple[Set[str], Optional[str]]:
    """Parse a hotkey string into modifiers and trigger."""
    parts = [part.strip() for part in hotkey.split('+') if part.strip()]
    modifiers: Set[str] = set()
    trigger: Optional[str] = None
    for part in parts:
        token = part.lower().strip('<>')
        if token in {'ctrl', 'control'}:
            modifiers.add('ctrl')
        elif token == 'shift':
            modifiers.add('shift')
        elif token in {'alt', 'option'}:
            modifiers.add('alt')
        elif token in {'cmd', 'win', 'super'}:
            modifiers.add('cmd')
        else:
            trigger = token
    return modifiers, trigger


def format_hotkey(modifiers: Set[str], trigger: Optional[str]) -> str:
    """Format a hotkey back into the canonical config string."""
    parts = [f'<{modifier}>' for modifier in HOTKEY_MODIFIER_ORDER if modifier in modifiers]
    if trigger:
        parts.append(trigger.lower())
    return '+'.join(parts)


def format_hotkey_display(modifiers: Set[str], trigger: Optional[str]) -> str:
    """Format a hotkey in a user-friendly display string."""
    parts = []
    for modifier in HOTKEY_MODIFIER_ORDER:
        if modifier in modifiers:
            parts.append(modifier.capitalize())
    if trigger:
        parts.append(trigger.upper() if len(trigger) == 1 else trigger.capitalize())
    return '+'.join(parts)


def normalize_capture_key(event) -> Optional[str]:
    """Normalize a Tk key event to a modifier name."""
    keysym = getattr(event, 'keysym', '')
    if not keysym:
        return None
    return TK_MODIFIER_KEYS.get(keysym.lower())


def normalize_trigger_key(event) -> Optional[str]:
    """Normalize a Tk key event into a valid trigger key."""
    keysym = getattr(event, 'keysym', '')
    if not keysym:
        return None
    lowered = keysym.lower()
    if lowered in TK_MODIFIER_KEYS:
        return None
    if lowered in {'escape', 'return'}:
        return None
    return lowered if lowered in ALLOWED_TRIGGER_KEYS else None


def normalize_pynput_trigger_key(key) -> Optional[str]:
    """Normalize a pynput key into a valid trigger key."""
    char = getattr(key, 'char', None)
    if char:
        lowered = char.lower()
        return lowered if lowered in ALLOWED_TRIGGER_KEYS else None
    name = getattr(key, 'name', None)
    if not name:
        vk = getattr(key, 'vk', None)
        if isinstance(vk, int) and 32 <= vk <= 126:
            lowered = chr(vk).lower()
            return lowered if lowered in ALLOWED_TRIGGER_KEYS else None
        return None
    lowered = name.lower()
    if lowered in {
        'ctrl', 'ctrl_l', 'ctrl_r',
        'shift', 'shift_l', 'shift_r',
        'alt', 'alt_l', 'alt_r',
        'cmd', 'cmd_l', 'cmd_r',
        'escape', 'return', 'enter',
    }:
        return None
    return lowered if lowered in ALLOWED_TRIGGER_KEYS else None
