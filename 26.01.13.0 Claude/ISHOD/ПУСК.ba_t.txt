@echo off
echo Запуск File Renamer v13.0...
start "" pythonw renamer_gui_v13_unified.pyw
if errorlevel 1 (
    start "" python renamer_gui_v13_unified.py
)
exit
