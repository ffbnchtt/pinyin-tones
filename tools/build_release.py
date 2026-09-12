#!/usr/bin/env python3
"""Build helper for packaging the Pinyin app across platforms.

This script centralizes the common build steps so the platform wrappers only
pass the target operating system.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import plistlib
import re
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
DISPLAY_NAME = 'Pinyin Tones'
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
SUPPORTED_ARCHITECTURES = {
    'windows': ('x64',),
    'macos': ('x64', 'arm64'),
    'linux': ('x64',),
}
SUPPORTED_FORMATS = {
    'windows': ('portable',),
    'macos': ('portable', 'dmg'),
    'linux': ('portable', 'appimage', 'deb'),
}
PACKAGE_ROOT = ROOT_DIR / 'packaging'
LINUX_PACKAGE_DIR = PACKAGE_ROOT / 'linux'
PROJECT_VERSION_FILE = ROOT_DIR / 'pyproject.toml'


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
    parser.add_argument(
        '--arch',
        choices=('x64', 'arm64'),
        default=normalize_architecture(platform.machine()),
        help='Target CPU architecture. Builds must run on a matching native runner.',
    )
    parser.add_argument(
        '--formats',
        default=None,
        help='Comma-separated formats: portable, dmg, appimage, deb. Defaults to the platform set.',
    )
    parser.add_argument(
        '--package-from-payload',
        action='store_true',
        help='Create archives/installers from an existing release payload without running PyInstaller.',
    )
    return parser.parse_args()


def normalize_architecture(machine_name: str) -> str:
    """Map common machine names to release architecture labels."""
    normalized = machine_name.strip().lower()
    aliases = {
        'amd64': 'x64',
        'x86_64': 'x64',
        'x64': 'x64',
        'aarch64': 'arm64',
        'arm64': 'arm64',
    }
    return aliases.get(normalized, normalized)


def parse_formats(platform_name: str, value: str | None = None) -> tuple[str, ...]:
    """Return validated release formats for a platform."""
    supported = SUPPORTED_FORMATS[platform_name]
    if value is None:
        return supported
    formats = tuple(item.strip().lower() for item in value.split(',') if item.strip())
    if not formats:
        raise ValueError('At least one release format is required')
    unsupported = set(formats).difference(supported)
    if unsupported:
        supported_text = ', '.join(supported)
        requested_text = ', '.join(sorted(unsupported))
        raise ValueError(f'Unsupported {platform_name} format(s): {requested_text}. Use: {supported_text}')
    return formats


def validate_target(platform_name: str, architecture: str) -> None:
    """Reject unsupported or cross-platform packaging requests."""
    if architecture not in SUPPORTED_ARCHITECTURES[platform_name]:
        raise ValueError(f'Unsupported architecture for {platform_name}: {architecture}')
    current_platform = normalize_platform_name(platform.system())
    current_arch = normalize_architecture(platform.machine())
    if current_platform != platform_name or current_arch != architecture:
        raise RuntimeError(
            f'Build {platform_name}/{architecture} on a matching native runner; '
            f'current host is {current_platform}/{current_arch}.'
        )


def release_asset_name(platform_name: str, architecture: str, release_format: str) -> str:
    """Return the stable public file name for a release asset."""
    if platform_name not in SUPPORTED_FORMATS:
        raise ValueError(f'Unsupported release platform: {platform_name}')
    if release_format == 'portable':
        if platform_name in {'windows', 'linux'}:
            return RELEASE_ASSET_NAMES[platform_name]
        return f'pinyin-tones-macos-{architecture}.zip'
    if platform_name == 'macos' and release_format == 'dmg':
        return f'pinyin-tones-macos-{architecture}.dmg'
    if platform_name == 'linux' and release_format == 'appimage':
        return 'pinyin-tones-linux-x86_64.AppImage'
    if platform_name == 'linux' and release_format == 'deb':
        return 'pinyin-tones-linux-amd64.deb'
    raise ValueError(f'Unsupported release format: {platform_name}/{release_format}')


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


def build_pyinstaller_command(
    platform_name: str,
    icon_assets: dict[str, Path],
    architecture: str | None = None,
) -> list[str]:
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
        if architecture:
            target_architecture = 'x86_64' if architecture == 'x64' else architecture
            command.extend(['--target-architecture', target_architecture])
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


def release_payload_directory(platform_name: str, architecture: str | None = None) -> Path:
    """Return the staging directory for a platform-specific release payload."""
    if architecture is None:
        return RELEASE_DIR / platform_name
    return RELEASE_DIR / platform_name / architecture


def copy_release_payload(
    platform_name: str,
    artifact_path: Path,
    icon_assets: dict[str, Path],
    architecture: str | None = None,
) -> Path:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    platform_release_dir = release_payload_directory(platform_name, architecture)
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


def create_release_archive(
    platform_name: str,
    release_dir: Path,
    architecture: str = 'x64',
) -> Path:
    """Create the upload-ready GitHub release archive for a platform payload."""
    asset_name = release_asset_name(platform_name, architecture, 'portable')

    archive_path = DIST_DIR / asset_name
    if archive_path.exists():
        archive_path.unlink()

    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(release_dir.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(release_dir))
    return archive_path


def project_version() -> str:
    """Read the package version without importing application dependencies."""
    match = re.search(
        r'^version\s*=\s*"([^"]+)"\s*$',
        PROJECT_VERSION_FILE.read_text(encoding='utf-8'),
        flags=re.MULTILINE,
    )
    if not match:
        raise ValueError(f'Could not find project version in {PROJECT_VERSION_FILE}')
    return match.group(1)


def create_macos_dmg(release_dir: Path, architecture: str) -> Path:
    """Create a macOS drag-and-drop installer from a signed app payload."""
    app_bundles = list(release_dir.glob('*.app'))
    if len(app_bundles) != 1:
        raise FileNotFoundError(f'Expected one .app bundle in {release_dir}')
    if shutil.which('hdiutil') is None:
        raise RuntimeError('hdiutil is required to create a macOS DMG')

    staging_dir = BUILD_DIR / 'dmg' / architecture
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)
    shutil.copytree(app_bundles[0], staging_dir / f'{DISPLAY_NAME}.app')
    applications_link = staging_dir / 'Applications'
    applications_link.symlink_to('/Applications')

    destination = DIST_DIR / release_asset_name('macos', architecture, 'dmg')
    if destination.exists():
        destination.unlink()
    subprocess.run(
        [
            'hdiutil', 'create', '-volname', DISPLAY_NAME, '-srcfolder', str(staging_dir),
            '-ov', '-format', 'UDZO', str(destination),
        ],
        check=True,
    )
    return destination


def linux_desktop_entry() -> str:
    """Return the desktop metadata shared by AppImage and DEB packages."""
    template = LINUX_PACKAGE_DIR / 'pinyin-tones.desktop'
    return template.read_text(encoding='utf-8').format(version=project_version())


def _write_executable(path: Path, contents: str) -> None:
    path.write_text(contents, encoding='utf-8', newline='\n')
    path.chmod(path.stat().st_mode | 0o111)


def create_linux_appimage(
    release_dir: Path,
    architecture: str,
    icon_assets: dict[str, Path],
) -> Path:
    """Build an AppImage from the portable Linux payload."""
    if architecture != 'x64':
        raise ValueError('AppImage packaging currently supports x64 only')
    executable = release_dir / APP_NAME
    if not executable.exists():
        raise FileNotFoundError(f'Missing Linux executable: {executable}')
    appimagetool = os.environ.get('APPIMAGETOOL') or shutil.which('appimagetool')
    if not appimagetool:
        raise RuntimeError('Set APPIMAGETOOL or install appimagetool to build an AppImage')

    appdir = BUILD_DIR / 'appimage' / f'{DISPLAY_NAME}.AppDir'
    if appdir.exists():
        shutil.rmtree(appdir)
    bin_dir = appdir / 'usr' / 'bin'
    icon_dir = appdir / 'usr' / 'share' / 'icons' / 'hicolor' / '256x256' / 'apps'
    applications_dir = appdir / 'usr' / 'share' / 'applications'
    bin_dir.mkdir(parents=True)
    icon_dir.mkdir(parents=True)
    applications_dir.mkdir(parents=True)
    shutil.copy2(executable, bin_dir / APP_NAME)
    (bin_dir / APP_NAME).chmod((bin_dir / APP_NAME).stat().st_mode | 0o111)
    shutil.copy2(icon_assets['png'], icon_dir / 'pinyin-tones.png')
    desktop_entry = linux_desktop_entry()
    (applications_dir / 'pinyin-tones.desktop').write_text(desktop_entry, encoding='utf-8')
    (appdir / 'pinyin-tones.desktop').write_text(desktop_entry, encoding='utf-8')
    shutil.copy2(icon_assets['png'], appdir / 'pinyin-tones.png')
    _write_executable(
        appdir / 'AppRun',
        '#!/bin/sh\nexec "$(dirname "$0")/usr/bin/pinyin_tones" "$@"\n',
    )

    destination = DIST_DIR / release_asset_name('linux', architecture, 'appimage')
    if destination.exists():
        destination.unlink()
    subprocess.run([str(appimagetool), '--no-appstream', str(appdir), str(destination)], check=True)
    destination.chmod(destination.stat().st_mode | 0o111)
    return destination


def create_linux_deb(
    release_dir: Path,
    architecture: str,
    icon_assets: dict[str, Path],
) -> Path:
    """Create a Debian package from the Linux portable executable."""
    if architecture != 'x64':
        raise ValueError('DEB packaging currently supports x64 only')
    executable = release_dir / APP_NAME
    if not executable.exists():
        raise FileNotFoundError(f'Missing Linux executable: {executable}')
    if shutil.which('dpkg-deb') is None:
        raise RuntimeError('dpkg-deb is required to create a DEB package')

    package_root = BUILD_DIR / 'deb' / 'root'
    if package_root.exists():
        shutil.rmtree(package_root)
    control_dir = package_root / 'DEBIAN'
    app_dir = package_root / 'opt' / 'pinyin-tones'
    desktop_dir = package_root / 'usr' / 'share' / 'applications'
    icon_dir = package_root / 'usr' / 'share' / 'icons' / 'hicolor' / '256x256' / 'apps'
    bin_dir = package_root / 'usr' / 'bin'
    docs_dir = package_root / 'usr' / 'share' / 'doc' / 'pinyin-tones'
    for directory in (control_dir, app_dir, desktop_dir, icon_dir, bin_dir, docs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    (control_dir / 'control').write_text(
        '\n'.join(
            [
                'Package: pinyin-tones',
                f'Version: {project_version()}',
                'Section: utils',
                'Priority: optional',
                'Architecture: amd64',
                'Depends: libx11-6, libxtst6',
                'Maintainer: Federico Bianchetti',
                'Description: Real-time pinyin tone conversion while you type.',
                '',
            ]
        ),
        encoding='utf-8',
    )
    target = app_dir / APP_NAME
    shutil.copy2(executable, target)
    target.chmod(target.stat().st_mode | 0o111)
    (bin_dir / 'pinyin-tones').symlink_to('/opt/pinyin-tones/pinyin_tones')
    (desktop_dir / 'pinyin-tones.desktop').write_text(linux_desktop_entry(), encoding='utf-8')
    shutil.copy2(icon_assets['png'], icon_dir / 'pinyin-tones.png')
    shutil.copy2(LICENSE_SOURCE, docs_dir / 'copyright')
    shutil.copy2(ensure_user_guide(), docs_dir / 'USER_GUIDE.md')

    destination = DIST_DIR / release_asset_name('linux', architecture, 'deb')
    if destination.exists():
        destination.unlink()
    subprocess.run(['dpkg-deb', '--build', str(package_root), str(destination)], check=True)
    return destination


def create_checksum_file(artifacts: Iterable[Path], destination: Path | None = None) -> Path:
    """Write SHA-256 checksums for release artifacts in deterministic order."""
    checksum_path = destination or DIST_DIR / 'SHA256SUMS.txt'
    lines = []
    for artifact in sorted({Path(path) for path in artifacts}, key=lambda path: path.name):
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        lines.append(f'{digest}  {artifact.name}')
    checksum_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return checksum_path


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


def package_existing_payload(
    platform_name: str,
    architecture: str,
    formats: tuple[str, ...],
    icon_assets: dict[str, Path],
) -> list[Path]:
    """Create selected distributable assets from an already-built payload."""
    release_dir = release_payload_directory(platform_name, architecture)
    if not release_dir.exists():
        raise FileNotFoundError(f'Missing release payload: {release_dir}')
    artifacts: list[Path] = []
    if 'portable' in formats:
        artifacts.append(create_release_archive(platform_name, release_dir, architecture))
    if 'dmg' in formats:
        artifacts.append(create_macos_dmg(release_dir, architecture))
    if 'appimage' in formats:
        artifacts.append(create_linux_appimage(release_dir, architecture, icon_assets))
    if 'deb' in formats:
        artifacts.append(create_linux_deb(release_dir, architecture, icon_assets))
    return artifacts


def build(
    platform_name: str,
    architecture: str | None = None,
    formats: tuple[str, ...] | None = None,
    package_from_payload: bool = False,
) -> tuple[Path, list[Path]]:
    """Build a native payload and package it in the requested release formats."""
    architecture = architecture or normalize_architecture(platform.machine())
    formats = formats or parse_formats(platform_name)
    if architecture not in SUPPORTED_ARCHITECTURES[platform_name]:
        raise ValueError(f'Unsupported architecture for {platform_name}: {architecture}')
    icon_assets = ensure_icon_assets()
    if package_from_payload:
        release_dir = release_payload_directory(platform_name, architecture)
    else:
        validate_target(platform_name, architecture)
        command = build_pyinstaller_command(platform_name, icon_assets, architecture)
        run_pyinstaller(command, platform_name)
        artifact_path = find_artifact_path(platform_name)
        release_dir = copy_release_payload(platform_name, artifact_path, icon_assets, architecture)
        remove_standalone_artifact(artifact_path, release_dir)
    artifacts = package_existing_payload(platform_name, architecture, formats, icon_assets)
    if artifacts:
        artifacts.append(create_checksum_file(artifacts))
    return release_dir, artifacts


def main() -> int:
    args = parse_args()
    formats = parse_formats(args.platform, args.formats)
    release_dir, artifacts = build(
        args.platform,
        architecture=args.arch,
        formats=formats,
        package_from_payload=args.package_from_payload,
    )
    print(f'Build complete: {release_dir}')
    for artifact in artifacts:
        print(f'Release artifact: {artifact}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
