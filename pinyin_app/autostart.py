"""Autostart helpers for Windows, macOS, and Linux."""

from __future__ import annotations

import os
import platform
import plistlib
import shlex
import subprocess
import sys
import logging
from dataclasses import dataclass
from typing import List

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows platforms
    winreg = None

logger = logging.getLogger('pinyin_app')


@dataclass(frozen=True)
class AutostartConfig:
    """Configuration values needed for autostart integration."""
    root_dir: str
    log_path: str
    app_name: str
    windows_run_key_path: str
    windows_run_value_name: str
    mac_label: str
    linux_autostart_filename: str
    script_rel_path: str = 'pinyin_live.py'


def get_launch_command_args(config: AutostartConfig) -> List[str]:
    """Return the command used to launch the app in the current environment."""
    script_path = os.path.abspath(os.path.join(config.root_dir, config.script_rel_path))
    if getattr(sys, 'frozen', False):
        return [os.path.abspath(sys.executable)]
    return [os.path.abspath(sys.executable), script_path]


def get_launch_command_string(config: AutostartConfig) -> str:
    """Return a shell-escaped string for startup entries."""
    return subprocess.list2cmdline(get_launch_command_args(config))


def get_macos_launch_agent_path(label: str) -> str:
    """Return the LaunchAgent plist path for macOS."""
    return os.path.expanduser(f'~/Library/LaunchAgents/{label}.plist')


def get_linux_autostart_path(filename: str) -> str:
    """Return the autostart desktop file path for Linux."""
    return os.path.expanduser(f'~/.config/autostart/{filename}')


def build_macos_launch_agent_plist(config: AutostartConfig) -> dict:
    """Build the macOS LaunchAgent plist contents."""
    return {
        'Label': config.mac_label,
        'ProgramArguments': get_launch_command_args(config),
        'RunAtLoad': True,
        'KeepAlive': False,
        'WorkingDirectory': config.root_dir,
        'StandardOutPath': config.log_path,
        'StandardErrorPath': config.log_path,
    }


def build_linux_desktop_entry(config: AutostartConfig) -> str:
    """Build the Linux autostart desktop entry text."""
    exec_line = shlex.join(get_launch_command_args(config))
    return (
        '[Desktop Entry]\n'
        f'Name={config.app_name}\n'
        'Type=Application\n'
        f'Exec={exec_line}\n'
        'X-GNOME-Autostart-enabled=true\n'
        'NoDisplay=true\n'
        'Terminal=false\n'
    )


def set_windows_autostart(enabled: bool, config: AutostartConfig) -> None:
    """Create or remove the Windows Run registry entry."""
    if winreg is None:
        raise RuntimeError('Windows registry access is not available')
    command = get_launch_command_string(config)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, config.windows_run_key_path) as key:
        if enabled:
            winreg.SetValueEx(key, config.windows_run_value_name, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, config.windows_run_value_name)
            except FileNotFoundError:
                pass


def set_macos_autostart(enabled: bool, config: AutostartConfig) -> None:
    """Create or remove the macOS LaunchAgent."""
    path = get_macos_launch_agent_path(config.mac_label)
    if enabled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            plistlib.dump(build_macos_launch_agent_plist(config), handle)
    elif os.path.exists(path):
        os.remove(path)


def set_linux_autostart(enabled: bool, config: AutostartConfig) -> None:
    """Create or remove the Linux autostart desktop entry."""
    path = get_linux_autostart_path(config.linux_autostart_filename)
    if enabled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(build_linux_desktop_entry(config))
    elif os.path.exists(path):
        os.remove(path)


def sync_autostart_setting(enabled: bool, config: AutostartConfig) -> bool:
    """Apply the autostart change for the current operating system."""
    try:
        system = platform.system()
        if system == 'Windows':
            set_windows_autostart(enabled, config)
        elif system == 'Darwin':
            set_macos_autostart(enabled, config)
        else:
            set_linux_autostart(enabled, config)
        return True
    except Exception:
        logger.exception('Failed to sync autostart setting')
        return False
