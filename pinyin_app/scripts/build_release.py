#!/usr/bin/env python3
"""Build helper for packaging the Pinyin app across platforms.

This script centralizes the common build steps so the platform wrappers only
pass the target operating system.
"""

from __future__ import annotations

import argparse
import os
import platform
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR
SRC_PATH = APP_DIR / 'src' / 'pinyin_live.py'
DIST_DIR = APP_DIR / 'dist'
BUILD_DIR = APP_DIR / 'build'
RELEASE_DIR = DIST_DIR / 'pinyin_app_release'
ASSET_DIR = BUILD_DIR / 'branding'
APP_NAME = 'pinyin_app'
APP_TITLE = 'Pinyin Tones'
APP_ID = 'pinyin-tones'
WINDOWS_RUN_KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
WINDOWS_RUN_VALUE_NAME = 'Pinyin Tones'
MAC_LAUNCH_AGENT_LABEL = 'com.federico.pinyin-tones'
LINUX_AUTOSTART_FILENAME = 'pinyin-tones.desktop'
ICON_BASENAME = 'pinyin_app'
LICENSE_SOURCE = ROOT_DIR.parent / 'LICENSE'
USER_GUIDE_SOURCE = APP_DIR / 'docs' / 'USER_GUIDE.md'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build the Pinyin app for a target platform.')
    parser.add_argument(
        '--platform',
        choices=('windows', 'macos', 'linux'),
        default=platform.system().lower(),
        help='Target platform used to choose PyInstaller flags and icon format.',
    )
    return parser.parse_args()


def ensure_user_guide() -> Path:
    if not USER_GUIDE_SOURCE.exists():
        raise FileNotFoundError(f'Missing user guide: {USER_GUIDE_SOURCE}')
    return USER_GUIDE_SOURCE


def build_icon_image(size: int = 1024) -> Image.Image:
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    center = size // 2
    radius = int(size * 0.42)
    base_color = (18, 22, 32, 255)
    accent = (0, 183, 102, 255)
    accent_soft = (255, 205, 63, 255)
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=base_color, outline=accent, width=max(8, size // 64))
    try:
        font = ImageFont.load_default()
        draw.text((int(size * 0.42), int(size * 0.34)), 'P', font=font, fill=(255, 255, 255, 255))
    except Exception:
        pass
    draw.line((int(size * 0.33), int(size * 0.66), int(size * 0.67), int(size * 0.66)), fill=accent_soft, width=max(10, size // 72))
    draw.line((int(size * 0.38), int(size * 0.58), int(size * 0.50), int(size * 0.50)), fill=accent_soft, width=max(8, size // 80))
    draw.line((int(size * 0.50), int(size * 0.50), int(size * 0.62), int(size * 0.44)), fill=accent_soft, width=max(8, size // 80))
    return image


def ensure_icon_assets() -> dict[str, Path]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    image = build_icon_image()

    png_path = ASSET_DIR / f'{ICON_BASENAME}.png'
    ico_path = ASSET_DIR / f'{ICON_BASENAME}.ico'
    icns_path = ASSET_DIR / f'{ICON_BASENAME}.icns'

    image.save(png_path)
    image.save(ico_path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    try:
        image.save(icns_path)
    except Exception:
        if icns_path.exists():
            icns_path.unlink()

    return {
        'png': png_path,
        'ico': ico_path,
        'icns': icns_path if icns_path.exists() else png_path,
    }


def get_launcher_command() -> list[str]:
    if getattr(sys, 'frozen', False):
        return [os.path.abspath(sys.executable)]
    return [os.path.abspath(sys.executable), str(SRC_PATH)]


def build_pyinstaller_command(platform_name: str, icon_assets: dict[str, Path]) -> list[str]:
    command = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--onefile',
        '--name',
        APP_NAME,
        '--clean',
        str(SRC_PATH),
    ]
    if platform_name == 'windows':
        command.insert(4, '--noconsole')
        command.extend(['--icon', str(icon_assets['ico'])])
    elif platform_name == 'macos':
        command.insert(4, '--windowed')
        command.extend(['--icon', str(icon_assets['icns'])])
    else:
        command.insert(4, '--noconsole')
    return command


def find_artifact_path(platform_name: str) -> Path:
    candidates: Iterable[Path]
    if platform_name == 'macos':
        candidates = (DIST_DIR / f'{APP_NAME}.app', DIST_DIR / APP_NAME)
    elif platform_name == 'windows':
        candidates = (DIST_DIR / f'{APP_NAME}.exe', DIST_DIR / APP_NAME)
    else:
        candidates = (DIST_DIR / APP_NAME, DIST_DIR / f'{APP_NAME}.exe')
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f'Build artifact not found in {DIST_DIR}')


def copy_release_payload(platform_name: str, artifact_path: Path, icon_assets: dict[str, Path]) -> Path:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    platform_release_dir = RELEASE_DIR / platform_name
    if platform_release_dir.exists():
        shutil.rmtree(platform_release_dir)
    platform_release_dir.mkdir(parents=True, exist_ok=True)

    if artifact_path.is_dir():
        shutil.copytree(artifact_path, platform_release_dir / artifact_path.name)
    else:
        shutil.copy2(artifact_path, platform_release_dir / artifact_path.name)

    if LICENSE_SOURCE.exists():
        shutil.copy2(LICENSE_SOURCE, platform_release_dir / 'LICENSE')
    if ensure_user_guide().exists():
        shutil.copy2(USER_GUIDE_SOURCE, platform_release_dir / 'USER_GUIDE.md')

    shutil.copy2(icon_assets['png'], platform_release_dir / icon_assets['png'].name)
    if icon_assets['ico'].exists():
        shutil.copy2(icon_assets['ico'], platform_release_dir / icon_assets['ico'].name)
    if icon_assets['icns'].exists() and icon_assets['icns'] != icon_assets['png']:
        shutil.copy2(icon_assets['icns'], platform_release_dir / icon_assets['icns'].name)

    return platform_release_dir


def run_pyinstaller(command: list[str]) -> None:
    subprocess.run(command, cwd=str(APP_DIR), check=True)


def build(platform_name: str) -> Path:
    icon_assets = ensure_icon_assets()
    command = build_pyinstaller_command(platform_name, icon_assets)
    run_pyinstaller(command)
    artifact_path = find_artifact_path(platform_name)
    release_dir = copy_release_payload(platform_name, artifact_path, icon_assets)
    return release_dir


def main() -> int:
    args = parse_args()
    release_dir = build(args.platform)
    print(f'Build complete: {release_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
