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


def get_autostart_target_path(config: AutostartConfig) -> str:
    """Return the path to verify when starting from autostart."""
    if getattr(sys, 'frozen', False):
        return os.path.abspath(sys.executable)
    return os.path.abspath(os.path.join(config.root_dir, config.script_rel_path))


def get_autostart_test_flag() -> str:
    """Return the test flag used by sh to validate the launch target."""
    return '-x' if getattr(sys, 'frozen', False) else '-f'


def get_windows_autostart_target(config: AutostartConfig) -> str:
    """Return the path that should exist for Windows autostart validation."""
    return get_autostart_target_path(config)


def get_windows_autostart_command(config: AutostartConfig) -> str:
    """Return a Windows Run command that self-cleans when the target is missing."""
    launch_cmd = get_launch_command_string(config)
    target_path = get_windows_autostart_target(config)
    reg_key = f'HKCU\\{config.windows_run_key_path}'
    reg_value = config.windows_run_value_name
    return (
        'cmd /c '
        f'if exist "{target_path}" '
        f'start "" {launch_cmd} '
        f'else reg delete "{reg_key}" /v "{reg_value}" /f'
    )


def get_macos_launch_agent_path(label: str) -> str:
    """Return the LaunchAgent plist path for macOS."""
    return os.path.expanduser(f'~/Library/LaunchAgents/{label}.plist')


def get_linux_autostart_path(filename: str) -> str:
    """Return the autostart desktop file path for Linux."""
    return os.path.expanduser(f'~/.config/autostart/{filename}')


def build_macos_launch_agent_plist(config: AutostartConfig) -> dict:
    """Build the macOS LaunchAgent plist contents."""
    cleanup_path = get_macos_launch_agent_path(config.mac_label)
    target_path = shlex.quote(get_autostart_target_path(config))
    test_flag = get_autostart_test_flag()
    launch_cmd = shlex.join(get_launch_command_args(config))
    cleanup_cmd = shlex.quote(cleanup_path)
    guard_cmd = (
        f'if [ {test_flag} {target_path} ]; then {launch_cmd}; '
        f'else rm -f {cleanup_cmd}; fi'
    )
    return {
        'Label': config.mac_label,
        'ProgramArguments': ['/bin/sh', '-c', guard_cmd],
        'RunAtLoad': True,
        'KeepAlive': False,
        'WorkingDirectory': config.root_dir,
        'StandardOutPath': config.log_path,
        'StandardErrorPath': config.log_path,
    }


def build_linux_desktop_entry(config: AutostartConfig) -> str:
    """Build the Linux autostart desktop entry text."""
    cleanup_path = get_linux_autostart_path(config.linux_autostart_filename)
    target_path = shlex.quote(get_autostart_target_path(config))
    test_flag = get_autostart_test_flag()
    launch_cmd = shlex.join(get_launch_command_args(config))
    cleanup_cmd = shlex.quote(cleanup_path)
    guard_cmd = (
        f'if [ {test_flag} {target_path} ]; then {launch_cmd}; '
        f'else rm -f {cleanup_cmd}; fi'
    )
    exec_line = shlex.join(['/bin/sh', '-c', guard_cmd])
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
    command = get_windows_autostart_command(config)
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
