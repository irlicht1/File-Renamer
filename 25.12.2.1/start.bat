@echo off
chcp 65001 > nul
title File Renamer v2.0
color 0A
cls

echo ====================================================
echo      ПРОГРАММА ПЕРЕИМЕНОВАНИЯ ФАЙЛОВ v2.0
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
if errorlevel 1 (
    echo Ошибка при установке pandas
    pause
    exit /b 1
)

py -m pip install openpyxl --quiet --upgrade
if errorlevel 1 (
    echo Ошибка при установке openpyxl
    pause
    exit /b 1
)

echo ------------------------------------------------
echo Запускаем программу...
echo.

timeout /t 2 /nobreak > nul

rem Запускаем скрипт Python
if exist "renamer_gui.py" (
    python renamer_gui.py
) else (
    echo Файл renamer_gui.py не найден!
    pause
    exit /b 1
)

pause