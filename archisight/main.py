# -*- coding: utf-8 -*-
"""
main.py — точка входа Archisight.

Здесь же живёт класс App — контроллер, который связывает воедино:
  - конфигурацию (config.py)
  - локализацию (i18n.py)
  - логику сканирования/удаления (core.py)
  - фоновый планировщик (scheduler.py)
  - автозапуск через реестр (autostart.py)
  - системный трей (tray.py)
  - окна интерфейса (gui/*)

Запуск:  python -m archisight.main [--minimized]
  --minimized  — запуститься сразу свёрнутым в трей (используется
                 автозапуском Windows, чтобы не показывать окно при
                 каждой загрузке системы).
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from . import autostart
from . import config as config_module
from . import core
from . import resources
from . import tray as tray_module
from .gui import style as S
from .gui.about_window import AboutWindow
from .gui.main_window import MainWindow
from .gui.settings_window import SettingsWindow
from .i18n import Translator
from .scheduler import Scheduler

SINGLE_INSTANCE_MUTEX_NAME = "Archisight_SingleInstance_Mutex_9F21C4"
_mutex_handle = None  # держим ссылку, чтобы мьютекс не освободился раньше времени


def acquire_single_instance_lock() -> bool:
    """Возвращает False, если приложение уже запущено (другой процесс)."""
    global _mutex_handle
    if not sys.platform.startswith("win"):
        return True  # вне Windows (только для разработки/тестов) — не блокируем

    kernel32 = ctypes.windll.kernel32
    _mutex_handle = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX_NAME)
    ERROR_ALREADY_EXISTS = 183
    if ctypes.GetLastError() == ERROR_ALREADY_EXISTS:
        return False
    return True


class App:
    PERIODIC_REFRESH_MS = 60_000

    def __init__(self, start_minimized: bool = False):
        self.config = config_module.load_config()
        self.tr = Translator(self.config.effective_language())

        self.root = tk.Tk()
        self.root.title(self.tr.t("app_title"))
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        self.root.maxsize(800, 600)
        self.root.resizable(False, False)

        self._set_window_icon()
        S.apply_style(self.root)

        self._build_menu()
        self.main_window = MainWindow(self.root, self)
        self.main_window.pack(fill="both", expand=True)

        self.tray = tray_module.TrayController(self)
        self.scheduler = Scheduler(get_config=lambda: self.config, run_cleanup_callback=self._scheduled_run)
        self.scheduler.start()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close_button)

        if start_minimized and self.tray.is_available:
            self.root.withdraw()
            self.tray.start()

        self._schedule_periodic_refresh()

    # -------------------------------------------------------------- window

    def _set_window_icon(self):
        try:
            ico_path = resources.get_asset_path("icon.ico")
            if os.path.isfile(ico_path):
                self.root.iconbitmap(ico_path)
                return
        except Exception:
            pass
        try:
            png_path = resources.get_asset_path("icon.png")
            if os.path.isfile(png_path):
                img = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, img)
                self._icon_photo_ref = img  # предотвращаем сборку мусора
        except Exception:
            pass

    def _build_menu(self):
        menubar = tk.Menu(self.root, tearoff=False)
        menubar.add_command(label=self.tr.t("menu_settings"), command=self.open_settings_window)
        menubar.add_command(label=self.tr.t("menu_info"), command=self.open_about_window)
        self.root.config(menu=menubar)
        self._menubar = menubar

    def _rebuild_menu_texts(self):
        self._menubar.entryconfigure(0, label=self.tr.t("menu_settings"))
        self._menubar.entryconfigure(1, label=self.tr.t("menu_info"))
        self.root.title(self.tr.t("app_title"))

    # --------------------------------------------------------- data / core

    def compute_preview(self) -> core.CleanupReport:
        """Только просмотр — НИКОГДА не удаляет файлы. Используется главным окном."""
        return core.perform_cleanup(
            self.config.archive_path,
            self.config.date_format(),
            self.config.retention_days,
            dry_run=True,
        )

    def is_autostart_active(self) -> bool:
        return autostart.is_autostart_registered()

    # -------------------------------------------------------------- actions

    def open_archive_folder(self):
        path = self.config.archive_path
        if not path or not os.path.isdir(path):
            messagebox.showerror(self.tr.t("error_title"), self.tr.t("error_path_missing"), parent=self.root)
            return
        try:
            os.startfile(path)  # type: ignore[attr-defined]  # доступно только на Windows
        except AttributeError:
            pass  # не-Windows окружение (разработка) — не является ошибкой
        except OSError:
            messagebox.showerror(self.tr.t("error_title"), self.tr.t("error_path_missing"), parent=self.root)

    def open_settings_window(self):
        SettingsWindow(self.root, self)

    def open_about_window(self):
        AboutWindow(self.root, self)

    def apply_new_config(self, new_config: config_module.AppConfig):
        self.config = new_config
        config_module.save_config(self.config)
        self.tr.set_language(self.config.effective_language())
        self._rebuild_menu_texts()
        self.refresh_main_window()
        self.tray.update_tooltip()

    def refresh_main_window(self):
        self.main_window.refresh()

    def record_manual_check_timestamp(self):
        self.config.last_check = datetime.now().isoformat(timespec="seconds")
        config_module.save_config(self.config)
        self.tray.update_tooltip()

    # ------------------------------------------------------- scheduled run

    def _scheduled_run(self):
        """Вызывается из фонового потока планировщика (см. scheduler.py).
        Файловые операции безопасно выполнять вне основного потока — это
        не Tk-вызовы. А вот обновление config/GUI переносим в основной поток."""
        report = core.perform_cleanup(
            self.config.archive_path,
            self.config.date_format(),
            self.config.retention_days,
            dry_run=False,
        )
        now_iso = datetime.now().isoformat(timespec="seconds")
        today_iso = datetime.now().date().isoformat()

        def _apply_on_main_thread():
            self.config.last_check = now_iso
            self.config.last_run_date = today_iso
            config_module.save_config(self.config)
            self.refresh_main_window()
            self.tray.update_tooltip()

        try:
            self.root.after(0, _apply_on_main_thread)
        except RuntimeError:
            pass  # окно уже уничтожено (приложение завершается)

    # ------------------------------------------------------------ tray/exit

    def _on_close_button(self):
        if self.config.autostart_enabled and self.tray.is_available:
            self.minimize_to_tray()
        else:
            self.quit_application()

    def minimize_to_tray(self):
        self.tray.start()
        self.root.withdraw()

    def restore_from_tray(self):
        self.tray.stop()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.refresh_main_window()

    def open_settings_from_tray(self):
        self.restore_from_tray()
        self.open_settings_window()

    def open_about_from_tray(self):
        self.restore_from_tray()
        self.open_about_window()

    def quit_application(self):
        self.scheduler.stop()
        self.tray.stop()
        self.root.destroy()

    # ------------------------------------------------------------ periodic

    def _schedule_periodic_refresh(self):
        def _tick():
            try:
                if self.root.state() != "withdrawn":
                    self.refresh_main_window()
            except tk.TclError:
                pass
            self.root.after(self.PERIODIC_REFRESH_MS, _tick)

        self.root.after(self.PERIODIC_REFRESH_MS, _tick)


def parse_args():
    parser = argparse.ArgumentParser(description="Archisight")
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="Запустить свёрнутым в трей (используется автозапуском Windows)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not acquire_single_instance_lock():
        # Archisight уже запущен — тихо завершаемся, чтобы не плодить окна/иконки в трее.
        return

    app = App(start_minimized=args.minimized)
    app.root.mainloop()


if __name__ == "__main__":
    main()
