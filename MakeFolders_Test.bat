@echo off
rem = """
:: Проверяем, есть ли Питон
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не установлен или не добавлен в PATH!
    echo Скачайте Python с python.org и при установке поставьте галочку "Add python.exe to PATH".
    pause
    exit /b
)

:: Запускаем этот же файл, но уже как Python-скрипт
echo Запускаю создание папок...
python -x "%~f0"
pause
exit /b
"""

import os, random
from datetime import datetime, timedelta

# Стартовая дата: 11.07.26 (Год, Месяц, День)
start_date = datetime(2026, 7, 11)
folders_created = 0
current_date = start_date

while folders_created < 200:
    # Форматируем в ДД.ММ.ГГ
    folder_name = current_date.strftime("%d.%m.%y")
    
    # Создаем папку, если такой еще нет
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    folders_created += 1

    # Логика пропуска: 15% шанс перепрыгнуть 1 или 2 дня
    if random.random() < 0.15:
        skip = random.choice([1, 2])
        current_date -= timedelta(days=1 + skip)
    else:
        # Иначе просто идем на 1 день назад
        current_date -= timedelta(days=1)

print("\nГотово! 200 папок с датами успешно созданы.")