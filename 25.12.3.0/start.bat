@echo off
chcp 65001 > nul
title File Renamer v3.0
color 0A
cls

echo ====================================================
echo      ПРОГРАММА ПЕРЕИМЕНОВАНИЯ ФАЙЛОВ v3.0
echo ====================================================
echo.

echo Проверяем наличие Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Скачайте и установите Python с python.org
    echo Обязательно отметьте "Add Python to PATH" при установке
    pause
    exit /b 1
)

echo Python найден!
py --version
echo.

echo Устанавливаем необходимые библиотеки...
echo ------------------------------------------------
py -m pip install pandas --quiet --upgrade
py -m pip install openpyxl --quiet --upgrade
echo ------------------------------------------------
echo.

echo Запускаем программу...
timeout /t 2 /nobreak > nul

python renamer_gui.py
pause