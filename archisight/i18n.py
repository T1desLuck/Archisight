# -*- coding: utf-8 -*-
"""
i18n.py — локализация Archisight (EN / RU).

Правило выбора языка по умолчанию:
  - Если пользователь ещё НИ РАЗУ не менял язык вручную (config.language == "auto"),
    язык определяется системной локалью: русская система -> RU, любая другая -> EN.
  - Как только пользователь сам выбрал язык в настройках и нажал "Сохранить",
    он фиксируется в config.language ("en"/"ru") и больше не зависит от системы.
"""

from __future__ import annotations

import locale
import os
import sys

SUPPORTED_LANGUAGES = ("en", "ru")
DEFAULT_LANGUAGE = "en"

TRANSLATIONS = {
    "en": {
        # --- Main window ---
        "app_title": "Archisight",
        "main_current_date": "Current date:",
        "main_folders_found": "Folders found:",
        "main_retention_days": "Keeping (days):",
        "main_archive_path": "Archive path:",
        "main_no_path_set": "No path set — open Settings to choose one",
        "main_open_archive": "Open archive",
        "main_status": "Status:",
        "main_status_active": "Active",
        "main_status_inactive": "Inactive",
        "main_date_range": "Date range in archive:",
        "main_date_range_none": "no recognized dated folders",
        "main_last_check": "Last check:",
        "main_last_check_never": "not run yet",
        "main_details_show": "Show summary \u25be",
        "main_details_hide": "Hide summary \u25b4",
        "main_details_ignored_header": "Not recognized / left untouched:",
        "main_details_ignored_empty": "No unrecognized items found.",
        "main_details_reason_not_a_folder": "file (not a folder)",
        "main_details_reason_format_mismatch": "name doesn't match the configured date format",
        "main_details_reason_invalid_date": "looks like a date, but it isn't a valid calendar date",
        "main_refresh": "Refresh",
        "menu_settings": "Settings",
        "menu_info": "Info",
        # --- Settings window ---
        "settings_title": "Archisight \u2014 Settings",
        "settings_language": "Language",
        "settings_language_en": "English",
        "settings_language_ru": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439",
        "settings_retention_days": "How many days to keep",
        "settings_retention_hint": "from {min} to {max} days",
        "settings_archive_path": "Archive folder",
        "settings_browse": "Browse\u2026",
        "settings_clear_path": "Clear path",
        "settings_run_time": "Daily auto-check time",
        "settings_clear_time": "Clear time",
        "settings_run_time_hint": "If no time is set, the automatic run never happens \u2014 even with autostart on.",
        "settings_date_format_header": "Folder name date format",
        "settings_date_order": "Order",
        "settings_date_order_dmy": "Day-Month-Year",
        "settings_date_order_mdy": "Month-Day-Year",
        "settings_date_order_ymd": "Year-Month-Day",
        "settings_separator": "Separator",
        "settings_sep_dot": "Dot ( . )",
        "settings_sep_dash": "Dash ( - )",
        "settings_sep_comma": "Comma ( , )",
        "settings_year_format": "Year format",
        "settings_year_short": "Short (26)",
        "settings_year_full": "Full (2026)",
        "settings_preview": "Preview:",
        "settings_preview_hint": "This is the exact folder name pattern Archisight will look for.",
        "settings_autostart": "Start automatically with Windows",
        "settings_apply_now": "Apply now",
        "settings_save": "Save",
        "settings_reset": "Reset to defaults",
        "settings_cancel": "Cancel",
        "settings_saved_toast": "Settings saved.",
        "settings_invalid_days": "Enter a whole number between {min} and {max}.",
        "settings_apply_now_no_path": "Choose an archive folder first.",
        "settings_apply_now_confirm_title": "Run now?",
        "settings_apply_now_confirm_text": (
            "Archisight will scan the archive folder right now using the "
            "settings currently shown in this window (even if not saved yet) "
            "and permanently delete any outdated folders.\n\nThis cannot be undone. Continue?"
        ),
        "settings_apply_now_result_title": "Run result",
        "settings_apply_now_result_deleted": "Folders deleted: {n}",
        "settings_apply_now_result_kept": "Folders kept: {n}",
        "settings_apply_now_result_ignored": "Unrecognized items (untouched): {n}",
        "settings_apply_now_result_errors": "Errors while deleting: {n}",
        "settings_apply_now_result_no_reference": (
            "No reference date could be determined (no dated folder is dated today or earlier). "
            "Nothing was deleted this run."
        ),
        "settings_reset_confirm_title": "Reset settings?",
        "settings_reset_confirm_text": (
            "This will restore Archisight to its default settings: no archive path, "
            "no scheduled time, default date format, autostart disabled. Continue?"
        ),
        "settings_path_invalid": "This path doesn't exist or isn't a folder.",
        # --- About window ---
        "about_title": "Archisight \u2014 About",
        "about_close": "Close",
        "about_body": (
            "Archisight\n"
            "Archive + Oversight\n\n"
            "Archisight quietly watches one folder \u2014 your daily-work archive \u2014 "
            "and keeps it tidy on its own.\n\n"
            "How it works:\n"
            "Every day you move yesterday's working folder into an archive, and start a "
            "fresh dated folder for today. Over weeks and months the archive fills up with "
            "dozens of dated folders, and old ones just take up space and clutter your view. "
            "Archisight looks only at folder names that exactly match a date pattern you "
            "configure (e.g. 10.07.26), finds the most recent one that isn't in the future, "
            "counts back the number of days you chose, and removes whatever is older \u2014 "
            "folder and all of its contents. Anything that doesn't match your exact date "
            "format \u2014 stray files, differently named folders \u2014 is never touched, only "
            "reported to you. Archisight never looks inside subfolders of your dated "
            "folders, and it never goes outside the one archive path you choose.\n\n"
            "You control everything: how many days to keep (3 to 730), the exact folder "
            "name pattern, what time of day the automatic check runs, and whether it runs "
            "automatically at all. A dedicated 'Apply now' button lets you test the effect "
            "instantly before turning autostart on.\n\n"
            "Author: Barkov N.S.\n"
            "Contact: tidesluck@icloud.com"
        ),
        # --- Tray ---
        "tray_open": "Open",
        "tray_settings": "Settings",
        "tray_info": "Info",
        "tray_exit": "Exit",
        "tray_tooltip_never": "Archisight \u2014 no checks run yet",
        "tray_tooltip_last": "Archisight \u2014 last check: {when}",
        "tray_minimized_title": "Archisight",
        "tray_minimized_text": "Archisight is still running in the background.",
        # --- Errors / common ---
        "error_title": "Error",
        "error_path_missing": "The selected path is unavailable or is not a folder.",
        "confirm_exit_title": "Exit Archisight?",
        "confirm_exit_text": "This will stop background monitoring until you open Archisight again. Continue?",
        "yes": "Yes",
        "no": "No",
        "ok": "OK",
    },
    "ru": {
        # --- Главное окно ---
        "app_title": "Archisight",
        "main_current_date": "Текущая дата:",
        "main_folders_found": "Найдено папок:",
        "main_retention_days": "Хранится дней:",
        "main_archive_path": "Путь к архиву:",
        "main_no_path_set": "Путь не выбран — откройте настройки",
        "main_open_archive": "Открыть архив",
        "main_status": "Статус:",
        "main_status_active": "Активно",
        "main_status_inactive": "Неактивно",
        "main_date_range": "Диапазон дат в архиве:",
        "main_date_range_none": "распознанных папок с датой нет",
        "main_last_check": "Последняя проверка:",
        "main_last_check_never": "ещё не выполнялась",
        "main_details_show": "Показать сводку \u25be",
        "main_details_hide": "Скрыть сводку \u25b4",
        "main_details_ignored_header": "Не распознано / не тронуто:",
        "main_details_ignored_empty": "Посторонних объектов не найдено.",
        "main_details_reason_not_a_folder": "файл (не папка)",
        "main_details_reason_format_mismatch": "имя не совпадает с заданным форматом даты",
        "main_details_reason_invalid_date": "похоже на дату, но такой даты не существует",
        "main_refresh": "Обновить",
        "menu_settings": "Настройки",
        "menu_info": "Инфо",
        # --- Окно настроек ---
        "settings_title": "Archisight — Настройки",
        "settings_language": "Язык",
        "settings_language_en": "English",
        "settings_language_ru": "Русский",
        "settings_retention_days": "Сколько дней хранить",
        "settings_retention_hint": "от {min} до {max} дней",
        "settings_archive_path": "Папка архива",
        "settings_browse": "Обзор…",
        "settings_clear_path": "Очистить путь",
        "settings_run_time": "Время ежедневной автопроверки",
        "settings_clear_time": "Очистить время",
        "settings_run_time_hint": "Если время не задано — автоматический запуск не выполняется, даже при включённом автозапуске.",
        "settings_date_format_header": "Формат названий папок",
        "settings_date_order": "Порядок",
        "settings_date_order_dmy": "День-Месяц-Год",
        "settings_date_order_mdy": "Месяц-День-Год",
        "settings_date_order_ymd": "Год-Месяц-День",
        "settings_separator": "Разделитель",
        "settings_sep_dot": "Точка ( . )",
        "settings_sep_dash": "Тире ( - )",
        "settings_sep_comma": "Запятая ( , )",
        "settings_year_format": "Формат года",
        "settings_year_short": "Короткий (26)",
        "settings_year_full": "Полный (2026)",
        "settings_preview": "Пример:",
        "settings_preview_hint": "Именно такой шаблон названия папки Archisight будет искать.",
        "settings_autostart": "Запускать вместе с Windows",
        "settings_apply_now": "Применить сейчас",
        "settings_save": "Сохранить",
        "settings_reset": "Сбросить",
        "settings_cancel": "Отмена",
        "settings_saved_toast": "Настройки сохранены.",
        "settings_invalid_days": "Введите целое число от {min} до {max}.",
        "settings_apply_now_no_path": "Сначала укажите папку архива.",
        "settings_apply_now_confirm_title": "Выполнить проверку сейчас?",
        "settings_apply_now_confirm_text": (
            "Archisight прямо сейчас просканирует папку архива с настройками, "
            "показанными в этом окне (даже если вы их ещё не сохранили), "
            "и безвозвратно удалит устаревшие папки.\n\nЭто действие нельзя отменить. Продолжить?"
        ),
        "settings_apply_now_result_title": "Результат проверки",
        "settings_apply_now_result_deleted": "Удалено папок: {n}",
        "settings_apply_now_result_kept": "Сохранено папок: {n}",
        "settings_apply_now_result_ignored": "Посторонних объектов (не тронуты): {n}",
        "settings_apply_now_result_errors": "Ошибок при удалении: {n}",
        "settings_apply_now_result_no_reference": (
            "Не удалось определить опорную дату (нет ни одной папки с датой "
            "сегодня или раньше). В этом запуске ничего не удалено."
        ),
        "settings_reset_confirm_title": "Сбросить настройки?",
        "settings_reset_confirm_text": (
            "Archisight вернётся к настройкам по умолчанию: путь и время очищены, "
            "формат даты — по умолчанию, автозапуск выключен. Продолжить?"
        ),
        "settings_path_invalid": "Такого пути не существует, либо это не папка.",
        # --- Окно "О программе" ---
        "about_title": "Archisight — О программе",
        "about_close": "Закрыть",
        "about_body": (
            "Archisight\n"
            "Archive + Oversight (архив + обзор)\n\n"
            "Archisight незаметно следит за одной папкой — вашим архивом рабочих "
            "дней — и сама поддерживает в ней порядок.\n\n"
            "Как это работает:\n"
            "Каждый день вы переносите вчерашнюю рабочую папку в архив и создаёте "
            "новую папку с сегодняшней датой. Со временем архив наполняется десятками "
            "папок с датами, а самые старые из них только занимают место и мешают "
            "ориентироваться. Archisight смотрит только на те папки, чьё имя ЦЕЛИКОМ "
            "совпадает с заданным вами форматом даты (например 10.07.26), находит "
            "самую свежую из них, что не позже сегодняшнего дня, отсчитывает от неё "
            "нужное количество дней назад и удаляет всё, что старше — папку целиком "
            "со всем содержимым. Всё остальное — посторонние файлы, папки с другим "
            "именем — программа никогда не трогает, а только показывает в сводке. "
            "Archisight не заглядывает внутрь вложенных папок и не выходит за пределы "
            "выбранного вами пути к архиву.\n\n"
            "Вы полностью управляете поведением программы: сколько дней хранить "
            "(от 3 до 730), точный формат названия папок, в какое время суток "
            "выполняется автоматическая проверка, и выполняется ли она вообще. "
            "Кнопка «Применить сейчас» позволяет мгновенно проверить результат "
            "перед тем, как включать автозапуск.\n\n"
            "Автор: Барков Н.С.\n"
            "Контакт: tidesluck@icloud.com"
        ),
        # --- Трей ---
        "tray_open": "Открыть",
        "tray_settings": "Настройки",
        "tray_info": "Инфо",
        "tray_exit": "Выход",
        "tray_tooltip_never": "Archisight — проверок ещё не было",
        "tray_tooltip_last": "Archisight — последняя проверка: {when}",
        "tray_minimized_title": "Archisight",
        "tray_minimized_text": "Archisight продолжает работать в фоне.",
        # --- Ошибки / общее ---
        "error_title": "Ошибка",
        "error_path_missing": "Указанный путь недоступен или не является папкой.",
        "confirm_exit_title": "Выйти из Archisight?",
        "confirm_exit_text": "Фоновый мониторинг остановится до следующего запуска программы. Продолжить?",
        "yes": "Да",
        "no": "Нет",
        "ok": "ОК",
    },
}


def detect_system_language() -> str:
    """Определяет язык системы. Возвращает 'ru', если система русская, иначе 'en'."""
    candidates = []

    if sys.platform.startswith("win"):
        try:
            import ctypes

            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            # 0x19 = русский язык (primary language id для ru-RU и т.д.)
            primary_lang = lang_id & 0x3FF
            if primary_lang == 0x19:
                return "ru"
            else:
                return "en"
        except Exception:
            pass

    try:
        loc = locale.getlocale()
        if loc and loc[0]:
            candidates.append(loc[0])
    except Exception:
        pass

    for env_var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(env_var)
        if val:
            candidates.append(val)

    for c in candidates:
        if c.lower().startswith("ru"):
            return "ru"

    return DEFAULT_LANGUAGE


_MONTHS_RU_GENITIVE = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]
_MONTHS_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def format_long_date(d, language: str) -> str:
    """Человекочитаемое представление даты для главного экрана,
    например '10 июля 2026' / 'July 10, 2026'."""
    if language == "ru":
        return f"{d.day} {_MONTHS_RU_GENITIVE[d.month - 1]} {d.year}"
    return f"{_MONTHS_EN[d.month - 1]} {d.day}, {d.year}"


def format_datetime_short(dt, language: str) -> str:
    """Короткое представление даты+времени для 'последней проверки' и трея."""
    date_part = format_long_date(dt.date(), language)
    time_part = dt.strftime("%H:%M")
    return f"{date_part}, {time_part}"


class Translator:
    """Простой держатель текущего языка + метод перевода t(key, **kwargs)."""

    def __init__(self, language: str):
        self.language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    def set_language(self, language: str):
        self.language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    def t(self, key: str, **kwargs) -> str:
        table = TRANSLATIONS.get(self.language, TRANSLATIONS[DEFAULT_LANGUAGE])
        text = table.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key) or key
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text
