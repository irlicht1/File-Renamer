rem Автопоиск файла программы (если нужно)
for %%F in (renamer_gui_*.py) do (
    echo ✅ Найден файл: %%F
    set "python_file=%%F"
    goto :found_file
)

:found_file
if defined python_file (
    echo Используется файл: %python_file%
    python "%python_file%"
) else (
    echo ❌ Не найден файл программы renamer_gui_*.py
    pause
    exit /b 1
)