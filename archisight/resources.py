# -*- coding: utf-8 -*-
"""resources.py — поиск пути к файлам ресурсов (иконка и т.п.).

Работает как при запуске из исходников, так и из exe, собранного
PyInstaller (который распаковывает ресурсы во временную папку
sys._MEIPASS во время выполнения).
"""

from __future__ import annotations

import os
import sys


def get_asset_path(filename: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS  # type: ignore[attr-defined]
        candidate = os.path.join(base, "assets", filename)
        if os.path.isfile(candidate):
            return candidate
    package_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(package_dir, "assets", filename)
