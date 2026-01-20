@echo off
chcp 65001 > nul
cls
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║      File Renamer v13.1.0 - Установка зависимостей       ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo.
    echo Скачайте с: https://www.python.org/downloads/
    echo При установке поставьте галочку "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo ✅ Python найден
echo.
echo Установка pandas и openpyxl...
echo.
python -m pip install --upgrade pip
python -m pip install pandas openpyxl

if errorlevel 1 (
    echo.
    echo ❌ Ошибка установки
    echo.
    pause
    exit /b 1
)

cls
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                 ✅ Установка завершена!                 ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo Теперь запустите программу:
echo.
echo   • Двойной клик на renamer_gui_v13_unified.pyw
echo   или
echo   • Двойной клик на ПУСК.bat
echo.
echo ══════════════════════════════════════════════════════════
pause
