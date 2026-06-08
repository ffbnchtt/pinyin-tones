"""Simple Tk dialog for update notifications."""

from __future__ import annotations

import logging
import platform
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from PIL import ImageTk

from pinyin_tones.tray_ui import create_tray_image
from pinyin_tones.update_check import ReleaseInfo


class UpdateAvailableDialog:
    """Popup dialog that offers update actions to the user."""

    def __init__(
        self,
        app: Any,
        current_version: str,
        release: ReleaseInfo,
        logger,
        on_download: Callable[[], bool],
        on_remind_later: Callable[[], None],
    ) -> None:
        self.app = app
        self.current_version = current_version
        self.release = release
        self.logger = logger or logging.getLogger("pinyin_tones")
        self.on_download = on_download
        self.on_remind_later = on_remind_later
        self.root = tk.Tk()

    def run(self) -> None:
        self._build_window()
        self.root.mainloop()

    def _build_window(self) -> None:
        self.root.attributes("-topmost", True)
        self.root.title("Actualización disponible")
        self.root.resizable(False, False)
        self.root.geometry("420x220")
        active_state = True
        if hasattr(self.app, "is_active"):
            try:
                active_state = bool(self.app.is_active())
            except Exception:
                active_state = True
        icon_image = ImageTk.PhotoImage(
            create_tray_image(active_state, show_status=False, with_background=True)
        )
        self.root.tk.call("wm", "iconphoto", str(self.root), str(icon_image))
        setattr(self.root, "_icon_image", icon_image)

        style = ttk.Style(self.root)
        available_themes = set(style.theme_names())
        if platform.system() == "Windows" and "vista" in available_themes:
            style.theme_use("vista")
        elif "aqua" in available_themes:
            style.theme_use("aqua")
        elif "clam" in available_themes:
            style.theme_use("clam")

        container = ttk.Frame(self.root, padding=(14, 14))
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(
            container,
            text="Hay una nueva versión disponible.",
            font=("", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            container,
            text=f"Versión actual: v{self.current_version}",
        ).grid(row=1, column=0, sticky="w", pady=(10, 2))
        ttk.Label(
            container,
            text=f"Nueva versión: v{self.release.version}",
        ).grid(row=2, column=0, sticky="w", pady=(0, 10))

        if self.release.asset_name:
            asset_text = f"Descarga disponible para este sistema: {self.release.asset_name}"
        else:
            asset_text = "No hay un archivo específico para este sistema en la release."
        ttk.Label(
            container,
            text=asset_text,
            wraplength=380,
        ).grid(row=3, column=0, sticky="w", pady=(0, 12))

        button_row = ttk.Frame(container)
        button_row.grid(row=4, column=0, sticky="e")

        download_button = ttk.Button(
            button_row,
            text="Descargar",
            command=self._download,
            state="normal" if self.release.asset_name else "disabled",
        )
        later_button = ttk.Button(button_row, text="Recordarme después", command=self._remind_later)

        download_button.grid(row=0, column=0)
        later_button.grid(row=0, column=1, padx=(6, 0))

        self.root.protocol("WM_DELETE_WINDOW", self._remind_later)

    def _close(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass

    def _download(self) -> None:
        should_close = self.on_download()
        if should_close:
            self._close()

    def _remind_later(self) -> None:
        self.on_remind_later()
        self._close()


def run_update_dialog(
    app: Any,
    current_version: str,
    release: ReleaseInfo,
    logger,
    on_download: Callable[[], bool],
    on_remind_later: Callable[[], None],
) -> None:
    """Open the update-available dialog."""
    UpdateAvailableDialog(
        app,
        current_version,
        release,
        logger,
        on_download,
        on_remind_later,
    ).run()
