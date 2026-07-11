# -*- coding: utf-8 -*-
"""
config.py — persistent settings for Archisight.

Настройки хранятся в JSON-файле в стандартной пользовательской папке:
  Windows: %APPDATA%\\Archisight\\config.json
  (на других ОС — в домашней папке пользователя, для разработки/тестов)

Настройки применяются только после явного нажатия "Сохранить" в окне
настроек — до этого момента изменения в диалоге хранятся исключительно
в памяти (см. gui/settings_window.py).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

from .core import (
    DEFAULT_RETENTION_DAYS,
    DateFormatSettings,
)
from .i18n import detect_system_language

APP_DIR_NAME = "Archisight"
CONFIG_FILE_NAME = "config.json"


def get_app_data_dir() -> str:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        # Не-Windows окружение используется только для разработки и тестов.
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    path = os.path.join(base, APP_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path() -> str:
    return os.path.join(get_app_data_dir(), CONFIG_FILE_NAME)


def get_lock_path() -> str:
    return os.path.join(get_app_data_dir(), "archisight.lock")


@dataclass
class AppConfig:
    language: str = "auto"          # "auto" | "en" | "ru"
    retention_days: int = DEFAULT_RETENTION_DAYS
    archive_path: Optional[str] = None
    run_time: Optional[str] = None  # "HH:MM" 24-часовой формат, либо None
    date_order: str = "DMY"
    date_separator: str = "."
    date_year_format: str = "short"
    autostart_enabled: bool = False
    last_check: Optional[str] = None      # ISO datetime строки последней проверки
    last_run_date: Optional[str] = None   # ISO дата последнего АВТОМАТИЧЕСКОГО запуска (защита от повторного запуска в тот же день)

    def date_format(self) -> DateFormatSettings:
        return DateFormatSettings(
            order=self.date_order,
            separator=self.date_separator,
            year_format=self.date_year_format,
        )

    def effective_language(self) -> str:
        if self.language in ("en", "ru"):
            return self.language
        return detect_system_language()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        defaults = cls()
        merged = defaults.to_dict()
        if isinstance(data, dict):
            for key in merged:
                if key in data:
                    merged[key] = data[key]
        return cls(**merged)

    @classmethod
    def defaults(cls) -> "AppConfig":
        return cls()


def load_config() -> AppConfig:
    path = get_config_path()
    if not os.path.isfile(path):
        return AppConfig.defaults()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppConfig.from_dict(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        # Повреждённый файл настроек не должен ронять приложение —
        # откатываемся на настройки по умолчанию.
        return AppConfig.defaults()


def save_config(config: AppConfig) -> None:
    path = get_config_path()
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)  # атомарная замена — не оставит битый файл при сбое записи
