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
import zipfile
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / 'src'
APP_DIR = SRC_DIR / 'pinyin_tones'
SRC_PATH = APP_DIR / 'pinyin_live.py'
DIST_DIR = ROOT_DIR / 'dist'
BUILD_DIR = ROOT_DIR / 'build'
RELEASE_DIR = DIST_DIR / 'pinyin_tones_release'
ASSET_DIR = BUILD_DIR / 'branding'
TRAY_ASSET_DIR = APP_DIR / 'assets' / 'tray'
APP_ICON_SOURCE = APP_DIR / 'assets' / 'app_icon.png'
APP_NAME = 'pinyin_tones'
ICON_BASENAME = 'pinyin_tones'
LICENSE_SOURCE = ROOT_DIR / 'LICENSE'
USER_GUIDE_SOURCE = ROOT_DIR / 'docs' / 'USER_GUIDE.md'
TK_RUNTIME_HOOK = BUILD_DIR / 'pyinstaller_tk_runtime.py'
PYINSTALLER_HOOK_DIR = BUILD_DIR / 'pyinstaller_hooks'
RELEASE_ASSET_NAMES = {
    'windows': 'pinyin-tones-windows.zip',
    'macos': 'pinyin-tones-macos.zip',
    'linux': 'pinyin-tones-linux.zip',
}


def normalize_platform_name(system_name: str) -> str:
    """Map Python platform names to the build helper's supported values."""
    normalized = system_name.strip().lower()
    aliases = {
        'windows': 'windows',
        'win32': 'windows',
        'darwin': 'macos',
        'mac': 'macos',
        'macos': 'macos',
        'linux': 'linux',
    }
    return aliases.get(normalized, normalized)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build the Pinyin app for a target platform.')
    parser.add_argument(
        '--platform',
        choices=('windows', 'macos', 'linux'),
        default=normalize_platform_name(platform.system()),
        help='Target platform used to choose PyInstaller flags and icon format.',
    )
    return parser.parse_args()


def ensure_user_guide() -> Path:
    if not USER_GUIDE_SOURCE.exists():
        raise FileNotFoundError(f'Missing user guide: {USER_GUIDE_SOURCE}')
    return USER_GUIDE_SOURCE


def build_icon_image(size: int = 1024) -> Image.Image:
    if APP_ICON_SOURCE.exists():
        image = Image.open(APP_ICON_SOURCE).convert('RGBA')
        if image.size != (size, size):
            image = image.resize((size, size), Image.LANCZOS)
        return image
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    center = size // 2
    radius = int(size * 0.42)
    base_color = (18, 22, 32, 255)
    accent = (0, 183, 102, 255)
    accent_soft = (255, 205, 63, 255)
    draw.ellipse(
        (center - radius, center - radius, center + radius, center + radius),
        fill=base_color,
        outline=accent,
        width=max(8, size // 64),
    )
    try:
        font = ImageFont.load_default()
        draw.text(
            (int(size * 0.42), int(size * 0.34)),
            'P',
            font=font,
            fill=(255, 255, 255, 255),
        )
    except Exception:
        pass
    draw.line(
        (int(size * 0.33), int(size * 0.66), int(size * 0.67), int(size * 0.66)),
        fill=accent_soft,
        width=max(10, size // 72),
    )
    draw.line(
        (int(size * 0.38), int(size * 0.58), int(size * 0.50), int(size * 0.50)),
        fill=accent_soft,
        width=max(8, size // 80),
    )
    draw.line(
        (int(size * 0.50), int(size * 0.50), int(size * 0.62), int(size * 0.44)),
        fill=accent_soft,
        width=max(8, size // 80),
    )
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


def build_pyinstaller_command(platform_name: str, icon_assets: dict[str, Path]) -> list[str]:
    command = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--onefile',
        '--name',
        APP_NAME,
        '--clean',
        '--paths',
        str(SRC_DIR),
        '--hidden-import',
        'pinyin_tones.pinyin_converter',
        str(SRC_PATH),
    ]
    if TRAY_ASSET_DIR.exists():
        data_sep = ';' if platform_name == 'windows' else ':'
        data_spec = f'{TRAY_ASSET_DIR}{data_sep}pinyin_tones/assets/tray'
        command.extend(['--add-data', data_spec])
    if platform_name == 'windows':
        command.insert(4, '--noconsole')
        command.extend(['--icon', str(icon_assets['ico'])])
        command.extend(build_windows_tk_options())
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


def remove_standalone_artifact(artifact_path: Path, release_dir: Path) -> None:
    """Remove the raw PyInstaller artifact after copying it into the release payload."""
    resolved_artifact = artifact_path.resolve()
    resolved_dist = DIST_DIR.resolve()
    resolved_release = release_dir.resolve()

    if resolved_artifact == resolved_release or resolved_release in resolved_artifact.parents:
        return
    if resolved_dist not in resolved_artifact.parents:
        return
    if not artifact_path.exists():
        return

    if artifact_path.is_dir():
        shutil.rmtree(artifact_path)
    else:
        artifact_path.unlink()


def create_release_archive(platform_name: str, release_dir: Path) -> Path:
    """Create the upload-ready GitHub release archive for a platform payload."""
    try:
        asset_name = RELEASE_ASSET_NAMES[platform_name]
    except KeyError as exc:
        raise ValueError(f'Unsupported release platform: {platform_name}') from exc

    archive_path = DIST_DIR / asset_name
    if archive_path.exists():
        archive_path.unlink()

    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(release_dir.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(release_dir))
    return archive_path


def get_tk_paths() -> tuple[Path, Path, Path, Path, Path]:
    """Return the local Python Tcl/Tk paths needed for Windows PyInstaller builds."""
    python_root = Path(sys.base_prefix)
    tcl_library = python_root / 'tcl' / 'tcl8.6'
    tk_library = python_root / 'tcl' / 'tk8.6'
    tkinter_binary = python_root / 'DLLs' / '_tkinter.pyd'
    tcl_binary = python_root / 'DLLs' / 'tcl86t.dll'
    tk_binary = python_root / 'DLLs' / 'tk86t.dll'
    return tcl_library, tk_library, tkinter_binary, tcl_binary, tk_binary


def ensure_windows_tk_runtime_hook() -> Path:
    """Write a PyInstaller runtime hook that points Tkinter to bundled Tcl/Tk data."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    TK_RUNTIME_HOOK.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "",
                "base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))",
                "tcl_dir = os.path.join(base_dir, '_tcl_data')",
                "tk_dir = os.path.join(base_dir, '_tk_data')",
                "if os.path.isdir(tcl_dir):",
                "    os.environ['TCL_LIBRARY'] = tcl_dir",
                "if os.path.isdir(tk_dir):",
                "    os.environ['TK_LIBRARY'] = tk_dir",
                "",
            ]
        ),
        encoding='utf-8',
    )
    return TK_RUNTIME_HOOK


def ensure_windows_tk_hook_dir() -> Path:
    """Write hooks that keep PyInstaller from excluding tkinter on this Windows install."""
    pre_find_dir = PYINSTALLER_HOOK_DIR / 'pre_find_module_path'
    pre_find_dir.mkdir(parents=True, exist_ok=True)
    (pre_find_dir / 'hook-tkinter.py').write_text(
        "\n".join(
            [
                "def pre_find_module_path(hook_api):",
                "    return None",
                "",
            ]
        ),
        encoding='utf-8',
    )
    return PYINSTALLER_HOOK_DIR


def build_windows_tk_options() -> list[str]:
    """Return explicit Tkinter bundle options for Windows PyInstaller builds."""
    tcl_library, tk_library, tkinter_binary, tcl_binary, tk_binary = get_tk_paths()
    missing_paths = [
        path
        for path in (tcl_library, tk_library, tkinter_binary, tcl_binary, tk_binary)
        if not path.exists()
    ]
    if missing_paths:
        missing = ', '.join(str(path) for path in missing_paths)
        raise FileNotFoundError(f'Missing Tcl/Tk runtime files required for Windows build: {missing}')

    data_sep = ';'
    runtime_hook = ensure_windows_tk_runtime_hook()
    hook_dir = ensure_windows_tk_hook_dir()
    return [
        '--additional-hooks-dir',
        str(hook_dir),
        '--hidden-import',
        'tkinter',
        '--hidden-import',
        '_tkinter',
        '--add-data',
        f'{tcl_library}{data_sep}_tcl_data',
        '--add-data',
        f'{tk_library}{data_sep}_tk_data',
        '--add-binary',
        f'{tkinter_binary}{data_sep}.',
        '--add-binary',
        f'{tcl_binary}{data_sep}.',
        '--add-binary',
        f'{tk_binary}{data_sep}.',
        '--runtime-hook',
        str(runtime_hook),
    ]


def build_pyinstaller_env(platform_name: str) -> dict[str, str]:
    env = os.environ.copy()
    if platform_name != 'windows':
        return env

    tcl_root = Path(sys.base_prefix) / 'tcl'
    tcl_library = tcl_root / 'tcl8.6'
    tk_library = tcl_root / 'tk8.6'
    if tcl_library.exists() and tk_library.exists():
        env.setdefault('TCL_LIBRARY', str(tcl_library))
        env.setdefault('TK_LIBRARY', str(tk_library))
    return env


def run_pyinstaller(command: list[str], platform_name: str) -> None:
    subprocess.run(command, cwd=str(ROOT_DIR), env=build_pyinstaller_env(platform_name), check=True)


def build(platform_name: str) -> Path:
    icon_assets = ensure_icon_assets()
    command = build_pyinstaller_command(platform_name, icon_assets)
    run_pyinstaller(command, platform_name)
    artifact_path = find_artifact_path(platform_name)
    release_dir = copy_release_payload(platform_name, artifact_path, icon_assets)
    remove_standalone_artifact(artifact_path, release_dir)
    create_release_archive(platform_name, release_dir)
    return release_dir


def main() -> int:
    args = parse_args()
    release_dir = build(args.platform)
    print(f'Build complete: {release_dir}')
    print(f'Release archive: {DIST_DIR / RELEASE_ASSET_NAMES[args.platform]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
