# -*- coding: utf-8 -*-
"""
core.py — вся логика работы с архивом Archisight, не зависящая от GUI.

Специально вынесена в отдельный модуль без импорта tkinter/pystray,
чтобы её можно было тестировать и переиспользовать независимо от интерфейса.

Ключевое правило удаления (см. README):
  1. Среди папок, чьё имя ЦЕЛИКОМ совпадает с настроенным форматом даты,
     находим самую свежую дату, которая не позже сегодняшней (today).
  2. От этой даты отсчитываем N календарных дней НАЗАД (N = retention_days).
     Это даёт "нижнюю границу" (cutoff) — например при N=10 и свежей дате
     07.07.2026 нижняя граница будет 28.06.2026.
  3. Все папки с датой >= cutoff — хранятся и не трогаются, даже если для
     каких-то дат внутри диапазона папок физически нет (выходные).
  4. Все папки с датой < cutoff — удаляются целиком (папка + всё содержимое).
  5. Всё, что не подпадает под формат даты (файлы, чужие папки, папки с
     датой в другом формате/разделителе) — никогда не трогается, а только
     показывается пользователю как "непонятные объекты".
  6. Сканирование НЕ рекурсивное — только первый уровень вложенности.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Tuple

DATE_ORDERS = ("DMY", "MDY", "YMD")
SEPARATORS = (".", "-", ",")
YEAR_FORMATS = ("short", "full")  # short = 2 digits (26), full = 4 digits (2026)

MIN_RETENTION_DAYS = 3
MAX_RETENTION_DAYS = 730
DEFAULT_RETENTION_DAYS = 90

# Порог для интерпретации короткого года: всегда считаем как 2000 + yy.
# Это осознанное упрощение: архив используется для недавних рабочих дней,
# формат "26" -> 2026 однозначен для практического диапазона дат этого приложения.
SHORT_YEAR_BASE = 2000


@dataclass(frozen=True)
class DateFormatSettings:
    order: str = "DMY"          # DMY / MDY / YMD
    separator: str = "."        # . - ,
    year_format: str = "short"  # short / full

    def __post_init__(self):
        if self.order not in DATE_ORDERS:
            raise ValueError(f"Unknown date order: {self.order}")
        if self.separator not in SEPARATORS:
            raise ValueError(f"Unknown separator: {self.separator}")
        if self.year_format not in YEAR_FORMATS:
            raise ValueError(f"Unknown year format: {self.year_format}")


@dataclass
class IgnoredItem:
    name: str
    kind: str    # "file" | "folder"
    reason: str  # "not_a_folder" | "format_mismatch" | "invalid_date"


@dataclass
class ScanResult:
    valid: List[Tuple[date, str, str]] = field(default_factory=list)  # (date, full_path, folder_name)
    ignored: List[IgnoredItem] = field(default_factory=list)
    error: Optional[str] = None  # "path_missing" | None


@dataclass
class RetentionResult:
    freshest: Optional[date]
    cutoff: Optional[date]
    keep: List[Tuple[date, str, str]]
    delete: List[Tuple[date, str, str]]
    reference_note: str  # "normal" | "all_future_dates" | "no_valid_folders"


@dataclass
class CleanupReport:
    success: bool
    error: Optional[str]
    scan: Optional[ScanResult]
    retention: Optional[RetentionResult]
    deleted_names: List[str] = field(default_factory=list)
    delete_errors: List[dict] = field(default_factory=list)
    dry_run: bool = False


def _escaped_sep(separator: str) -> str:
    return re.escape(separator)


def build_regex(fmt: DateFormatSettings) -> re.Pattern:
    """Строит regex, требующий ПОЛНОГО совпадения имени папки с форматом даты.

    День/месяц — 1 или 2 цифры (без обязательного ведущего нуля).
    Год — 2 или 4 цифры в зависимости от настройки.
    """
    d = r"(?P<d>\d{1,2})"
    m = r"(?P<m>\d{1,2})"
    y = r"(?P<y>\d{2})" if fmt.year_format == "short" else r"(?P<y>\d{4})"
    sep = _escaped_sep(fmt.separator)

    parts = {"D": d, "M": m, "Y": y}
    order_letters = {"DMY": "DMY", "MDY": "MDY", "YMD": "YMD"}[fmt.order]
    pattern_body = sep.join(parts[letter] for letter in order_letters)
    return re.compile(rf"^{pattern_body}$")


def parse_folder_name(name: str, fmt: DateFormatSettings) -> Optional[date]:
    """Возвращает date, если имя папки ЦЕЛИКОМ соответствует формату, иначе None."""
    pattern = build_regex(fmt)
    match = pattern.match(name)
    if not match:
        return None
    try:
        day = int(match.group("d"))
        month = int(match.group("m"))
        year = int(match.group("y"))
        if fmt.year_format == "short":
            year += SHORT_YEAR_BASE
        return date(year, month, day)
    except ValueError:
        return None


def format_date(d: date, fmt: DateFormatSettings) -> str:
    """Форматирует дату согласно настройкам — используется для живого превью
    в окне настроек и для отображения диапазонов дат на главном экране."""
    day = str(d.day)
    month = str(d.month)
    year = str(d.year % 100).zfill(2) if fmt.year_format == "short" else str(d.year)
    values = {"D": day, "M": month, "Y": year}
    order_letters = fmt.order
    return fmt.separator.join(values[letter] for letter in order_letters)


def scan_archive(archive_path: Optional[str], fmt: DateFormatSettings) -> ScanResult:
    """Сканирует ТОЛЬКО первый уровень вложенности архива."""
    if not archive_path or not os.path.isdir(archive_path):
        return ScanResult(valid=[], ignored=[], error="path_missing")

    pattern = build_regex(fmt)
    valid: List[Tuple[date, str, str]] = []
    ignored: List[IgnoredItem] = []

    try:
        entries = list(os.scandir(archive_path))
    except OSError:
        return ScanResult(valid=[], ignored=[], error="path_missing")

    for entry in entries:
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError:
            continue

        if not is_dir:
            ignored.append(IgnoredItem(name=entry.name, kind="file", reason="not_a_folder"))
            continue

        match = pattern.match(entry.name)
        if not match:
            ignored.append(IgnoredItem(name=entry.name, kind="folder", reason="format_mismatch"))
            continue

        try:
            day = int(match.group("d"))
            month = int(match.group("m"))
            year = int(match.group("y"))
            if fmt.year_format == "short":
                year += SHORT_YEAR_BASE
            parsed = date(year, month, day)
        except ValueError:
            ignored.append(IgnoredItem(name=entry.name, kind="folder", reason="invalid_date"))
            continue

        valid.append((parsed, entry.path, entry.name))

    return ScanResult(valid=valid, ignored=ignored, error=None)


def compute_retention(
    valid_entries: List[Tuple[date, str, str]],
    retention_days: int,
    today: Optional[date] = None,
) -> RetentionResult:
    """Считает, какие папки хранить, а какие удалять.

    Опорная точка — самая свежая дата <= today. От неё отсчитываем
    retention_days КАЛЕНДАРНЫХ дней назад (включительно) — это и есть
    диапазон хранения. Пропуски дат (выходные) не влияют на диапазон.
    """
    today = today or date.today()

    if not valid_entries:
        return RetentionResult(
            freshest=None, cutoff=None, keep=[], delete=[], reference_note="no_valid_folders"
        )

    past_or_today = [e for e in valid_entries if e[0] <= today]

    if not past_or_today:
        # Аномалия: все найденные даты — в будущем относительно системной даты.
        # Ничего не удаляем и явно сигнализируем об этом наружу.
        return RetentionResult(
            freshest=None,
            cutoff=None,
            keep=list(valid_entries),
            delete=[],
            reference_note="all_future_dates",
        )

    freshest = max(e[0] for e in past_or_today)
    cutoff = freshest - timedelta(days=retention_days - 1)

    keep = [e for e in valid_entries if e[0] >= cutoff]
    delete = [e for e in valid_entries if e[0] < cutoff]

    return RetentionResult(
        freshest=freshest, cutoff=cutoff, keep=keep, delete=delete, reference_note="normal"
    )


def perform_cleanup(
    archive_path: Optional[str],
    fmt: DateFormatSettings,
    retention_days: int,
    today: Optional[date] = None,
    dry_run: bool = False,
) -> CleanupReport:
    """Полный проход: сканирование + расчёт + (если не dry_run) реальное удаление."""
    scan = scan_archive(archive_path, fmt)
    if scan.error:
        return CleanupReport(success=False, error=scan.error, scan=scan, retention=None, dry_run=dry_run)

    retention = compute_retention(scan.valid, retention_days, today)

    deleted_names: List[str] = []
    delete_errors: List[dict] = []

    if dry_run:
        deleted_names = [name for _, _, name in retention.delete]
    else:
        for _, path, name in retention.delete:
            try:
                shutil.rmtree(path)
                deleted_names.append(name)
            except OSError as exc:
                delete_errors.append({"name": name, "error": str(exc)})

    return CleanupReport(
        success=True,
        error=None,
        scan=scan,
        retention=retention,
        deleted_names=deleted_names,
        delete_errors=delete_errors,
        dry_run=dry_run,
    )
