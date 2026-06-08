#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación principal: escucha global de teclado, buffer y conversión en tiempo real.
Toggle: Ctrl+Alt+Shift+P
"""

import sys
import time
import threading
import os
import logging
import tempfile
from typing import Any, Optional

from pynput import keyboard
import pystray
import platform
import shlex
from tkinter import messagebox

# When running `python src/pinyin_tones/pinyin_live.py`, ensure the src directory
# is on sys.path so package imports resolve correctly.
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if __package__ is None:
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from pinyin_tones.autostart import AutostartConfig, sync_autostart_setting
    from pinyin_tones.config_store import load_config, save_config
    from pinyin_tones.hotkeys import (
        format_hotkey,
        format_hotkey_display,
        normalize_capture_key,
        normalize_pynput_trigger_key,
        normalize_trigger_key,
        parse_hotkey,
    )
    from pinyin_tones.settings_ui import HotkeySettingsDialog, run_hotkey_settings_dialog
    from pinyin_tones.tray_ui import create_tray_image
    from pinyin_tones.update_dialog import run_update_dialog
    from pinyin_tones.update_check import ReleaseInfo, UpdateState
    from pinyin_tones.version import __version__
    from pinyin_tones.paths import get_app_root, get_state_dir
    from pinyin_tones import update_check as _update_check
    from pinyin_tones import clipboard as _clipboard
    from pinyin_tones import buffer as _buffer
    from pinyin_tones import autostart as _autostart

    # Re-export selected functions for backwards compatibility
    paste_text = _clipboard.paste_text
    sync_clipboard_text = _clipboard.sync_clipboard_text
    restore_clipboard_baseline = _clipboard.restore_clipboard_baseline
    delete_last_token = _buffer.delete_last_token
    process_buffer = _buffer.process_buffer
    handle_alpha_char = _buffer.handle_alpha_char
    handle_digit_char = _buffer.handle_digit_char
    reset_buffer = _buffer.reset_buffer
    # Expose internals for backward compatibility (tests and callers)
    BUFFER = _buffer.BUFFER
    BUFFER_LOCK = _buffer.BUFFER_LOCK
    pyperclip = _clipboard.pyperclip

    # Re-export autostart helpers for compatibility (wrap to inject config)
    def get_launch_command_args():
        return _autostart.get_launch_command_args(build_autostart_config())

    def get_launch_command_string():
        return _autostart.get_launch_command_string(build_autostart_config())

    def get_macos_launch_agent_path(label: str):
        return _autostart.get_macos_launch_agent_path(label)

    def get_linux_autostart_path(filename: str):
        return _autostart.get_linux_autostart_path(filename)

    def _get_autostart_target_path() -> str:
        if getattr(sys, "frozen", False):
            return os.path.abspath(sys.executable)
        return os.path.abspath(os.path.join(ROOT_DIR, SCRIPT_REL_PATH))

    def _get_autostart_test_flag() -> str:
        return "-x" if getattr(sys, "frozen", False) else "-f"

    def _build_unix_autostart_guard(cleanup_path: str) -> str:
        launch_cmd = shlex.join(get_launch_command_args())
        target_path = shlex.quote(_get_autostart_target_path())
        cleanup_cmd = shlex.quote(cleanup_path)
        test_flag = _get_autostart_test_flag()
        return (
            f"if [ {test_flag} {target_path} ]; then {launch_cmd}; "
            f"else rm -f {cleanup_cmd}; fi"
        )

    def build_macos_launch_agent_plist():
        # build plist using the local get_launch_command_args so tests can patch it
        guard_cmd = _build_unix_autostart_guard(
            get_macos_launch_agent_path(MAC_LAUNCH_AGENT_LABEL)
        )
        return {
            "Label": MAC_LAUNCH_AGENT_LABEL,
            "ProgramArguments": ["/bin/sh", "-c", guard_cmd],
            "RunAtLoad": True,
            "KeepAlive": False,
            "WorkingDirectory": ROOT_DIR,
            "StandardOutPath": LOG_PATH,
            "StandardErrorPath": LOG_PATH,
        }

    def build_linux_desktop_entry():
        # build desktop entry using the local get_launch_command_args so tests can patch it
        guard_cmd = _build_unix_autostart_guard(
            get_linux_autostart_path(LINUX_AUTOSTART_FILENAME)
        )
        exec_line = shlex.join(["/bin/sh", "-c", guard_cmd])
        return (
            "[Desktop Entry]\n"
            f"Name={APP_NAME}\n"
            "Type=Application\n"
            f"Exec={exec_line}\n"
            "X-GNOME-Autostart-enabled=true\n"
            "NoDisplay=true\n"
            "Terminal=false\n"
        )

    def set_windows_autostart(enabled: bool, config: Optional[AutostartConfig] = None):
        return _autostart.set_windows_autostart(
            enabled, config or build_autostart_config()
        )

    def set_macos_autostart(enabled: bool, config: Optional[AutostartConfig] = None):
        return _autostart.set_macos_autostart(
            enabled, config or build_autostart_config()
        )

    def set_linux_autostart(enabled: bool, config: Optional[AutostartConfig] = None):
        return _autostart.set_linux_autostart(
            enabled, config or build_autostart_config()
        )

    def sync_autostart_setting(
        enabled: bool, config: Optional[AutostartConfig] = None
    ) -> bool:
        # Dispatch to local set_* functions so tests can patch them on pinyin_live
        try:
            system = platform.system()
            if config is None:
                if system == "Windows":
                    set_windows_autostart(enabled)
                elif system == "Darwin":
                    set_macos_autostart(enabled)
                else:
                    set_linux_autostart(enabled)
            else:
                if system == "Windows":
                    set_windows_autostart(enabled, config)
                elif system == "Darwin":
                    set_macos_autostart(enabled, config)
                else:
                    set_linux_autostart(enabled, config)
            return True
        except Exception:
            logger.exception("Failed to sync autostart setting")
            return False

except ImportError:  # pragma: no cover - script execution fallback
    from autostart import AutostartConfig, sync_autostart_setting
    from config_store import load_config, save_config
    from hotkeys import (
        format_hotkey,
        format_hotkey_display,
        normalize_capture_key,
        normalize_pynput_trigger_key,
        normalize_trigger_key,
        parse_hotkey,
    )
    from settings_ui import HotkeySettingsDialog, run_hotkey_settings_dialog
    from tray_ui import create_tray_image
    from update_dialog import run_update_dialog
    from update_check import ReleaseInfo, UpdateState
    from version import __version__
    from paths import get_app_root, get_state_dir
    import update_check as _update_check


# Paths
ROOT_DIR = get_app_root()
STATE_DIR = get_state_dir(ROOT_DIR)
CONFIG_PATH = os.path.join(STATE_DIR, "config.json")
LOG_PATH = os.path.join(STATE_DIR, "pinyin_tones.log")
DOWNLOAD_DIR = os.path.join(STATE_DIR, "downloads")

# Logger
logger = logging.getLogger("pinyin_tones")
PRODUCTION_LOG_LEVEL = logging.ERROR
logger.setLevel(PRODUCTION_LOG_LEVEL)
fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
if not logger.handlers:
    try:
        fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        fh.setLevel(PRODUCTION_LOG_LEVEL)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(PRODUCTION_LOG_LEVEL)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

# Estado global
ACTIVE = True
ACTIVE_LOCK = threading.Lock()
PRESSED_KEYS = set()
DEFAULT_HOTKEY = "<ctrl>+<alt>+<shift>+p"
CONFIG_DIALOG_OPEN = threading.Event()
SETTINGS_REQUESTED = threading.Event()
UPDATE_DIALOG_REQUESTED = threading.Event()
STARTUP_ENABLED_DEFAULT = False
UPDATE_CHECK_ENABLED_DEFAULT = True
UPDATE_CHECK_INTERVAL_HOURS_DEFAULT = 24
DEFAULT_CONFIG = {
    "hotkey": DEFAULT_HOTKEY,
    "autostart": STARTUP_ENABLED_DEFAULT,
    "update_check_enabled": UPDATE_CHECK_ENABLED_DEFAULT,
    "update_check_interval_hours": UPDATE_CHECK_INTERVAL_HOURS_DEFAULT,
    "last_update_check_at": None,
    "downloaded_update_version": None,
    "downloaded_update_path": None,
}
STOP_REQUESTED = threading.Event()
DIALOG_TITLE = "Configuración"
APP_NAME = "Pinyin Tones"
APP_VERSION = __version__
WINDOWS_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_RUN_VALUE_NAME = "Pinyin Tones"
MAC_LAUNCH_AGENT_LABEL = "com.federico.pinyin-tones"
LINUX_AUTOSTART_FILENAME = "pinyin-tones.desktop"
SCRIPT_REL_PATH = os.path.join("src", "pinyin_tones", "pinyin_live.py")
SINGLE_INSTANCE_LOCK_FILENAME = "pinyin-tones.lock"


def build_autostart_config() -> AutostartConfig:
    """Build the autostart config from the current runtime paths."""
    return AutostartConfig(
        root_dir=ROOT_DIR,
        log_path=LOG_PATH,
        app_name=APP_NAME,
        windows_run_key_path=WINDOWS_RUN_KEY_PATH,
        windows_run_value_name=WINDOWS_RUN_VALUE_NAME,
        mac_label=MAC_LAUNCH_AGENT_LABEL,
        linux_autostart_filename=LINUX_AUTOSTART_FILENAME,
        script_rel_path=SCRIPT_REL_PATH,
    )


def get_single_instance_lock_path() -> str:
    """Return the per-user lock path used to prevent duplicate app instances."""
    return os.path.join(tempfile.gettempdir(), SINGLE_INSTANCE_LOCK_FILENAME)


class SingleInstanceLock:
    """Non-blocking process lock held while the desktop app is running."""

    def __init__(self, path: str):
        self.path = path
        self.handle: Optional[Any] = None

    def acquire(self) -> bool:
        """Acquire the lock, returning False when another instance holds it."""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        handle = open(self.path, "a+", encoding="utf-8")
        try:
            self._lock_handle(handle)
        except OSError:
            handle.close()
            return False
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        self.handle = handle
        return True

    def release(self) -> None:
        """Release the held lock."""
        if self.handle is None:
            return
        try:
            self._unlock_handle(self.handle)
        except OSError:
            pass
        try:
            self.handle.close()
        finally:
            self.handle = None

    def _lock_handle(self, handle: Any) -> None:
        handle.seek(0)
        if platform.system() == "Windows":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock_handle(self, handle: Any) -> None:
        handle.seek(0)
        if platform.system() == "Windows":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            return
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def __enter__(self):
        if not self.acquire():
            return None
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        self.release()


def is_configuration_open() -> bool:
    """Return True when the settings dialog is open."""
    return CONFIG_DIALOG_OPEN.is_set()


def is_input_suppressed() -> bool:
    """Return True if synthetic input should be ignored."""
    return _buffer.is_input_suppressed()


def sync_clipboard_text(expected_text: str):
    return _clipboard.sync_clipboard_text(expected_text)


def restore_clipboard_baseline():
    return _clipboard.restore_clipboard_baseline()


def schedule_clipboard_restore():
    return _clipboard.schedule_clipboard_restore()


def paste_text(text: str):
    return _clipboard.paste_text(text)


def delete_last_token():
    """Delete the current buffered token from the focused app."""
    return _buffer.delete_last_token()


def process_buffer():
    return _buffer.process_buffer()


def handle_alpha_char(char: str):
    return _buffer.handle_alpha_char(char)


def handle_digit_char(char: str):
    return _buffer.handle_digit_char(char)


def on_type(key):
    """Handle global keypress events when active."""
    if is_input_suppressed() or is_configuration_open():
        return
    if key == keyboard.Key.backspace:
        with _buffer.BUFFER_LOCK:
            if _buffer.BUFFER:
                _buffer.BUFFER.pop()
                logger.debug(f"Buffer after backspace: {''.join(_buffer.BUFFER)}")
        return
    try:
        char = key.char
        logger.info("on_type char=%r suppressed=%s", char, is_input_suppressed())
    except AttributeError:
        _buffer.reset_buffer()
        return
    if char is None:
        _buffer.reset_buffer()
        return
    with ACTIVE_LOCK:
        if not ACTIVE:
            return
    if char.isalpha() and (char.isascii() or char in "vVüÜ"):
        _buffer.handle_alpha_char(char)
    elif char.isdigit() and char in "12345":
        _buffer.handle_digit_char(char)
    else:
        logger.debug(f"Resetting buffer on non-token char: {repr(char)}")
        _buffer.reset_buffer()


class PinyinApp:
    """Application controller for listeners, tray, and settings."""

    def __init__(self):
        """Initialize app state and listeners."""
        self.config = load_config(CONFIG_PATH, DEFAULT_CONFIG)
        self.hotkey = self.config.get("hotkey", DEFAULT_HOTKEY)
        self.autostart_enabled = bool(
            self.config.get("autostart", STARTUP_ENABLED_DEFAULT)
        )
        self.hotkey_modifiers, self.hotkey_trigger = parse_hotkey(self.hotkey)
        self.type_listener: Optional[keyboard.Listener] = None
        self.toggle_listener: Optional[keyboard.Listener] = None
        self.icon: Optional[Any] = None
        self.autostart_config = build_autostart_config()
        self.update_state = UpdateState(status="idle")
        self.update_lock = threading.Lock()
        self._build_listeners()
        self._prune_downloaded_update_state()

    def _build_listeners(self):
        """Create global keyboard listeners."""
        self.type_listener = keyboard.Listener(on_press=on_type)
        self.toggle_listener = keyboard.Listener(
            on_press=self._toggle_on_press, on_release=self._toggle_on_release
        )
        logger.info("Keyboard listeners created")

    def start(self):
        """Start listeners and tray icon."""
        try:
            if self.autostart_enabled:
                sync_autostart_setting(True, self.autostart_config)
            if self.type_listener:
                logger.info("Starting typing listener")
                self.type_listener.start()
            if self.toggle_listener:
                logger.info("Starting hotkey listener")
                self.toggle_listener.start()
            self.request_update_check()
            threading.Thread(target=self._run_tray_safe, daemon=True).start()
        except Exception:
            logger.exception("Failed to start application listeners")
            self.stop()
            raise

    def stop(self):
        """Stop listeners and tray icon."""
        try:
            if self.toggle_listener:
                self.toggle_listener.stop()
        except Exception:
            pass
        try:
            if self.type_listener:
                self.type_listener.stop()
        except Exception:
            pass
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

    def refresh_hotkey(self):
        """Recompute hotkey modifiers and trigger from config."""
        self.hotkey_modifiers, self.hotkey_trigger = parse_hotkey(self.hotkey)
        logger.info(f"Hotkey updated to {self.hotkey}")

    def _save_config(self) -> None:
        save_config(CONFIG_PATH, self.config)

    def _downloads_dir(self) -> str:
        return _update_check.ensure_download_dir(DOWNLOAD_DIR)

    def _prune_downloaded_update_state(self) -> None:
        downloaded_version = self.config.get("downloaded_update_version")
        downloaded_path = self.config.get("downloaded_update_path")
        if not downloaded_version or not downloaded_path:
            return
        if not os.path.exists(downloaded_path) or not _update_check.is_newer_version(
            downloaded_version, APP_VERSION
        ):
            self.config["downloaded_update_version"] = None
            self.config["downloaded_update_path"] = None
            self._save_config()

    def _set_update_state(self, state: UpdateState) -> None:
        with self.update_lock:
            self.update_state = state
        if self.icon and hasattr(self.icon, "update_menu"):
            try:
                self.icon.update_menu()
            except Exception:
                pass

    def _get_update_state(self) -> UpdateState:
        with self.update_lock:
            return self.update_state

    def _should_prompt_for_update(
        self, state: UpdateState, force_prompt: bool = False
    ) -> bool:
        return state.status == "available" and state.latest_release is not None

    def request_update_check(self, force: bool = False) -> None:
        """Start a background update check."""
        logger.info("Queueing update check force=%s", force)
        thread = threading.Thread(
            target=self._run_update_check,
            kwargs={"force": force},
            daemon=True,
        )
        thread.start()

    def _run_update_check(self, force: bool = False) -> None:
        """Fetch latest release information without blocking the tray loop."""
        if not force and not _update_check.should_check_for_updates(self.config):
            logger.info("Skipping update check because interval has not elapsed")
            return
        logger.info(
            "Starting update check force=%s current_version=%s", force, APP_VERSION
        )
        self._set_update_state(UpdateState(status="checking"))
        state = _update_check.check_for_updates(
            current_version=APP_VERSION,
            downloaded_version=self.config.get("downloaded_update_version"),
            downloaded_path=self.config.get("downloaded_update_path"),
        )
        _update_check.mark_update_check(self.config)
        self._save_config()
        self._set_update_state(state)
        if state.latest_release is not None:
            logger.info(
                "Update check finished status=%s latest=%s downloaded=%s",
                state.status,
                state.latest_release.version,
                bool(state.downloaded_path),
            )
        else:
            logger.info(
                "Update check finished status=%s error=%r",
                state.status,
                state.last_error,
            )
        if self._should_prompt_for_update(state, force_prompt=force):
            logger.info(
                "Requesting update dialog for version=%s", state.latest_release.version
            )
            UPDATE_DIALOG_REQUESTED.set()

    def _update_status_label(self, _item=None) -> str:
        state = self._get_update_state()
        if state.status == "checking":
            return "Buscando actualizaciones..."
        if state.status == "available" and state.latest_release and state.downloaded_path:
            return f"Actualización descargada: v{state.latest_release.version}"
        if state.status == "available" and state.latest_release:
            return f"Nueva versión disponible: v{state.latest_release.version}"
        if state.status == "up_to_date":
            return "Actualizado"
        if state.status == "error":
            return "No se pudo buscar actualizaciones"
        return "Actualizado"

    def _app_info_label(self, _item=None) -> str:
        return f"{APP_NAME} v{APP_VERSION}"

    def _update_menu_label(self, _item=None) -> str:
        state = self._get_update_state()
        if state.status == "checking":
            return "Buscando actualizaciones..."
        if state.status == "available" and state.latest_release and state.downloaded_path:
            return f"Actualización descargada (v{state.latest_release.version})"
        if state.status == "available" and state.latest_release:
            return f"Actualización disponible (v{state.latest_release.version})"
        if state.status in {"idle", "up_to_date"}:
            return "Actualizado"
        if state.status == "error":
            return "No se pudo buscar actualización"
        return "Actualizado"

    def _can_open_download_folder(self, _item=None) -> bool:
        path = self.config.get("downloaded_update_path")
        return bool(path and os.path.exists(path))

    def _can_download_update(self, _item=None) -> bool:
        state = self._get_update_state()
        if state.status != "available":
            return False
        release = state.latest_release
        if release is None or not release.asset_name:
            return False
        return bool(release.asset_url)

    def _should_show_update_menu(self, _item=None) -> bool:
        return self._can_download_update()

    def open_download_folder(self, *_):
        """Open the downloaded update folder when available."""
        path = self.config.get("downloaded_update_path")
        if not path:
            return
        try:
            logger.info("Opening update download folder path=%s", path)
            _update_check.open_download_folder(path)
        except Exception:
            logger.exception("Failed to open update download folder")

    def download_latest_update(self) -> bool:
        """Download the latest compatible release asset and guide the user."""
        state = self._get_update_state()
        release = state.latest_release
        if release is None or not release.asset_name:
            logger.info("No compatible downloadable asset found for latest release")
            messagebox.showinfo(
                "Actualización",
                "No hay una descarga automática disponible para este sistema en esta release.",
            )
            return True
        if not release.asset_url:
            logger.info("No compatible downloadable asset found for latest release")
            messagebox.showinfo(
                "Actualización",
                "No hay una descarga automática disponible para este sistema en esta release.",
            )
            return True
        existing_path = _update_check.existing_download_for_release(
            release,
            self.config.get("downloaded_update_version"),
            self.config.get("downloaded_update_path"),
        )
        try:
            if existing_path is None:
                logger.info(
                    "Downloading update version=%s asset=%s",
                    release.version,
                    release.asset_name,
                )
                existing_path = _update_check.download_release_asset(
                    release,
                    self._downloads_dir(),
                )
            else:
                logger.info(
                    "Reusing previously downloaded update version=%s path=%s",
                    release.version,
                    existing_path,
                )
            self.config["downloaded_update_version"] = release.version
            self.config["downloaded_update_path"] = existing_path
            self._save_config()
            state.downloaded_path = existing_path
            self._set_update_state(state)
            _update_check.open_download_folder(existing_path)
            messagebox.showinfo(
                "Actualización descargada",
                "La nueva versión se descargó correctamente. Cerrá la app actual y reemplazá o instalá el paquete descargado.",
            )
            return True
        except Exception as exc:
            logger.exception("Failed to download update")
            messagebox.showerror(
                "Error de actualización",
                f"No se pudo descargar la actualización.\n\n{exc}",
            )
            return False

    def remind_update_later(self) -> None:
        """Leave the update available without muting future notifications."""
        logger.info("Update reminder deferred by user")

    def show_update_dialog(self) -> None:
        """Open the update-available dialog on the main thread."""
        state = self._get_update_state()
        release = state.latest_release
        if release is None:
            return
        run_update_dialog(
            self,
            APP_VERSION,
            release,
            logger,
            self.download_latest_update,
            self.remind_update_later,
        )

    def toggle_active(self):
        """Toggle the live conversion state."""
        global ACTIVE
        with ACTIVE_LOCK:
            ACTIVE = not ACTIVE
            print("Modo Pinyin:", "ACTIVADO" if ACTIVE else "DESACTIVADO")
        logger.info(f"Toggled ACTIVE -> {ACTIVE}")
        if self.icon:
            self.icon.icon = create_tray_image(ACTIVE)
            if hasattr(self.icon, "update_menu"):
                try:
                    self.icon.update_menu()
                except Exception:
                    pass

    def _is_active(self) -> bool:
        with ACTIVE_LOCK:
            return ACTIVE

    def is_active(self) -> bool:
        return self._is_active()

    def _tray_toggle_label(self, _item=None) -> str:
        label = "Desactivar" if self._is_active() else "Activar"
        shortcut = format_hotkey_display(self.hotkey_modifiers, self.hotkey_trigger)
        if not shortcut:
            return label
        if platform.system() == "Windows":
            # Tab separates the label from the right-aligned accelerator column on Windows menus.
            return f"{label}\t{shortcut}"
        return f"{label} ({shortcut})"

    def open_settings(self, *_):
        """Request opening the settings dialog from the tray."""
        if CONFIG_DIALOG_OPEN.is_set():
            return
        logger.info("Tray requested settings dialog")
        SETTINGS_REQUESTED.set()

    def _toggle_on_press(self, key):
        """Handle key-down events for the toggle hotkey."""
        if is_configuration_open():
            return
        try:
            trigger = normalize_pynput_trigger_key(key)
            logger.info(
                f"Hotkey press received: key={key!r}, trigger={trigger!r}, pressed={sorted(PRESSED_KEYS)}"
            )
            if trigger and trigger == self.hotkey_trigger:
                PRESSED_KEYS.add("trigger")
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
                PRESSED_KEYS.add("ctrl")
            if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                PRESSED_KEYS.add("shift")
            if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
                PRESSED_KEYS.add("alt")
            if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                PRESSED_KEYS.add("cmd")
            if (
                self.hotkey_modifiers.issubset(PRESSED_KEYS)
                and "trigger" in PRESSED_KEYS
            ):
                logger.info(
                    f"Hotkey matched: modifiers={sorted(self.hotkey_modifiers)}, trigger={self.hotkey_trigger!r}"
                )
                self.toggle_active()
        except Exception as exc:
            logger.info(f"Hotkey press handling error: {exc}")

    def _toggle_on_release(self, key):
        """Handle key-up events for the toggle hotkey."""
        if is_configuration_open():
            return
        try:
            trigger = normalize_pynput_trigger_key(key)
            logger.info(
                f"Hotkey release received: key={key!r}, trigger={trigger!r}, pressed_before={sorted(PRESSED_KEYS)}"
            )
            if trigger and trigger == self.hotkey_trigger:
                PRESSED_KEYS.discard("trigger")
        except Exception:
            pass
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
            PRESSED_KEYS.discard("ctrl")
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            PRESSED_KEYS.discard("shift")
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            PRESSED_KEYS.discard("alt")
        if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            PRESSED_KEYS.discard("cmd")

    def _run_tray(self):
        """Run the system tray icon loop."""
        image = create_tray_image(ACTIVE)
        menu = pystray.Menu(
            pystray.MenuItem(self._app_info_label, lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(self._tray_toggle_label, lambda: self.toggle_active()),
            pystray.MenuItem("Configuración", lambda: self.open_settings()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                self._update_menu_label,
                pystray.Menu(
                    pystray.MenuItem(
                        "Descargar actualización",
                        lambda: self.download_latest_update(),
                        enabled=self._can_download_update,
                    ),
                    pystray.MenuItem(
                        "Abrir carpeta de descargas",
                        lambda: self.open_download_folder(),
                        enabled=self._can_open_download_folder,
                    ),
                ),
                visible=self._should_show_update_menu,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", lambda: quit_app(self)),
        )
        self.icon = pystray.Icon("pinyin", image, f"{APP_NAME} v{APP_VERSION}", menu)
        if self.icon:
            self.icon.run()

    def _run_tray_safe(self):
        """Run the tray loop and stop the app if tray initialization fails."""
        try:
            self._run_tray()
        except Exception:
            logger.exception("System tray failed")
            STOP_REQUESTED.set()


def quit_app(app: PinyinApp):
    """Stop the app and signal the main loop to exit."""
    STOP_REQUESTED.set()
    try:
        app.stop()
    except Exception:
        pass
    try:
        if app.icon:
            app.icon.stop()
    except Exception:
        pass


def run_hotkey_settings_dialog_for_app(app: PinyinApp) -> None:
    """Open the settings dialog with proper runtime dependencies."""
    CONFIG_DIALOG_OPEN.set()
    try:
        run_hotkey_settings_dialog(
            app,
            DIALOG_TITLE,
            logger,
            lambda enabled: sync_autostart_setting(enabled, build_autostart_config()),
            lambda cfg: save_config(CONFIG_PATH, cfg),
            STARTUP_ENABLED_DEFAULT,
        )
    finally:
        CONFIG_DIALOG_OPEN.clear()


def run_update_dialog_for_app(app: PinyinApp) -> None:
    """Open the update notification dialog on the main thread."""
    CONFIG_DIALOG_OPEN.set()
    try:
        app.show_update_dialog()
    finally:
        CONFIG_DIALOG_OPEN.clear()


def show_startup_error(exc: Exception) -> None:
    """Show a startup error when GUI dialogs are available."""
    try:
        messagebox.showerror(
            APP_NAME,
            "No se pudo iniciar Pinyin Tones.\n\n"
            "Revisá permisos de teclado/accesibilidad o reiniciá la aplicación.\n\n"
            f"Detalle: {exc}",
        )
    except Exception:
        pass


def main():
    """Entry point for the desktop app."""
    with SingleInstanceLock(get_single_instance_lock_path()) as instance_lock:
        if instance_lock is None:
            message = f"Another {APP_NAME} instance is already running; exiting"
            logger.info(message)
            print(message, file=sys.stderr)
            return
        _run_main_loop()


def _run_main_loop():
    """Run the desktop app after the single-instance guard is held."""
    print("Pinyin Tones - Running")
    print("Usá el ícono en la bandeja para ver el estado y modificar atajo")
    app = PinyinApp()
    logger.info(
        f"App starting with hotkey={app.hotkey!r}, modifiers={sorted(app.hotkey_modifiers)}, trigger={app.hotkey_trigger!r}"
    )
    try:
        app.start()
    except Exception as exc:
        show_startup_error(exc)
        return
    try:
        while not STOP_REQUESTED.is_set():
            if SETTINGS_REQUESTED.is_set() and not CONFIG_DIALOG_OPEN.is_set():
                SETTINGS_REQUESTED.clear()
                logger.info(
                    "Settings requested from tray; opening dialog on main thread"
                )
                run_hotkey_settings_dialog_for_app(app)
                continue
            if UPDATE_DIALOG_REQUESTED.is_set() and not CONFIG_DIALOG_OPEN.is_set():
                UPDATE_DIALOG_REQUESTED.clear()
                logger.info("Update dialog requested; opening on main thread")
                run_update_dialog_for_app(app)
                continue
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nSaliendo...")
        app.stop()
        sys.exit(0)
    finally:
        app.stop()


if __name__ == "__main__":
    main()
