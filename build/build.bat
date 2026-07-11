@echo off
REM ============================================================
REM  build.bat - Сборка Archisight.exe из исходников (Windows)
REM
REM  Запускать из КОРНЯ проекта (там, где лежит run_archisight.py),
REM  например двойным щелчком по build\build.bat из проводника,
REM  либо командой:  build\build.bat
REM ============================================================

setlocal

cd /d "%~dp0\.."

echo.
echo === Archisight: проверка Python ===
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден в PATH. Установите Python 3.10+ с https://python.org
    echo При установке ОБЯЗАТЕЛЬНО отметьте галочку "Add python.exe to PATH".
    pause
    exit /b 1
)

echo.
echo === Archisight: установка зависимостей ===
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Не удалось установить зависимости. См. сообщение об ошибке выше.
    pause
    exit /b 1
)

echo.
echo === Archisight: очистка предыдущей сборки ===
if exist "build_pyinstaller" rmdir /s /q "build_pyinstaller"
if exist "dist" rmdir /s /q "dist"
if exist "Archisight.spec" del /q "Archisight.spec"

echo.
echo === Archisight: сборка .exe (PyInstaller) ===
python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "Archisight" ^
    --icon "archisight\assets\icon.ico" ^
    --add-data "archisight\assets;assets" ^
    --workpath "build_pyinstaller" ^
    --distpath "dist" ^
    run_archisight.py

if errorlevel 1 (
    echo.
    echo Сборка завершилась с ошибкой. См. сообщения выше.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   ГОТОВО! Файл находится здесь:
echo   %cd%\dist\Archisight.exe
echo ============================================================
echo.
echo Можно скопировать Archisight.exe куда угодно (например на
echo рабочий стол или в Program Files) и запускать напрямую —
echo Python на целевом компьютере для этого больше не нужен.
echo.
pause
