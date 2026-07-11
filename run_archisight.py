# -*- coding: utf-8 -*-
"""
run_archisight.py — точка входа верхнего уровня.

Используется:
  1. Для запуска из исходников:      python run_archisight.py
  2. Как входной файл для PyInstaller при сборке .exe (см. build/build.bat)

Отдельный файл нужен потому, что archisight/main.py использует
относительные импорты (часть пакета archisight) — PyInstaller и обычный
"python archisight/main.py" такое напрямую не запустят, а через этот
файл пакет импортируется правильно.
"""

from archisight.main import main

if __name__ == "__main__":
    main()
