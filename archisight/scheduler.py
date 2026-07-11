# -*- coding: utf-8 -*-
"""
scheduler.py — фоновый поток, который раз в сутки в заданное пользователем
время запускает реальную проверку/очистку архива.

Условие срабатывания (строго по ТЗ):
  автозапуск включён  И  время в настройках задано  И  сегодня ещё не
  выполнялся автоматический запуск.

Если хотя бы одно условие не выполняется — поток ничего не делает,
но продолжает тихо ждать (настройки могут поменяться в любой момент,
пока приложение открыто).
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Callable


class Scheduler:
    def __init__(self, get_config: Callable, run_cleanup_callback: Callable, check_interval: int = 20):
        """
        get_config: функция без аргументов, возвращающая актуальный AppConfig.
        run_cleanup_callback: функция без аргументов, выполняющая реальный
            запуск очистки И обновляющая config.last_run_date / last_check.
        """
        self.get_config = get_config
        self.run_cleanup_callback = run_cleanup_callback
        self.check_interval = check_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="ArchisightScheduler", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception:
                # Планировщик не должен падать целиком из-за единичной ошибки —
                # просто пропускаем этот тик и пробуем в следующий раз.
                pass
            self._stop_event.wait(self.check_interval)

    def _tick(self):
        config = self.get_config()

        if not config.autostart_enabled:
            return
        if not config.run_time:
            return

        now = datetime.now()
        today_iso = now.date().isoformat()

        if config.last_run_date == today_iso:
            return  # сегодня уже выполняли

        if now.strftime("%H:%M") == config.run_time:
            self.run_cleanup_callback()
