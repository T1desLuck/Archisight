# -*- coding: utf-8 -*-
"""
Тесты ядра логики Archisight. Запуск:
    cd archisight_project
    python -m unittest discover tests -v

Эти тесты НЕ требуют tkinter/pystray и работают на любой ОС —
проверяют только archisight/core.py (сканирование, расчёт хранения,
реальное и тестовое удаление).
"""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from archisight.core import (
    DateFormatSettings,
    compute_retention,
    format_date,
    parse_folder_name,
    perform_cleanup,
    scan_archive,
)


def make_archive(names):
    base = tempfile.mkdtemp(prefix="archisight_test_")
    for n in names:
        os.makedirs(os.path.join(base, n))
        with open(os.path.join(base, n, "file.txt"), "w") as f:
            f.write("content")
    return base


class TestDateParsing(unittest.TestCase):
    def test_dmy_dot_short_year(self):
        fmt = DateFormatSettings(order="DMY", separator=".", year_format="short")
        self.assertEqual(parse_folder_name("10.07.26", fmt), date(2026, 7, 10))
        self.assertEqual(parse_folder_name("5.7.26", fmt), date(2026, 7, 5))  # без ведущего нуля
        self.assertIsNone(parse_folder_name("10-07-26", fmt))  # неверный разделитель
        self.assertIsNone(parse_folder_name("10.07.2026", fmt))  # полный год вместо короткого
        self.assertIsNone(parse_folder_name("32.07.26", fmt))  # несуществующая дата
        self.assertIsNone(parse_folder_name("10.07.26 (копия)", fmt))  # лишние символы

    def test_mdy_dash_full_year(self):
        fmt = DateFormatSettings(order="MDY", separator="-", year_format="full")
        self.assertEqual(parse_folder_name("7-10-2026", fmt), date(2026, 7, 10))
        self.assertIsNone(parse_folder_name("7-10-26", fmt))

    def test_ymd_comma(self):
        fmt = DateFormatSettings(order="YMD", separator=",", year_format="full")
        self.assertEqual(parse_folder_name("2026,07,10", fmt), date(2026, 7, 10))

    def test_format_date_symmetry(self):
        fmt = DateFormatSettings(order="DMY", separator=".", year_format="short")
        d = date(2026, 7, 5)
        s = format_date(d, fmt)
        self.assertEqual(s, "5.7.26")
        self.assertEqual(parse_folder_name(s, fmt), d)


class TestRetentionCalculation(unittest.TestCase):
    def setUp(self):
        self.fmt = DateFormatSettings(order="DMY", separator=".", year_format="short")

    def test_example_from_spec_no_gaps(self):
        """Ровно пример из ТЗ: today=10.07.26, retention=10 -> хранится
        07.07..28.06 (10 папок), удаляется всё старше 28.06.26."""
        names = [
            "07.07.26", "06.07.26", "05.07.26", "04.07.26", "03.07.26",
            "02.07.26", "01.07.26", "30.06.26", "29.06.26", "28.06.26",
            "27.06.26", "26.06.26", "25.06.26",
        ]
        base = make_archive(names)
        try:
            report = perform_cleanup(base, self.fmt, retention_days=10, today=date(2026, 7, 10), dry_run=True)
            kept = sorted(n for _, _, n in report.retention.keep)
            deleted = sorted(n for _, _, n in report.retention.delete)
            self.assertEqual(
                kept,
                sorted(["07.07.26", "06.07.26", "05.07.26", "04.07.26", "03.07.26",
                        "02.07.26", "01.07.26", "30.06.26", "29.06.26", "28.06.26"]),
            )
            self.assertEqual(deleted, sorted(["27.06.26", "26.06.26", "25.06.26"]))
        finally:
            shutil.rmtree(base)

    def test_weekend_gap_does_not_break_counting(self):
        """Пропуск даты (выходной, папки físicamente нет) не должен ломать расчёт —
        отсутствующая дата просто пропускается, диапазон считается по календарным дням."""
        names = [
            "07.07.26", "06.07.26", "05.07.26", "04.07.26", "03.07.26", "02.07.26",
            # 01.07.26 отсутствует (выходной)
            "30.06.26", "29.06.26", "28.06.26", "27.06.26",
        ]
        base = make_archive(names)
        try:
            report = perform_cleanup(base, self.fmt, retention_days=10, today=date(2026, 7, 10), dry_run=True)
            # cutoff = 07.07.26 - 9 дней = 28.06.26
            kept = sorted(n for _, _, n in report.retention.keep)
            deleted = sorted(n for _, _, n in report.retention.delete)
            self.assertNotIn("27.06.26", kept)
            self.assertIn("27.06.26", deleted)
            self.assertIn("28.06.26", kept)
        finally:
            shutil.rmtree(base)

    def test_no_valid_folders(self):
        base = make_archive(["not_a_date_folder"])
        try:
            report = perform_cleanup(base, self.fmt, retention_days=10, today=date(2026, 7, 10), dry_run=True)
            self.assertEqual(report.retention.reference_note, "no_valid_folders")
            self.assertEqual(report.retention.delete, [])
        finally:
            shutil.rmtree(base)

    def test_all_future_dates_are_never_deleted(self):
        base = make_archive(["01.01.30", "02.01.30"])
        try:
            report = perform_cleanup(base, self.fmt, retention_days=10, today=date(2026, 7, 10), dry_run=True)
            self.assertEqual(report.retention.reference_note, "all_future_dates")
            self.assertEqual(report.retention.delete, [])
            self.assertEqual(len(report.retention.keep), 2)
        finally:
            shutil.rmtree(base)

    def test_missing_path_reports_error_not_crash(self):
        report = perform_cleanup("/this/path/does/not/exist", self.fmt, retention_days=10, dry_run=True)
        self.assertEqual(report.error, "path_missing")
        self.assertFalse(report.success)


class TestScanIgnoresForeignItems(unittest.TestCase):
    def test_files_and_mismatched_folders_are_ignored_not_touched(self):
        fmt = DateFormatSettings(order="DMY", separator=".", year_format="short")
        base = make_archive(["10.07.26", "some_project_folder"])
        with open(os.path.join(base, "notes.txt"), "w") as f:
            f.write("do not touch")
        try:
            scan = scan_archive(base, fmt)
            self.assertEqual(len(scan.valid), 1)
            ignored_names = sorted(i.name for i in scan.ignored)
            self.assertEqual(ignored_names, ["notes.txt", "some_project_folder"])
            # физически ничего не удалено сканированием
            self.assertTrue(os.path.isfile(os.path.join(base, "notes.txt")))
            self.assertTrue(os.path.isdir(os.path.join(base, "some_project_folder")))
        finally:
            shutil.rmtree(base)


class TestRealDeletion(unittest.TestCase):
    def test_real_deletion_removes_only_expired_folders_with_contents(self):
        fmt = DateFormatSettings(order="DMY", separator=".", year_format="short")
        names = ["10.07.26", "09.07.26", "01.01.26"]
        base = make_archive(names)
        try:
            report = perform_cleanup(base, fmt, retention_days=3, today=date(2026, 7, 10), dry_run=False)
            remaining = sorted(os.listdir(base))
            self.assertEqual(remaining, ["09.07.26", "10.07.26"])
            self.assertEqual(report.deleted_names, ["01.01.26"])
        finally:
            shutil.rmtree(base)


if __name__ == "__main__":
    unittest.main()
