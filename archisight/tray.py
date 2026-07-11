# -*- coding: utf-8 -*-
"""
tray.py — значок в системном трее Windows.

Показывается, когда приложение свёрнуто (окно закрыто крестиком при
включённом автозапуске). При наведении курсора показывает дату и время
последней проверки архива. Правый клик открывает меню с теми же
пунктами, что и верхнее меню главного окна.

Если библиотека pystray недоступна (например, не установлена), трей
просто не запускается — приложение продолжает работать в обычном окне,
без сбоев (см. main.py: закрытие в таком случае эквивалентно выходу).
"""

from __future__ import annotations

import threading

from . import resources

try:
    import pystray
    from PIL import Image

    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False


class TrayController:
    def __init__(self, app):
        self.app = app
        self._icon = None
        self._thread = None

    @property
    def is_available(self) -> bool:
        return PYSTRAY_AVAILABLE

    def _build_menu(self):
        t = self.app.tr.t
        return pystray.Menu(
            pystray.MenuItem(t("tray_open"), self._on_open, default=True),
            pystray.MenuItem(t("tray_settings"), self._on_settings),
            pystray.MenuItem(t("tray_info"), self._on_info),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(t("tray_exit"), self._on_exit),
        )

    def start(self):
        if not PYSTRAY_AVAILABLE:
            return
        if self._thread and self._thread.is_alive():
            self.update_tooltip()
            return

        image = Image.open(resources.get_asset_path("icon.png")).convert("RGBA")
        self._icon = pystray.Icon("Archisight", image, self._tooltip_text(), self._build_menu())
        self._thread = threading.Thread(target=self._icon.run, name="ArchisightTray", daemon=True)
        self._thread.start()

    def stop(self):
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def update_tooltip(self):
        if self._icon is not None:
            try:
                self._icon.title = self._tooltip_text()
                self._icon.menu = self._build_menu()
            except Exception:
                pass

    def _tooltip_text(self) -> str:
        t = self.app.tr.t
        cfg = self.app.config
        if not cfg.last_check:
            return t("tray_tooltip_never")
        from datetime import datetime

        from . import i18n

        try:
            dt = datetime.fromisoformat(cfg.last_check)
            when = i18n.format_datetime_short(dt, self.app.tr.language)
        except ValueError:
            when = "\u2014"
        return t("tray_tooltip_last", when=when)

    # -------- callbacks (выполняются в потоке pystray -> прокидываем в Tk)

    def _on_open(self, icon=None, item=None):
        self.app.root.after(0, self.app.restore_from_tray)

    def _on_settings(self, icon=None, item=None):
        self.app.root.after(0, self.app.open_settings_from_tray)

    def _on_info(self, icon=None, item=None):
        self.app.root.after(0, self.app.open_about_from_tray)

    def _on_exit(self, icon=None, item=None):
        self.app.root.after(0, self.app.quit_application)
