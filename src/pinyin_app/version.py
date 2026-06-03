"""Application version helpers."""

from __future__ import annotations

import re
from typing import Optional, Tuple

__version__ = "0.1.0"

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def parse_version(value: str | None) -> Optional[Tuple[int, int, int]]:
    """Parse a simple semantic version like 0.1.0 or v0.1.0."""
    if not value:
        return None
    match = _VERSION_RE.match(value.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def normalize_version(value: str | None) -> str:
    """Normalize a version for display and comparisons."""
    parsed = parse_version(value)
    if parsed is None:
        return (value or "").strip()
    major, minor, patch = parsed
    return f"{major}.{minor}.{patch}"


def is_newer_version(candidate: str | None, current: str | None) -> bool:
    """Return True when candidate is newer than current."""
    candidate_parsed = parse_version(candidate)
    current_parsed = parse_version(current)
    if candidate_parsed is None or current_parsed is None:
        return False
    return candidate_parsed > current_parsed
