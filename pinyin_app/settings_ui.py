"""Settings dialog for hotkey configuration."""

from __future__ import annotations

from typing import Any, Optional
import logging

from pynput import keyboard
from PIL import ImageTk
import tkinter as tk
from tkinter import messagebox

from pinyin_app.hotkeys import (
    format_hotkey,
    format_hotkey_display,
    normalize_pynput_trigger_key,
    parse_hotkey,
)
from pinyin_app.tray_ui import create_tray_image


class HotkeySettingsDialog:
    """Tk dialog to capture hotkey and update settings."""

    def __init__(
        self,
        app: Any,
        dialog_title: str,
        logger,
        sync_autostart,
        save_config,
        startup_enabled_default: bool,
    ) -> None:
        self.app = app
        self.dialog_title = dialog_title
        self.logger = logger or logging.getLogger('pinyin_app')
        self.sync_autostart = sync_autostart
        self.save_config = save_config
        self.startup_enabled_default = startup_enabled_default
        self.root = tk.Tk()
        self.capture_state = {
            'pressed_keys': set(),
            'modifiers': set(),
            'trigger': None,
            'listener': None,
        }
        self.capture_var = tk.StringVar(value=app.hotkey)
        self.status_var = tk.StringVar(value='')
        self.autostart_var = tk.BooleanVar(value=bool(app.config.get('autostart', startup_enabled_default)))

    def run(self) -> None:
        """Open the dialog and block until closed."""
        getattr(self, 'logger', logging.getLogger('pinyin_app')).info('Hotkey settings dialog opening')
        try:
            self._build_window()
            self._start_listener()
            self.root.mainloop()
        finally:
            self._stop_listener()
            getattr(self, 'logger', logging.getLogger('pinyin_app')).info('Hotkey settings dialog closed')

    def _build_window(self) -> None:
        self.root.attributes('-topmost', True)
        self.root.title(self.dialog_title)
        self.root.resizable(False, False)
        icon_image = ImageTk.PhotoImage(create_tray_image(True))
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

    def _start_listener(self) -> None:
        self.capture_state['listener'] = keyboard.Listener(
            on_press=self.on_capture_press,
            on_release=self.on_capture_release,
            suppress=True,
        )
        self.capture_state['listener'].start()
        getattr(self, 'logger', logging.getLogger('pinyin_app')).info('Hotkey capture listener started with suppress=True')

    def _stop_listener(self) -> None:
        listener = self.capture_state.get('listener')
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass

    def _schedule_ui(self, callback) -> None:
        try:
            self.root.after(0, callback)
        except Exception:
            callback()

    def refresh_preview(self) -> None:
        """Update the hotkey preview label."""
        preview = format_hotkey_display(self.capture_state['modifiers'], self.capture_state['trigger'])
        if preview:
            self.capture_var.set(preview)
            self.status_var.set('')
        else:
            self.capture_var.set('Pulsa la combinacion deseada')
            self.status_var.set('')

    def begin_capture(self) -> None:
        """Reset capture state before starting a chord."""
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

    def _record_press(self, key) -> None:
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

    def close(self) -> None:
        """Destroy the dialog window."""
        self._stop_listener()
        try:
            self.root.destroy()
        except Exception:
            pass

    def request_close(self) -> None:
        """Schedule dialog close on the UI thread."""
        self._schedule_ui(self.close)

    def save(self) -> None:
        """Persist the new hotkey and autostart values."""
        new = format_hotkey(self.capture_state['modifiers'], self.capture_state['trigger']).strip()
        if not new or not self.capture_state['trigger']:
            messagebox.showerror('Error', 'El hotkey debe incluir una tecla principal, por ejemplo p')
            return
        getattr(self, 'logger', logging.getLogger('pinyin_app')).info(f'Hotkey dialog saving new hotkey={new!r}')
        self.app.config['hotkey'] = new
        self.save_config(self.app.config)
        self.app.hotkey = new
        self.app.refresh_hotkey()
        desired_autostart = bool(self.autostart_var.get())
        if desired_autostart != self.app.autostart_enabled:
            if self.sync_autostart(desired_autostart):
                self.app.autostart_enabled = desired_autostart
                self.app.config['autostart'] = desired_autostart
                self.save_config(self.app.config)
            else:
                messagebox.showwarning(
                    'Inicio automático',
                    'No se pudo actualizar el inicio automático. El atajo se guardó, pero el sistema no pudo aplicar el cambio.',
                )
        self.request_close()

    def cancel(self) -> None:
        """Close without saving."""
        self.request_close()

    def on_capture_press(self, key):
        """Handle a key press during capture."""
        getattr(self, 'logger', logging.getLogger('pinyin_app')).info(f'Capture press received: key={key!r}')
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
        """Handle a key release during capture."""
        self.capture_state['pressed_keys'].discard(self._capture_key_identity(key))
        return True


def run_hotkey_settings_dialog(app: Any, dialog_title: str, logger, sync_autostart, save_config, startup_enabled_default: bool) -> None:
    """Open the settings dialog for the provided app instance."""
    HotkeySettingsDialog(
        app,
        dialog_title,
        logger,
        sync_autostart,
        save_config,
        startup_enabled_default,
    ).run()
