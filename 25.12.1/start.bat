@echo off
chcp 65001 > nul
title File Renamer - GUI Version
color 0A
cls

echo ====================================================
echo      ПРОГРАММА ПЕРЕИМЕНОВАНИЯ ФАЙЛОВ
echo      Графическая версия с удобным интерфейсом
echo ====================================================
echo.
echo Убедитесь, что у вас установлен Python 3.6 или выше!
echo.
echo Проверяем наличие Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ОШИБКА: Python не установлен или не добавлен в PATH!
    echo.
    echo Инструкция:
    echo 1. Скачайте Python с https://python.org/downloads/
    echo 2. При установке ОБЯЗАТЕЛЬНО отметьте галочку:
    echo    "Add Python to PATH"
    echo 3. Перезапустите компьютер после установки
    echo 4. Запустите этот файл снова
    pause
    exit
)

echo.
echo Python найден! Проверяем необходимые библиотеки...
echo.

echo Устанавливаем библиотеки (если их нет)...
pip install pandas openpyxl --quiet
echo.

echo Запускаем программу...
echo.
echo Если появится окно с двумя кнопками "Обзор" - все работает!
echo ====================================================
echo.

python renamer_gui.py

if errorlevel 1 (
    echo.
    echo Произошла ошибка при запуске программы.
    echo Попробуйте установить библиотеки вручную:
    echo.
    echo Откройте командную строку и выполните:
    echo pip install pandas openpyxl
    echo.
    pause
)