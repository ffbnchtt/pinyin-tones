#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación principal: escucha global de teclado, buffer y conversión en tiempo real.
Toggle: Ctrl+Alt+P
"""

import sys
import time
import json
import threading
import os
import platform
import plistlib
import shlex
import logging
import subprocess
from typing import Any, Optional

from pynput import keyboard
import pyautogui
import pystray
from PIL import Image, ImageDraw, ImageFont, ImageTk
import tkinter as tk
from tkinter import messagebox

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import winreg
except ImportError:
    winreg = None

if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    sys.path.insert(0, os.path.join(base_dir, 'src'))

from pinyin_converter import convert_pinyin_token


# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')
LOG_PATH = os.path.join(ROOT_DIR, 'pinyin_app.log')

# Logger
logger = logging.getLogger('pinyin_app')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_PATH, encoding='utf-8')
fmt = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
fh.setFormatter(fmt)
if not logger.handlers:
    logger.addHandler(fh)

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False


# Estado global
ACTIVE = False
BUFFER = []
BUFFER_LOCK = threading.Lock()
ACTIVE_LOCK = threading.Lock()
PRESSED_KEYS = set()
DEFAULT_HOTKEY = '<ctrl>+<alt>+p'
CONFIG_DIALOG_OPEN = threading.Event()
SETTINGS_REQUESTED = threading.Event()
STARTUP_ENABLED_DEFAULT = False
SUPPRESS_INPUT = False
SUPPRESS_UNTIL = 0.0
STOP_REQUESTED = threading.Event()
CLIPBOARD_RESTORE_DELAY = 0.15
CLIPBOARD_SYNC_TIMEOUT = 0.01
CLIPBOARD_SYNC_POLL = 0.001
CLIPBOARD_BASELINE = None
CLIPBOARD_RESTORE_TIMER = None
CLIPBOARD_RESTORE_LOCK = threading.Lock()
HOTKEY_MODIFIER_ORDER = ('ctrl', 'alt', 'shift', 'cmd')
DIALOG_TITLE = 'Configuración'
APP_NAME = 'Pinyin Tones'
APP_ID = 'pinyin-tones'
WINDOWS_RUN_KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
WINDOWS_RUN_VALUE_NAME = 'Pinyin Tones'
MAC_LAUNCH_AGENT_LABEL = 'com.federico.pinyin-tones'
LINUX_AUTOSTART_FILENAME = 'pinyin-tones.desktop'
ALLOWED_TRIGGER_KEYS = set('abcdefghijklmnopqrstuvwxyz')
TK_MODIFIER_KEYS = {
    'control_l': 'ctrl',
    'control_r': 'ctrl',
    'control': 'ctrl',
    'shift_l': 'shift',
    'shift_r': 'shift',
    'shift': 'shift',
    'alt_l': 'alt',
    'alt_r': 'alt',
    'alt': 'alt',
    'option': 'alt',
    'super_l': 'cmd',
    'super_r': 'cmd',
    'super': 'cmd',
    'meta_l': 'cmd',
    'meta_r': 'cmd',
    'meta': 'cmd',
    'command': 'cmd',
    'cmd': 'cmd',
}


def load_config():
    default = {'hotkey': '<ctrl>+<alt>+p', 'autostart': STARTUP_ENABLED_DEFAULT}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            return {**default, **cfg}
    except Exception:
        return default


def save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print('Error saving config:', exc)


def get_launch_command_args():
    script_path = os.path.abspath(os.path.join(ROOT_DIR, 'src', 'pinyin_live.py'))
    if getattr(sys, 'frozen', False):
        return [os.path.abspath(sys.executable)]
    return [os.path.abspath(sys.executable), script_path]


def get_launch_command_string() -> str:
    return subprocess.list2cmdline(get_launch_command_args())


def get_macos_launch_agent_path() -> str:
    return os.path.expanduser(f'~/Library/LaunchAgents/{MAC_LAUNCH_AGENT_LABEL}.plist')


def get_linux_autostart_path() -> str:
    return os.path.expanduser(f'~/.config/autostart/{LINUX_AUTOSTART_FILENAME}')


def build_macos_launch_agent_plist() -> dict:
    return {
        'Label': MAC_LAUNCH_AGENT_LABEL,
        'ProgramArguments': get_launch_command_args(),
        'RunAtLoad': True,
        'KeepAlive': False,
        'WorkingDirectory': ROOT_DIR,
        'StandardOutPath': LOG_PATH,
        'StandardErrorPath': LOG_PATH,
    }


def build_linux_desktop_entry() -> str:
    exec_line = shlex.join(get_launch_command_args())
    return (
        '[Desktop Entry]\n'
        f'Name={APP_NAME}\n'
        'Type=Application\n'
        f'Exec={exec_line}\n'
        'X-GNOME-Autostart-enabled=true\n'
        'NoDisplay=true\n'
        'Terminal=false\n'
    )


def set_windows_autostart(enabled: bool):
    if winreg is None:
        raise RuntimeError('Windows registry access is not available')
    command = get_launch_command_string()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY_PATH) as key:
        if enabled:
            winreg.SetValueEx(key, WINDOWS_RUN_VALUE_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, WINDOWS_RUN_VALUE_NAME)
            except FileNotFoundError:
                pass


def set_macos_autostart(enabled: bool):
    path = get_macos_launch_agent_path()
    if enabled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            plistlib.dump(build_macos_launch_agent_plist(), f)
    elif os.path.exists(path):
        os.remove(path)


def set_linux_autostart(enabled: bool):
    path = get_linux_autostart_path()
    if enabled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(build_linux_desktop_entry())
    elif os.path.exists(path):
        os.remove(path)


def sync_autostart_setting(enabled: bool) -> bool:
    try:
        system = platform.system()
        if system == 'Windows':
            set_windows_autostart(enabled)
        elif system == 'Darwin':
            set_macos_autostart(enabled)
        else:
            set_linux_autostart(enabled)
        logger.info(f'Autostart set to {enabled} on {system}')
        return True
    except Exception as exc:
        logger.exception(f'Could not update autostart to {enabled}: {exc}')
        return False


def parse_hotkey(hotkey: str):
    parts = [part.strip() for part in hotkey.split('+') if part.strip()]
    modifiers = set()
    trigger = None
    for part in parts:
        token = part.lower().strip('<>')
        if token in {'ctrl', 'control'}:
            modifiers.add('ctrl')
        elif token == 'shift':
            modifiers.add('shift')
        elif token in {'alt', 'option'}:
            modifiers.add('alt')
        elif token in {'cmd', 'win', 'super'}:
            modifiers.add('cmd')
        else:
            trigger = token
    return modifiers, trigger


def format_hotkey(modifiers, trigger: Optional[str]):
    parts = [f'<{modifier}>' for modifier in HOTKEY_MODIFIER_ORDER if modifier in modifiers]
    if trigger:
        parts.append(trigger.lower())
    return '+'.join(parts)


def format_hotkey_display(modifiers, trigger: Optional[str]):
    parts = []
    for modifier in HOTKEY_MODIFIER_ORDER:
        if modifier in modifiers:
            parts.append(modifier.capitalize())
    if trigger:
        parts.append(trigger.upper() if len(trigger) == 1 else trigger.capitalize())
    return '+'.join(parts)


def normalize_capture_key(event) -> Optional[str]:
    keysym = getattr(event, 'keysym', '')
    if not keysym:
        return None
    return TK_MODIFIER_KEYS.get(keysym.lower())


def normalize_trigger_key(event) -> Optional[str]:
    keysym = getattr(event, 'keysym', '')
    if not keysym:
        return None
    lowered = keysym.lower()
    if lowered in TK_MODIFIER_KEYS:
        return None
    if lowered in {'escape', 'return'}:
        return None
    return lowered


def normalize_pynput_trigger_key(key) -> Optional[str]:
    char = getattr(key, 'char', None)
    if char:
        lowered = char.lower()
        return lowered if lowered in ALLOWED_TRIGGER_KEYS else None
    name = getattr(key, 'name', None)
    if not name:
        vk = getattr(key, 'vk', None)
        if isinstance(vk, int) and 32 <= vk <= 126:
            lowered = chr(vk).lower()
            return lowered if lowered in ALLOWED_TRIGGER_KEYS else None
        return None
    lowered = name.lower()
    if lowered in {
        'ctrl', 'ctrl_l', 'ctrl_r',
        'shift', 'shift_l', 'shift_r',
        'alt', 'alt_l', 'alt_r',
        'cmd', 'cmd_l', 'cmd_r',
        'escape', 'return', 'enter',
    }:
        return None
    return lowered if lowered in ALLOWED_TRIGGER_KEYS else None


def is_configuration_open() -> bool:
    return CONFIG_DIALOG_OPEN.is_set()


def reset_buffer():
    with BUFFER_LOCK:
        BUFFER.clear()


def set_input_suppressed(value: bool):
    global SUPPRESS_INPUT
    SUPPRESS_INPUT = value


def suppress_input_for(seconds: float):
    global SUPPRESS_UNTIL
    SUPPRESS_UNTIL = max(SUPPRESS_UNTIL, time.monotonic() + seconds)


def is_input_suppressed() -> bool:
    return SUPPRESS_INPUT or time.monotonic() < SUPPRESS_UNTIL


def sync_clipboard_text(expected_text: str):
    if pyperclip is None:
        return
    deadline = time.monotonic() + CLIPBOARD_SYNC_TIMEOUT
    while time.monotonic() < deadline:
        try:
            if pyperclip.paste() == expected_text:
                return
        except Exception:
            return
        time.sleep(CLIPBOARD_SYNC_POLL)


def restore_clipboard_baseline():
    if pyperclip is None:
        return
    global CLIPBOARD_BASELINE, CLIPBOARD_RESTORE_TIMER
    with CLIPBOARD_RESTORE_LOCK:
        baseline = CLIPBOARD_BASELINE
        CLIPBOARD_BASELINE = None
        CLIPBOARD_RESTORE_TIMER = None
    if baseline is None:
        return
    try:
        pyperclip.copy(baseline)
    except Exception:
        pass


def schedule_clipboard_restore():
    if pyperclip is None:
        return
    global CLIPBOARD_RESTORE_TIMER
    with CLIPBOARD_RESTORE_LOCK:
        if CLIPBOARD_RESTORE_TIMER is not None:
            try:
                CLIPBOARD_RESTORE_TIMER.cancel()
            except Exception:
                pass
            CLIPBOARD_RESTORE_TIMER = None
        if CLIPBOARD_BASELINE is None:
            return
        timer = threading.Timer(CLIPBOARD_RESTORE_DELAY, restore_clipboard_baseline)
        timer.daemon = True
        CLIPBOARD_RESTORE_TIMER = timer
        timer.start()


def paste_text(text: str):
    if pyperclip is None:
        logger.info('pyperclip not available; falling back to pyautogui.write')
        pyautogui.write(text, interval=0.01)
        return
    global CLIPBOARD_BASELINE
    try:
        previous_clipboard = pyperclip.paste()
    except Exception:
        previous_clipboard = None
    if CLIPBOARD_BASELINE is None and previous_clipboard is not None:
        CLIPBOARD_BASELINE = previous_clipboard
    try:
        pyperclip.copy(text)
        sync_clipboard_text(text)
        pyautogui.hotkey('ctrl', 'v')
    finally:
        schedule_clipboard_restore()


def delete_last_token():
    with BUFFER_LOCK:
        presses = max(1, len(BUFFER))
    pyautogui.press('backspace', presses=presses, interval=0)


def process_buffer():
    global BUFFER
    with BUFFER_LOCK:
        if not BUFFER:
            return
        current = ''.join(BUFFER)
    converted = convert_pinyin_token(current)
    if converted == current:
        logger.info(f"No convertible token found for buffer: {current}")
        return
    logger.info(f"Converting token '{current}' -> '{converted}'")
    try:
        set_input_suppressed(True)
        suppress_input_for(max(0.02, 0.004 * len(current)))
        delete_last_token()
        paste_text(converted)
    finally:
        set_input_suppressed(False)
        suppress_input_for(max(0.03, 0.003 * len(current)))
        reset_buffer()


def handle_alpha_char(char: str):
    with BUFFER_LOCK:
        BUFFER.append(char)
        current = ''.join(BUFFER)
    logger.debug(f"Appended char '{char}' -> buffer: {current}")
    if len(current) >= 2 and current[-1].isdigit() and current[-1] in '12345':
        process_buffer()


def handle_digit_char(char: str):
    with BUFFER_LOCK:
        if BUFFER and BUFFER[-1].isalpha():
            BUFFER.append(char)
            current = ''.join(BUFFER)
        else:
            logger.debug(f"Digit '{char}' not after alpha, resetting buffer")
            BUFFER.clear()
            return
    logger.debug(f"Appended digit '{char}' -> buffer: {current}")
    process_buffer()


def on_type(key):
    if is_input_suppressed() or is_configuration_open():
        return
    if key == keyboard.Key.backspace:
        with BUFFER_LOCK:
            if BUFFER:
                BUFFER.pop()
                logger.debug(f"Buffer after backspace: {''.join(BUFFER)}")
        return
    try:
        char = key.char
    except AttributeError:
        reset_buffer()
        return
    if char is None:
        reset_buffer()
        return
    with ACTIVE_LOCK:
        if not ACTIVE:
            return
    if char.isalpha() and (char.isascii() or char in 'vV'):
        handle_alpha_char(char)
    elif char.isdigit() and char in '12345':
        handle_digit_char(char)
    else:
        logger.debug(f"Resetting buffer on non-token char: {repr(char)}")
        reset_buffer()


class PinyinApp:
    def __init__(self):
        self.config = load_config()
        self.hotkey = self.config.get('hotkey', DEFAULT_HOTKEY)
        self.autostart_enabled = bool(self.config.get('autostart', STARTUP_ENABLED_DEFAULT))
        self.hotkey_modifiers, self.hotkey_trigger = parse_hotkey(self.hotkey)
        self.type_listener: Optional[keyboard.Listener] = None
        self.toggle_listener: Optional[keyboard.Listener] = None
        self.icon: Optional[Any] = None
        self._build_listeners()

    def _build_listeners(self):
        self.type_listener = keyboard.Listener(on_press=on_type)
        self.toggle_listener = keyboard.Listener(on_press=self._toggle_on_press, on_release=self._toggle_on_release)
        logger.info('Keyboard listeners created')

    def start(self):
        if self.autostart_enabled:
            sync_autostart_setting(True)
        if self.type_listener:
            logger.info('Starting typing listener')
            self.type_listener.start()
        if self.toggle_listener:
            logger.info('Starting hotkey listener')
            self.toggle_listener.start()
        threading.Thread(target=self._run_tray, daemon=True).start()

    def stop(self):
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
        self.hotkey_modifiers, self.hotkey_trigger = parse_hotkey(self.hotkey)
        logger.info(f"Hotkey updated to {self.hotkey}")

    def toggle_active(self):
        global ACTIVE
        with ACTIVE_LOCK:
            ACTIVE = not ACTIVE
            print('Modo Pinyin:', 'ACTIVADO' if ACTIVE else 'DESACTIVADO')
        logger.info(f"Toggled ACTIVE -> {ACTIVE}")
        if self.icon:
            self.icon.icon = create_image('green' if ACTIVE else 'red')

    def open_settings(self, *_):
        if CONFIG_DIALOG_OPEN.is_set():
            return
        logger.info('Tray requested settings dialog')
        SETTINGS_REQUESTED.set()

    def _open_settings_dialog(self):
        run_hotkey_settings_dialog(self)

    def _toggle_on_press(self, key):
        if is_configuration_open():
            return
        try:
            trigger = normalize_pynput_trigger_key(key)
            logger.info(f'Hotkey press received: key={key!r}, trigger={trigger!r}, pressed={sorted(PRESSED_KEYS)}')
            if trigger and trigger == self.hotkey_trigger:
                PRESSED_KEYS.add('trigger')
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
                PRESSED_KEYS.add('ctrl')
            if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                PRESSED_KEYS.add('shift')
            if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
                PRESSED_KEYS.add('alt')
            if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                PRESSED_KEYS.add('cmd')
            if self.hotkey_modifiers.issubset(PRESSED_KEYS) and 'trigger' in PRESSED_KEYS:
                logger.info(f'Hotkey matched: modifiers={sorted(self.hotkey_modifiers)}, trigger={self.hotkey_trigger!r}')
                self.toggle_active()
        except Exception as exc:
            logger.info(f"Hotkey press handling error: {exc}")

    def _toggle_on_release(self, key):
        if is_configuration_open():
            return
        try:
            trigger = normalize_pynput_trigger_key(key)
            logger.info(f'Hotkey release received: key={key!r}, trigger={trigger!r}, pressed_before={sorted(PRESSED_KEYS)}')
            if trigger and trigger == self.hotkey_trigger:
                PRESSED_KEYS.discard('trigger')
        except Exception:
            pass
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
            PRESSED_KEYS.discard('ctrl')
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            PRESSED_KEYS.discard('shift')
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            PRESSED_KEYS.discard('alt')
        if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            PRESSED_KEYS.discard('cmd')

    def _run_tray(self):
        image = create_image('green' if ACTIVE else 'red')
        menu = pystray.Menu(
            pystray.MenuItem('Activar/Desactivar', lambda: self.toggle_active()),
            pystray.MenuItem('Configuración', lambda: self.open_settings()),
            pystray.MenuItem('Salir', lambda: quit_app(self)),
        )
        self.icon = pystray.Icon('pinyin', image, 'Pinyin', menu)
        if self.icon:
            self.icon.run()


def create_image(color: str) -> Image.Image:
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    accent = (0, 180, 80, 255) if color == 'green' else (200, 60, 60, 255)
    base = (22, 24, 30, 255)
    draw.ellipse((6, 6, 58, 58), fill=base, outline=accent, width=4)
    try:
        fnt = ImageFont.load_default()
        draw.text((23, 20), 'P', font=fnt, fill=(255, 255, 255, 255))
        draw.line((20, 44, 44, 44), fill=accent, width=4)
    except Exception:
        pass
    return img


def quit_app(app: PinyinApp):
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


class HotkeySettingsDialog:
    def __init__(self, app: PinyinApp):
        self.app = app
        self.root = tk.Tk()
        self.capture_state = {
            'pressed_keys': set(),
            'modifiers': set(),
            'trigger': None,
            'listener': None,
        }
        self.capture_var = tk.StringVar(value=app.hotkey)
        self.status_var = tk.StringVar(value='')
        self.autostart_var = tk.BooleanVar(value=bool(app.config.get('autostart', STARTUP_ENABLED_DEFAULT)))

    def run(self):
        CONFIG_DIALOG_OPEN.set()
        logger.info('Hotkey settings dialog opening')
        try:
            self._build_window()
            self._start_listener()
            self.root.mainloop()
        finally:
            CONFIG_DIALOG_OPEN.clear()
            self._stop_listener()
            logger.info('Hotkey settings dialog closed')

    def _build_window(self):
        self.root.attributes('-topmost', True)
        self.root.title(DIALOG_TITLE)
        self.root.resizable(False, False)
        icon_image = ImageTk.PhotoImage(create_image('green' if ACTIVE else 'red'))
        self.root.tk.call('wm', 'iconphoto', str(self.root), str(icon_image))
        setattr(self.root, '_icon_image', icon_image)

        container = tk.Frame(self.root, padx=16, pady=16)
        container.pack(fill='both', expand=True)

        tk.Label(container, text='Atajo global', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        tk.Label(
            container,
            text='Pulsa la combinacion directamente. Esc cierra la ventana.',
            anchor='w',
            justify='left',
        ).pack(anchor='w', pady=(4, 10))

        tk.Label(
            container,
            text='Recomendado: Ctrl+Alt+<letra>. Evita atajos reservados por Windows u otras apps.',
            anchor='w',
            justify='left',
            fg='#666666',
        ).pack(anchor='w', pady=(0, 10))

        tk.Checkbutton(
            container,
            text='Iniciar con el sistema operativo',
            variable=self.autostart_var,
            anchor='w',
            justify='left',
        ).pack(anchor='w', pady=(0, 10))

        entry = tk.Entry(container, textvariable=self.capture_var, width=34, justify='center', state='readonly')
        entry.pack(fill='x')
        entry.focus_set()

        tk.Label(container, textvariable=self.status_var, fg='#666666').pack(anchor='w', pady=(6, 0))

        button_row = tk.Frame(container)
        button_row.pack(fill='x', pady=(16, 0))
        save_button = tk.Button(button_row, text='Guardar', command=self.save, width=10)
        cancel_button = tk.Button(button_row, text='Cancelar', command=self.cancel, width=10)
        cancel_button.pack(side='right')
        save_button.pack(side='right', padx=(0, 8))

        self.capture_state['modifiers'], self.capture_state['trigger'] = parse_hotkey(self.app.hotkey)
        self.refresh_preview()
        self.root.protocol('WM_DELETE_WINDOW', self.cancel)

    def _start_listener(self):
        self.capture_state['listener'] = keyboard.Listener(
            on_press=self.on_capture_press,
            on_release=self.on_capture_release,
            suppress=True,
        )
        self.capture_state['listener'].start()
        logger.info('Hotkey capture listener started with suppress=True')

    def _stop_listener(self):
        listener = self.capture_state.get('listener')
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass

    def _schedule_ui(self, callback):
        try:
            self.root.after(0, callback)
        except Exception:
            callback()

    def refresh_preview(self):
        preview = format_hotkey_display(self.capture_state['modifiers'], self.capture_state['trigger'])
        if preview:
            self.capture_var.set(preview)
            self.status_var.set('')
        else:
            self.capture_var.set('Pulsa la combinacion deseada')
            self.status_var.set('')

    def begin_capture(self):
        self.capture_state['modifiers'].clear()
        self.capture_state['trigger'] = None

    def _capture_started(self) -> bool:
        return bool(self.capture_state['pressed_keys'])

    def _capture_key_identity(self, key) -> str:
        char = getattr(key, 'char', None)
        if char:
            return f'char:{char.lower()}'
        name = getattr(key, 'name', None)
        if name:
            return f'name:{name.lower()}'
        vk = getattr(key, 'vk', None)
        if vk is not None:
            return f'vk:{vk}'
        return repr(key)

    def _record_press(self, key):
        if not self._capture_started():
            self.begin_capture()

        self.capture_state['pressed_keys'].add(self._capture_key_identity(key))

        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
            self.capture_state['modifiers'].add('ctrl')
            return
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self.capture_state['modifiers'].add('shift')
            return
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.capture_state['modifiers'].add('alt')
            return
        if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            self.capture_state['modifiers'].add('cmd')
            return

        trigger = normalize_pynput_trigger_key(key)
        if trigger:
            self.capture_state['trigger'] = trigger

    def close(self):
        self._stop_listener()
        try:
            self.root.destroy()
        except Exception:
            pass

    def request_close(self):
        self._schedule_ui(self.close)

    def save(self):
        new = format_hotkey(self.capture_state['modifiers'], self.capture_state['trigger']).strip()
        if not new or not self.capture_state['trigger']:
            messagebox.showerror('Error', 'El hotkey debe incluir una tecla principal, por ejemplo p')
            return
        logger.info(f'Hotkey dialog saving new hotkey={new!r}')
        self.app.config['hotkey'] = new
        save_config(self.app.config)
        self.app.hotkey = new
        self.app.refresh_hotkey()
        desired_autostart = bool(self.autostart_var.get())
        if desired_autostart != self.app.autostart_enabled:
            if sync_autostart_setting(desired_autostart):
                self.app.autostart_enabled = desired_autostart
                self.app.config['autostart'] = desired_autostart
                save_config(self.app.config)
            else:
                messagebox.showwarning(
                    'Inicio automático',
                    'No se pudo actualizar el inicio automático. El atajo se guardó, pero el sistema no pudo aplicar el cambio.',
                )
        self.request_close()

    def cancel(self):
        self.request_close()

    def on_capture_press(self, key):
        logger.info(f'Capture press received: key={key!r}')
        if key == keyboard.Key.esc:
            self.cancel()
            return False
        if key == keyboard.Key.enter:
            self.save()
            return False
        self._record_press(key)
        self._schedule_ui(self.refresh_preview)
        return True

    def on_capture_release(self, key):
        self.capture_state['pressed_keys'].discard(self._capture_key_identity(key))
        return True


def run_hotkey_settings_dialog(app: PinyinApp):
    HotkeySettingsDialog(app).run()


def main():
    print('App de Pinyin en vivo')
    print('Usa el icono en la bandeja para ver el estado y modificar atajo')
    app = PinyinApp()
    logger.info(f"App starting with hotkey={app.hotkey!r}, modifiers={sorted(app.hotkey_modifiers)}, trigger={app.hotkey_trigger!r}")
    app.start()
    try:
        while not STOP_REQUESTED.is_set():
            if SETTINGS_REQUESTED.is_set() and not CONFIG_DIALOG_OPEN.is_set():
                SETTINGS_REQUESTED.clear()
                logger.info('Settings requested from tray; opening dialog on main thread')
                run_hotkey_settings_dialog(app)
                continue
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('\nSaliendo...')
        app.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
