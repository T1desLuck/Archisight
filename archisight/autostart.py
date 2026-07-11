# -*- coding: utf-8 -*-
"""
autostart.py — включение/выключение автозапуска Archisight вместе с Windows.

Используется стандартный пользовательский ключ реестра
HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
— он не требует прав администратора и является стандартным способом
автозапуска приложений для текущего пользователя.

На не-Windows системах (например, при разработке/тестах в этой песочнице)
все функции безопасно возвращают False / no-op, не пытаясь трогать реестр.
"""

from __future__ import annotations

import os
import sys

AUTOSTART_VALUE_NAME = "Archisight"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def get_launch_command(minimized: bool = True) -> str:
    """Строит команду автозапуска.

    Если приложение собрано через PyInstaller (frozen) — запускается сам exe.
    Иначе (режим разработки) — запускается через pythonw.exe, чтобы не
    показывать консольное окно.
    """
    if getattr(sys, "frozen", False):
        exe = sys.executable
        cmd = f'"{exe}"'
    else:
        python_dir = os.path.dirname(sys.executable)
        pythonw = os.path.join(python_dir, "pythonw.exe")
        if not os.path.isfile(pythonw):
            pythonw = sys.executable
        main_script = os.path.abspath(sys.argv[0])
        cmd = f'"{pythonw}" "{main_script}"'

    if minimized:
        cmd += " --minimized"
    return cmd


def is_autostart_registered() -> bool:
    """Проверяет РЕАЛЬНОЕ состояние в реестре (источник истины для статуса
    "Активно/Неактивно" на главном экране), а не только сохранённый флаг
    в config.json — так статус остаётся верным, даже если реестр был
    изменён в обход программы."""
    if not _is_windows():
        return False
    import winreg  # импортируется только на Windows

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, AUTOSTART_VALUE_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_autostart(enabled: bool) -> bool:
    """Включает или выключает автозапуск. Возвращает True при успехе."""
    if not _is_windows():
        return False
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key, AUTOSTART_VALUE_NAME, 0, winreg.REG_SZ, get_launch_command()
                )
            else:
                try:
                    winreg.DeleteValue(key, AUTOSTART_VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False
