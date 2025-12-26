@echo off
chcp 65001 > nul
title File Renamer v4.0 - Сортировка по дате создания
color 0A
cls

echo ====================================================
echo      ПРОГРАММА ПЕРЕИМЕНОВАНИЯ ФАЙЛОВ v4.0
echo      Версия с сортировкой по дате создания
echo ====================================================
echo.

echo Проверяем наличие Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Скачайте и установите Python с python.org
    echo Обязательно отметьте "Add Python to PATH" при установке
    echo.
    pause
    exit /b 1
)

echo Python найден!
py --version
echo.

echo Устанавливаем/проверяем необходимые библиотеки...
echo ------------------------------------------------
py -m pip install pandas --quiet --upgrade
if errorlevel 1 (
    echo Ошибка при установке pandas
    echo Попробуйте установить вручную: py -m pip install pandas
    pause
    exit /b 1
)

py -m pip install openpyxl --quiet --upgrade
if errorlevel 1 (
    echo Ошибка при установке openpyxl
    echo Попробуйте установить вручную: py -m pip install openpyxl
    pause
    exit /b 1
)

echo ------------------------------------------------
echo Библиотеки успешно установлены!
echo.

echo ====================================================
echo ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:
echo.
echo 1. В таблице Excel/CSV должен быть ОДИН столбец
echo    с новыми именами файлов (без расширения)
echo.
echo 2. Программа берет файлы из папки, сортирует их
echo    ПО ДАТЕ СОЗДАНИЯ (от старых к новым)
echo.
echo 3. Порядок переименования:
echo    - Самый старый файл -> первое имя из таблицы
echo    - Второй по старшинству -> второе имя и т.д.
echo.
echo 4. К каждому новому имени добавляется .mp4
echo    Дубликаты получают номера: (1), (2)...
echo ====================================================
echo.

echo Запускаем программу переименования...
echo.

timeout /t 3 /nobreak > nul

rem Запускаем скрипт Python
if exist "renamer_gui_v4.py" (
    python renamer_gui_v4.py
) else (
    echo ОШИБКА: Файл renamer_gui_v4.py не найден!
    echo Убедитесь, что в этой папке есть файл renamer_gui_v4.py
    echo.
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo ====================================================
    echo Произошла ошибка при запуске программы.
    echo.
    echo ВОЗМОЖНЫЕ ПРИЧИНЫ:
    echo 1. Отсутствуют необходимые библиотеки
    echo 2. Ошибки в коде Python
    echo 3. Проблемы с доступом к файлам
    echo.
    echo РЕШЕНИЯ:
    echo 1. Установите библиотеки: py -m pip install pandas openpyxl
    echo 2. Проверьте правильность кода в renamer_gui_v4.py
    echo 3. Убедитесь, что файлы не используются другими программами
    echo.
    echo ====================================================
    pause
)

pause