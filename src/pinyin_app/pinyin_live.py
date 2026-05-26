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
from typing import Any, Optional

from pynput import keyboard
import pyautogui
import pystray
import platform
import shlex

# When running `python src/pinyin_app/pinyin_live.py`, ensure the src directory
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
    from pinyin_app.autostart import AutostartConfig, sync_autostart_setting
    from pinyin_app.config_store import load_config, save_config
    from pinyin_app.hotkeys import (
        format_hotkey,
        format_hotkey_display,
        normalize_capture_key,
        normalize_pynput_trigger_key,
        normalize_trigger_key,
        parse_hotkey,
    )
    from pinyin_app.settings_ui import HotkeySettingsDialog, run_hotkey_settings_dialog
    from pinyin_app.tray_ui import create_tray_image
    from pinyin_app import clipboard as _clipboard
    from pinyin_app import buffer as _buffer
    from pinyin_app import autostart as _autostart

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
    pyautogui = getattr(_buffer, "pyautogui", getattr(_clipboard, "pyautogui", None))

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


# Paths
ROOT_DIR = os.path.abspath(os.path.join(SRC_DIR, os.pardir))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
LOG_PATH = os.path.join(ROOT_DIR, "pinyin_app.log")

# Logger
logger = logging.getLogger("pinyin_app")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
fh.setFormatter(fmt)
if not logger.handlers:
    logger.addHandler(fh)

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False


# Estado global
ACTIVE = True
ACTIVE_LOCK = threading.Lock()
PRESSED_KEYS = set()
DEFAULT_HOTKEY = "<ctrl>+<alt>+<shift>+p"
CONFIG_DIALOG_OPEN = threading.Event()
SETTINGS_REQUESTED = threading.Event()
STARTUP_ENABLED_DEFAULT = False
DEFAULT_CONFIG = {"hotkey": DEFAULT_HOTKEY, "autostart": STARTUP_ENABLED_DEFAULT}
STOP_REQUESTED = threading.Event()
DIALOG_TITLE = "Configuración"
APP_NAME = "Pinyin Tones"
WINDOWS_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_RUN_VALUE_NAME = "Pinyin Tones"
MAC_LAUNCH_AGENT_LABEL = "com.federico.pinyin-tones"
LINUX_AUTOSTART_FILENAME = "pinyin-tones.desktop"
SCRIPT_REL_PATH = os.path.join("src", "pinyin_app", "pinyin_live.py")


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
    except AttributeError:
        _buffer.reset_buffer()
        return
    if char is None:
        _buffer.reset_buffer()
        return
    with ACTIVE_LOCK:
        if not ACTIVE:
            return
    if char.isalpha() and (char.isascii() or char in "vV"):
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
        self._build_listeners()

    def _build_listeners(self):
        """Create global keyboard listeners."""
        self.type_listener = keyboard.Listener(on_press=on_type)
        self.toggle_listener = keyboard.Listener(
            on_press=self._toggle_on_press, on_release=self._toggle_on_release
        )
        logger.info("Keyboard listeners created")

    def start(self):
        """Start listeners and tray icon."""
        if self.autostart_enabled:
            sync_autostart_setting(True, self.autostart_config)
        if self.type_listener:
            logger.info("Starting typing listener")
            self.type_listener.start()
        if self.toggle_listener:
            logger.info("Starting hotkey listener")
            self.toggle_listener.start()
        threading.Thread(target=self._run_tray, daemon=True).start()

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
            pystray.MenuItem(self._tray_toggle_label, lambda: self.toggle_active()),
            pystray.MenuItem("Configuración", lambda: self.open_settings()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", lambda: quit_app(self)),
        )
        self.icon = pystray.Icon("pinyin", image, "Pinyin Tones", menu)
        if self.icon:
            self.icon.run()


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


def main():
    """Entry point for the desktop app."""
    print("App de Pinyin en vivo")
    print("Usá el ícono en la bandeja para ver el estado y modificar atajo")
    app = PinyinApp()
    logger.info(
        f"App starting with hotkey={app.hotkey!r}, modifiers={sorted(app.hotkey_modifiers)}, trigger={app.hotkey_trigger!r}"
    )
    app.start()
    try:
        while not STOP_REQUESTED.is_set():
            if SETTINGS_REQUESTED.is_set() and not CONFIG_DIALOG_OPEN.is_set():
                SETTINGS_REQUESTED.clear()
                logger.info(
                    "Settings requested from tray; opening dialog on main thread"
                )
                run_hotkey_settings_dialog_for_app(app)
                continue
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nSaliendo...")
        app.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
