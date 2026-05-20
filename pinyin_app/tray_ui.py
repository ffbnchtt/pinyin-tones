"""Small helper to build a tray icon image for the app."""

from __future__ import annotations

from PIL import Image, ImageDraw

def create_tray_image(active: bool = False, size: int = 64) -> Image.Image:
    """Return a PIL image representing the tray icon state."""
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    center = size // 2
    radius = int(size * 0.42)
    base_color = (18, 22, 32, 255)
    accent = (0, 183, 102, 255) if active else (160, 160, 160, 255)
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=base_color, outline=accent, width=max(2, size // 32))
    return image
