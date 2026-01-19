@echo off
chcp 65001 > nul
title File Renamer v5.0 - Улучшенная диагностика
color 0A
cls

echo ========================================================
echo      ПРОГРАММА ПЕРЕИМЕНОВАНИЯ ФАЙЛОВ v5.0
echo      Версия с расширенной диагностикой проблем
echo ========================================================
echo.

echo Проверяем наличие Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo.
    echo РЕШЕНИЕ:
    echo 1. Скачайте Python с python.org
    echo 2. При установке отметьте "Add Python to PATH"
    echo 3. Перезапустите компьютер
    echo.
    pause
    exit /b 1
)

echo Python найден!
py --version
echo.

echo Устанавливаем/проверяем необходимые библиотеки...
echo --------------------------------------------------------
echo Устанавливаем pandas...
py -m pip install pandas --quiet --upgrade
if errorlevel 1 (
    echo ❌ Ошибка установки pandas
    echo Попробуйте: py -m pip install pandas --user
    pause
    exit /b 1
)

echo Устанавливаем openpyxl...
py -m pip install openpyxl --quiet --upgrade
if errorlevel 1 (
    echo ❌ Ошибка установки openpyxl
    echo Попробуйте: py -m pip install openpyxl --user
    pause
    exit /b 1
)

echo --------------------------------------------------------
echo ✅ Библиотеки успешно установлены!
echo.

echo ========================================================
echo ОСОБЕННОСТИ ВЕРСИИ 5.0:
echo.
echo 1. Детальный анализ таблицы:
echo    - Показывает пустые строки
echo    - Показывает строки только с пробелами
echo    - Отображает все действительные имена
echo.
echo 2. Подробная диагностика:
echo    - Сравнение количества файлов и имен
echo    - Показывает разницу если количества не совпадают
echo    - Экспорт лога в файл
echo.
echo 3. Сортировка по дате создания
echo 4. Обработка дубликатов с нумерацией
echo 5. Автоматическое добавление .mp4
echo ========================================================
echo.

echo Запускаем программу переименования...
echo.

timeout /t 3 /nobreak > nul

rem Проверяем наличие файла программы
if not exist "renamer_gui_v5.py" (
    echo ❌ ОШИБКА: Файл renamer_gui_v5.py не найден!
    echo.
    echo Убедитесь, что в этой папке есть файл renamer_gui_v5.py
    echo или переименуйте ваш файл в renamer_gui_v5.py
    echo.
    pause
    exit /b 1
)

rem Запускаем программу
echo ✅ Запуск программы...
python renamer_gui_v5.py

if errorlevel 1 (
    echo.
    echo ========================================================
    echo ❌ Произошла ошибка при запуске программы.
    echo.
    echo ВОЗМОЖНЫЕ ПРИЧИНЫ:
    echo 1. Отсутствуют необходимые библиотеки
    echo 2. Ошибка в коде Python
    echo 3. Проблемы с доступом к файлам
    echo.
    echo РЕШЕНИЯ:
    echo 1. Установите библиотеки: py -m pip install pandas openpyxl
    echo 2. Проверьте, что файлы не используются другими программами
    echo 3. Запустите программу от имени администратора
    echo.
    echo ========================================================
)

echo.
pause