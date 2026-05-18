#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación principal: escucha global de teclado, buffer y conversión en tiempo real.
Toggle: Ctrl+Shift+P
"""

import sys
import time
import json
import threading
import os
import logging
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
    from pinyin_converter import convert_pinyin_token, has_vowel
except ImportError:
    from .pinyin_converter import convert_pinyin_token, has_vowel


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
logger.addHandler(fh)

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False


# Estado global
ACTIVE = False
BUFFER = []
BUFFER_LOCK = threading.Lock()
ACTIVE_LOCK = threading.Lock()
PRESSED_KEYS = set()
DEFAULT_HOTKEY = '<ctrl>+<shift>+p'
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
    default = {'hotkey': '<ctrl>+<shift>+p'}
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
    except Exception as e:
        print('Error saving config:', e)


def parse_hotkey(hotkey: str):
    parts = [part.strip() for part in hotkey.split('+') if part.strip()]
    modifiers = set()
    trigger = None
    for part in parts:
        token = part.lower().strip('<>')
        if token in {'ctrl', 'control'}:
            modifiers.add('ctrl')
        elif token in {'shift'}:
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


def normalize_capture_key(event) -> Optional[str]:
    keysym = getattr(event, 'keysym', '')
    if not keysym:
        return None
    return TK_MODIFIER_KEYS.get(keysym.lower())


def normalize_trigger_key(event) -> Optional[str]:
    char = getattr(event, 'char', None)
    if not char or len(char) != 1:
        return None
    if not char.isascii() or not char.isalnum():
        return None
    return char.lower()


def reset_buffer():
    global BUFFER
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


def restore_clipboard_later(previous_clipboard: str):
    if pyperclip is None:
        return
    time.sleep(CLIPBOARD_RESTORE_DELAY)
    try:
        pyperclip.copy(previous_clipboard)
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


def delete_last_token():
    with BUFFER_LOCK:
        presses = max(1, len(BUFFER))
    pyautogui.press('backspace', presses=presses, interval=0)


def process_buffer():
    """Convierte el buffer completo si termina en un patrón convertible."""
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
    # Listener para pulsaciones normales (captura global)
    if is_input_suppressed():
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
        # Tecla especial -> reset buffer
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
        self.hotkey_modifiers, self.hotkey_trigger = parse_hotkey(self.hotkey)
        self.type_listener: Optional[keyboard.Listener] = None
        self.toggle_listener: Optional[keyboard.Listener] = None
        self.icon: Optional[Any] = None
        self._build_listeners()

    def _build_listeners(self):
        # Typing listener
        self.type_listener = keyboard.Listener(on_press=on_type)
        # Toggle listener: track modifiers and 'p' to toggle
        self.toggle_listener = keyboard.Listener(on_press=self._toggle_on_press, on_release=self._toggle_on_release)

    def start(self):
        # Start listeners
        if self.type_listener:
            self.type_listener.start()
        if self.toggle_listener:
            self.toggle_listener.start()
        # Start tray icon in thread
        t = threading.Thread(target=self._run_tray, daemon=True)
        t.start()

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
            status = 'ACTIVADO' if ACTIVE else 'DESACTIVADO'
            print('Modo Pinyin:', status)
        logger.info(f"Toggled ACTIVE -> {ACTIVE}")
        # Update tray icon
        if self.icon:
            self.icon.icon = create_image('green' if ACTIVE else 'red')

    def open_settings(self, *_):
        threading.Thread(target=self._open_settings_dialog, daemon=True).start()

    def _open_settings_dialog(self):
        capture_state = {
            'modifiers': set(),
            'trigger': None,
            'listening': False,
        }

        def refresh_preview():
            preview = format_hotkey(capture_state['modifiers'], capture_state['trigger'])
            if preview:
                capture_var.set(preview)
                status_var.set('')
            else:
                capture_var.set('Pulsa la combinacion deseada')
                status_var.set('')

        def begin_capture():
            if not capture_state['listening']:
                capture_state['modifiers'].clear()
                capture_state['trigger'] = None
                capture_state['listening'] = True

        def save():
            new = format_hotkey(capture_state['modifiers'], capture_state['trigger']).strip()
            if not new or not capture_state['trigger']:
                messagebox.showerror('Error', 'El hotkey debe incluir una tecla principal, por ejemplo p')
                return
            self.config['hotkey'] = new
            save_config(self.config)
            self.hotkey = new
            self.refresh_hotkey()
            root.destroy()

        def cancel():
            root.destroy()

        def on_key_press(event):
            if getattr(event, 'keysym', '').lower() == 'escape':
                cancel()
                return 'break'

            modifier = normalize_capture_key(event)
            if modifier:
                begin_capture()
                capture_state['modifiers'].add(modifier)
                capture_state['trigger'] = None
                refresh_preview()
                return 'break'

            trigger = normalize_trigger_key(event)
            if trigger:
                begin_capture()
                capture_state['trigger'] = trigger
                refresh_preview()
                return 'break'

            status_var.set('Usa una letra o numero como tecla principal.')
            return None

        root = tk.Tk()
        root.attributes('-topmost', True)
        root.title('Configuración')
        root.resizable(False, False)

        icon_image = ImageTk.PhotoImage(create_image('green' if ACTIVE else 'red'))
        root.tk.call('wm', 'iconphoto', str(root), str(icon_image))
        setattr(root, '_icon_image', icon_image)

        container = tk.Frame(root, padx=16, pady=16)
        container.pack(fill='both', expand=True)

        tk.Label(container, text='Atajo global', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        tk.Label(
            container,
            text='Pulsa la combinacion directamente. Esc cierra la ventana.',
            anchor='w',
            justify='left',
        ).pack(anchor='w', pady=(4, 10))

        capture_var = tk.StringVar(value=self.hotkey)
        status_var = tk.StringVar(value='')
        entry = tk.Entry(container, textvariable=capture_var, width=34, justify='center', state='readonly')
        entry.pack(fill='x')
        entry.focus_set()

        tk.Label(container, textvariable=status_var, fg='#666666').pack(anchor='w', pady=(6, 0))

        button_row = tk.Frame(container)
        button_row.pack(fill='x', pady=(16, 0))
        save_button = tk.Button(button_row, text='Guardar', command=save, width=10)
        cancel_button = tk.Button(button_row, text='Cancelar', command=cancel, width=10)
        cancel_button.pack(side='right')
        save_button.pack(side='right', padx=(0, 8))

        capture_state['modifiers'], capture_state['trigger'] = parse_hotkey(self.hotkey)
        refresh_preview()

        root.bind('<KeyPress>', on_key_press)
        root.bind('<Escape>', lambda _event: cancel())
        root.bind('<Return>', lambda _event: save())
        root.mainloop()

    def _toggle_on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                char = key.char.lower()
                if char == self.hotkey_trigger:
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
                self.toggle_active()
        except Exception as exc:
            logger.info(f"Hotkey press handling error: {exc}")

    def _toggle_on_release(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                if key.char.lower() == self.hotkey_trigger:
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
        # Create icon and menu
        image = create_image('green' if ACTIVE else 'red')
        menu = pystray.Menu(
            pystray.MenuItem('Toggle', lambda: self.toggle_active()),
            pystray.MenuItem('Settings', lambda: self.open_settings()),
            pystray.MenuItem('Quit', lambda: quit_app(self))
        )
        self.icon = pystray.Icon('pinyin', image, 'Pinyin', menu)
        if self.icon:
            self.icon.run()


def create_image(color: str) -> Image.Image:
    # Simple 64x64 app badge with a P monogram for tray and window icons.
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
    # Stop the tray icon loop without raising SystemExit inside callback
    try:
        if app.icon:
            app.icon.stop()
    except Exception:
        pass


def main():
    print('App de Pinyin en vivo')
    print("Usa el icono en la bandeja para ver el estado y modificar atajo")
    app = PinyinApp()
    app.start()
    try:
        while not STOP_REQUESTED.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('\nSaliendo...')
        app.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
