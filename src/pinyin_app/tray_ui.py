"""Small helper to build a tray icon image for the app."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ASSET_DIR = Path(__file__).resolve().parent / "assets" / "tray"
ICON_BASENAME = "tray_quicksand_o_caron"
ICON_SIZES = (16, 20, 24, 32, 64)


def _asset_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "pinyin_app" / "assets" / "tray"
    return ASSET_DIR


def _pick_size(size: int) -> int:
    return min(ICON_SIZES, key=lambda candidate: abs(candidate - size))


def _load_base_icon(size: int) -> Image.Image | None:
    root = _asset_root()
    if not root.exists():
        return None
    chosen = _pick_size(size)
    path = root / f"{ICON_BASENAME}_{chosen}px.png"
    if not path.exists():
        return None
    image = Image.open(path).convert("RGBA")
    if image.size != (size, size):
        image = image.resize((size, size), Image.LANCZOS)
    return image


def _draw_fallback_base(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    size = image.size[0]
    center = size // 2
    radius = int(size * 0.5)
    base_color = (0, 0, 0, 255)
    draw.ellipse(
        (center - radius, center - radius, center + radius, center + radius),
        fill=base_color,
    )


def _draw_status_badge(image: Image.Image, active: bool) -> None:
    """Large visible Windows-style corner badge."""
    draw = ImageDraw.Draw(image)
    size = image.size[0]
    radius = max(1, int(size * 0.20))
    border = max(1, int(size * 0.05))
    margin = max(1, int(size * 0.01))
    cx = size - radius - border - margin
    cy = size - radius - border - margin
    color = (35, 210, 75, 255) if active else (220, 50, 50, 255)
    draw.ellipse(
        (
            cx - radius - border,
            cy - radius - border,
            cx + radius + border,
            cy + radius + border,
        ),
        fill=(0, 0, 0, 255),
    )
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=color,
    )


# =========================================================
# MAIN ICON
# =========================================================


def create_tray_image(
    active: bool = False,
    size: int = 64,
    show_status: bool = True,
    with_background: bool = False,
) -> Image.Image:
    """Create transparent tray icon."""
    base_icon = _load_base_icon(size)
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if with_background or base_icon is None:
        _draw_fallback_base(image)
    if base_icon is not None:
        image.alpha_composite(base_icon)
    if show_status:
        _draw_status_badge(image, active)
    return image
