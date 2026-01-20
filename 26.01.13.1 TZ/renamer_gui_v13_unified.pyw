# -*- coding: utf-8 -*-
"""
Программа для переименования файлов по таблице
Графический интерфейс - версия 13.0 (улучшенная)
С добавлением суффикса _TZ перед расширением файла
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, List, Any
import re
from collections import defaultdict, Counter
from dataclasses import dataclass
import threading

try:
    import pandas as pd
except ImportError:
    print("Ошибка: Не установлена библиотека pandas")
    print("Установите: pip install pandas openpyxl")
    sys.exit(1)

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

CONFIG = {
    'window': {'width': 750, 'height': 600, 'title': 'Переименование файлов v13.1.0', 'resizable': False},
    'fonts': {'title': ('Arial', 14, 'bold'), 'header': ('Arial', 10, 'bold'), 
              'normal': ('Arial', 9), 'log': ('Consolas', 9), 'small': ('Arial', 8)},
    'logging': {'file': 'file_renamer.log', 'max_bytes': 10*1024*1024, 'backup_count': 3,
                'format': '%(asctime)s - %(levelname)s - %(message)s'},
    'display': {'max_preview_items': 20, 'max_log_lines': 1000},
    'colors': {'info_bg': '#f0f8ff', 'warning_bg': '#fff0f0', 'success': 'green', 'error': 'red'},
    'table_formats': [('Excel files', '*.xlsx *.xls'), ('CSV files', '*.csv'), ('All files', '*.*')],
    'invalid_chars': '<>:"/\\|?*',
    'file_suffix': '_TZ',
    'dry_run': {'enabled': True, 'default': False}
}

# ============================================================================
# ИСКЛЮЧЕНИЯ
# ============================================================================

class FileRenamerError(Exception): pass
class TableError(FileRenamerError): pass
class EmptyTableError(TableError): pass
class FileOperationError(FileRenamerError): pass
class InvalidFileNameError(FileRenamerError): pass

# ============================================================================
# УТИЛИТЫ
# ============================================================================

def sanitize_filename(name: str) -> str:
    if not name or not isinstance(name, str):
        raise InvalidFileNameError("Имя файла не может быть пустым")
    sanitized = name
    for char in CONFIG['invalid_chars']:
        sanitized = sanitized.replace(char, '_')
    sanitized = sanitized.strip().rstrip('.')
    if not sanitized:
        raise InvalidFileNameError(f"Имя '{name}' содержит только недопустимые символы")
    return sanitized

def extract_base_name(name: str) -> str:
    return re.sub(r'\s*\(\d+\)$', '', str(name)).strip()

# ============================================================================
# ПРОЦЕССОР ТАБЛИЦ
# ============================================================================

class TableProcessor:
    def __init__(self, table_path: str):
        self.table_path = Path(table_path)
        self.df = None
        self.names = None
        self._load_table()

    def _load_table(self):
        if not self.table_path.exists():
            raise FileNotFoundError(f"Файл таблицы не найден: {self.table_path}")
        try:
            if self.table_path.suffix.lower() == '.csv':
                self.df = pd.read_csv(self.table_path, encoding='utf-8', header=None)
            else:
                self.df = pd.read_excel(self.table_path, header=None)
            if len(self.df.columns) == 0:
                raise EmptyTableError("Таблица пуста")
            self.names = self.df.iloc[:, 0]
            logging.info(f"Загружена таблица: {self.table_path.name}, строк: {len(self.names)}")
        except pd.errors.EmptyDataError:
            raise EmptyTableError("Файл таблицы пуст")
        except Exception as e:
            raise TableError(f"Ошибка загрузки таблицы: {str(e)}")

    def get_valid_names(self) -> pd.Series:
        non_empty = self.names.dropna()
        non_empty_str = non_empty.astype(str).str.strip()
        valid = non_empty_str[non_empty_str != '']
        try:
            valid = valid.apply(sanitize_filename)
        except Exception as e:
            logging.warning(f"Ошибка санитизации: {str(e)}")
        return valid

    def analyze_content(self) -> Dict[str, Any]:
        total_rows = len(self.names)
        empty_nan = self.names.isna().sum()
        non_empty = self.names.dropna()
        non_empty_str = non_empty.astype(str).str.strip()
        whitespace_only = (non_empty_str == '').sum()
        valid_names = self.get_valid_names()
        duplicates_info = {}
        if len(valid_names) > 0:
            name_counts = Counter(valid_names.tolist())
            duplicates_info = {name: count for name, count in name_counts.items() if count > 1}
        return {
            'total_rows': total_rows, 'empty_nan': int(empty_nan),
            'whitespace_only': int(whitespace_only), 'valid_names': valid_names,
            'valid_count': len(valid_names), 'duplicates_original': duplicates_info,
            'unique_names': len(set(valid_names))
        }

    def get_preview(self, max_items: int = 5) -> List[tuple]:
        preview = []
        for i, value in enumerate(self.names.head(max_items)):
            preview.append((i + 1, "[ПУСТО]" if pd.isna(value) else str(value)))
        return preview

# ============================================================================
# ПЕРЕИМЕНОВАНИЕ ФАЙЛОВ
# ============================================================================

@dataclass
class RenameOperation:
    index: int
    old_path: Path
    new_name: str
    status: str
    error_message: Optional[str] = None
    is_duplicate: bool = False
    duplicate_number: Optional[int] = None

class FileRenamer:
    def __init__(self, folder_path: str, dry_run: bool = False):
        self.folder_path = Path(folder_path)
        self.dry_run = dry_run
        self.operations: List[RenameOperation] = []
        self.files: List[Path] = []
        self._load_files()

    def _load_files(self):
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Папка не найдена: {self.folder_path}")
        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"Это не папка: {self.folder_path}")
        self.files = [item for item in self.folder_path.iterdir() if item.is_file()]
        self.files.sort(key=lambda x: x.name.lower())
        logging.info(f"Загружено {len(self.files)} файлов")

    def get_file_statistics(self) -> Dict[str, int]:
        extensions = {}
        for file_path in self.files:
            ext = file_path.suffix.lower()
            extensions[ext if ext else '[без расширения]'] = extensions.get(ext, 0) + 1
        return extensions

    def prepare_operations(self, new_names: List[str]) -> List[RenameOperation]:
        self.operations = []
        base_name_counter = defaultdict(int)
        used_final_names = set()
        files_to_process = min(len(self.files), len(new_names))
        suffix = CONFIG['file_suffix']

        for i in range(files_to_process):
            file_path = self.files[i]
            original_name = new_names[i]
            base_name = extract_base_name(original_name)
            original_extension = file_path.suffix
            base_name_counter[base_name] += 1

            is_duplicate = False
            duplicate_num = None

            if base_name_counter[base_name] == 1:
                final_base_name = base_name
            else:
                final_base_name = f"{base_name} ({base_name_counter[base_name] - 1})"
                is_duplicate = True
                duplicate_num = base_name_counter[base_name] - 1

            temp_final_name = final_base_name
            suffix_counter = 1
            while temp_final_name in used_final_names:
                temp_final_name = f"{base_name} ({base_name_counter[base_name]-1}_{suffix_counter})"
                suffix_counter += 1

            final_name_without_ext = temp_final_name
            final_name_with_ext = final_name_without_ext + suffix + original_extension
            used_final_names.add(final_name_without_ext)
            new_path = self.folder_path / final_name_with_ext

            if new_path.exists() and new_path != file_path:
                operation = RenameOperation(i+1, file_path, final_name_with_ext, 'error',
                                          'Файл уже существует', is_duplicate, duplicate_num)
            else:
                operation = RenameOperation(i+1, file_path, final_name_with_ext, 'pending',
                                          None, is_duplicate, duplicate_num)
            self.operations.append(operation)

        for i in range(files_to_process, len(self.files)):
            operation = RenameOperation(i+1, self.files[i], '', 'skipped',
                                      'Не хватило имен')
            self.operations.append(operation)

        logging.info(f"Подготовлено {len(self.operations)} операций")
        return self.operations

    def execute_operations(self) -> Dict[str, int]:
        stats = {'success': 0, 'error': 0, 'skipped': 0}
        for op in self.operations:
            if op.status == 'skipped':
                stats['skipped'] += 1
                continue
            if op.status == 'error':
                stats['error'] += 1
                continue
            try:
                new_path = self.folder_path / op.new_name
                if self.dry_run:
                    op.status = 'success'
                    logging.info(f"[DRY RUN] {op.old_path.name} -> {op.new_name}")
                else:
                    op.old_path.rename(new_path)
                    op.status = 'success'
                    logging.info(f"Переименован: {op.old_path.name} -> {op.new_name}")
                stats['success'] += 1
            except Exception as e:
                op.status = 'error'
                op.error_message = str(e)
                stats['error'] += 1
                logging.error(f"Ошибка: {op.old_path.name} - {str(e)}")
        return stats

    def get_duplicate_operations(self) -> List[RenameOperation]:
        return [op for op in self.operations if op.is_duplicate]

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

def setup_logging():
    log_config = CONFIG['logging']
    file_handler = RotatingFileHandler(log_config['file'], maxBytes=log_config['max_bytes'],
                                      backupCount=log_config['backup_count'], encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(log_config['format'])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logging.info("="*50)
    logging.info("File Renamer v13.1.0 запущен")
    logging.info("="*50)

# ============================================================================
# GUI
# ============================================================================

class FileRenamerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_window()
        self.table_path = tk.StringVar()
        self.folder_path = tk.StringVar()
        self.dry_run_var = tk.BooleanVar(value=CONFIG['dry_run']['default'])
        self.status_var = tk.StringVar(value="Готов к работе")
        self.table_processor: Optional[TableProcessor] = None
        self.file_renamer: Optional[FileRenamer] = None
        self._create_widgets()
        self._create_status_bar()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.logger.info("GUI инициализирован")

    def _setup_window(self):
        cfg = CONFIG['window']
        self.root.title(cfg['title'])
        self.root.geometry(f"{cfg['width']}x{cfg['height']}")
        self.root.resizable(cfg['resizable'], cfg['resizable'])
        self._center_window(cfg['width'], cfg['height'])
        self._setup_styles()

    def _center_window(self, width, height):
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _setup_styles(self):
        style = ttk.Style()
        fonts, colors = CONFIG['fonts'], CONFIG['colors']
        style.configure('Title.TLabel', font=fonts['title'])
        style.configure('Header.TLabel', font=fonts['header'])
        style.configure('Success.TLabel', foreground=colors['success'])
        style.configure('Error.TLabel', foreground=colors['error'])

    def _create_widgets(self):
        ttk.Label(self.root, text="📁 " + CONFIG['window']['title'],
                 style='Title.TLabel').pack(pady=15)

        # Info panel
        info_frame = tk.Frame(self.root, bg=CONFIG['colors']['info_bg'],
                             relief="solid", borderwidth=1)
        info_frame.pack(fill="x", padx=20, pady=(0,10))
        tk.Label(info_frame, text=(
            "📋 ФОРМАТ РАБОТЫ:\n"
            "1. Файлы сортируются ПО АЛФАВИТУ (A-Z, А-Я)\n"
            "2. Первый файл → первое имя из таблицы\n"
            "3. 🔄 ДУБЛИКАТЫ: первый раз без номера, затем (1), (2)\n"
            "4. 📎 К имени добавляется _TZ перед расширением\n"
            "5. ❗ В таблице НЕТ строки заголовка\n"
            "6. ✨ Недопустимые символы заменяются на '_'"
        ), font=CONFIG['fonts']['normal'], bg=CONFIG['colors']['info_bg'],
        justify="left", padx=10, pady=10).pack()

        # Table section
        table_frame = ttk.LabelFrame(self.root, text="1. Выберите таблицу")
        table_frame.pack(fill="x", padx=20, pady=10)
        ttk.Label(table_frame, text="Путь:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(table_frame, textvariable=self.table_path, width=55).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Button(table_frame, text="Обзор...", command=self._browse_table,
                  width=10).grid(row=0, column=2, padx=5, pady=5)

        # Folder section
        folder_frame = ttk.LabelFrame(self.root, text="2. Выберите папку")
        folder_frame.pack(fill="x", padx=20, pady=10)
        ttk.Label(folder_frame, text="Путь:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=55).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Button(folder_frame, text="Обзор...", command=self._browse_folder,
                  width=10).grid(row=0, column=2, padx=5, pady=5)

        # Options
        options_frame = ttk.LabelFrame(self.root, text="3. Опции")
        options_frame.pack(fill="x", padx=20, pady=10)
        ttk.Checkbutton(options_frame,
            text="🔍 Режим предпросмотра (Dry Run)",
            variable=self.dry_run_var).pack(padx=10, pady=5, anchor="w")
        tk.Label(options_frame,
            text=f"✨ Суффикс: {CONFIG['file_suffix']}",
            font=CONFIG['fonts']['small'], fg='blue').pack(padx=10, pady=(0,5), anchor="w")

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)
        self.run_button = ttk.Button(button_frame, text="🚀 НАЧАТЬ",
            command=self._start_renaming_thread, width=25)
        self.run_button.pack(side="left", padx=5)
        self.preview_button = ttk.Button(button_frame, text="👁️ ПРЕДПРОСМОТР",
            command=self._preview_renaming, width=20)
        self.preview_button.pack(side="left", padx=5)

        # Log
        log_frame = ttk.LabelFrame(self.root, text="Лог")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text = tk.Text(text_frame, height=12, wrap="word",
                               font=CONFIG['fonts']['log'])
        scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_frame = tk.Frame(log_frame)
        btn_frame.pack(fill="x", padx=5, pady=(0,5))
        ttk.Button(btn_frame, text="Очистить", command=self._clear_log, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Копировать", command=self._copy_log, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Экспорт", command=self._export_log, width=12).pack(side="left", padx=5)

    def _create_status_bar(self):
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken",
                 anchor="w").pack(side="bottom", fill="x")

    def _browse_table(self):
        filename = filedialog.askopenfilename(title="Выберите таблицу",
                                             filetypes=CONFIG['table_formats'])
        if filename:
            self.table_path.set(filename)
            self._log(f"📋 Таблица: {os.path.basename(filename)}")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку")
        if folder:
            self.folder_path.set(folder)
            self._log(f"📁 Папка: {os.path.basename(folder)}")

    def _log(self, message: str):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update()

    def _clear_log(self):
        self.log_text.delete(1.0, "end")

    def _copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get(1.0, "end"))
        self._log("📋 Скопировано")

    def _export_log(self):
        try:
            log_file = filedialog.asksaveasfilename(
                title="Сохранить лог", defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if log_file:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, "end"))
                self._log(f"📁 Сохранено: {os.path.basename(log_file)}")
        except Exception as e:
            self._log(f"❌ Ошибка: {str(e)}")

    def _preview_renaming(self):
        original = self.dry_run_var.get()
        self.dry_run_var.set(True)
        self._start_renaming()
        self.dry_run_var.set(original)

    def _start_renaming_thread(self):
        threading.Thread(target=self._start_renaming, daemon=True).start()

    def _start_renaming(self):
        table, folder = self.table_path.get(), self.folder_path.get()
        if not table or not folder:
            messagebox.showerror("Ошибка", "Выберите таблицу и папку!")
            return
        if not os.path.exists(table) or not os.path.exists(folder):
            messagebox.showerror("Ошибка", "Файл или папка не найдены!")
            return

        dry_run = self.dry_run_var.get()
        mode = "ПРЕДПРОСМОТР" if dry_run else "ПЕРЕИМЕНОВАНИЕ"

        confirm_text = (
            f"{'🔍 РЕЖИМ ПРЕДПРОСМОТРА' if dry_run else '⚠️ НАЧАТЬ'}\n\n"
            f"Таблица: {os.path.basename(table)}\n"
            f"Папка: {os.path.basename(folder)}\n"
            f"Суффикс: {CONFIG['file_suffix']}\n\n"
            f"{'Файлы НЕ будут изменены' if dry_run else 'Сделайте резервную копию!'}"
        )

        if not messagebox.askyesno("Подтверждение", confirm_text):
            return

        self._log("\n" + "="*70)
        self._log(f"🚀 {mode}")
        self._log("="*70)

        try:
            self.run_button.config(state="disabled")
            self.preview_button.config(state="disabled")
            self.status_var.set(f"{mode}...")

            self._log("\n📊 Загрузка таблицы...")
            self.table_processor = TableProcessor(table)
            analysis = self.table_processor.analyze_content()

            self._log(f"   Строк: {analysis['total_rows']}")
            self._log(f"   Действительных имен: {analysis['valid_count']}")

            if analysis['valid_count'] == 0:
                messagebox.showerror("Ошибка", "Нет действительных имен!")
                return

            self._log("\n📝 Первые 5 имен:")
            for idx, name in self.table_processor.get_preview(5):
                self._log(f"   {idx}. {name}")

            if analysis['duplicates_original']:
                self._log("\n🔄 Дубликаты в таблице:")
                for name, count in list(analysis['duplicates_original'].items())[:5]:
                    self._log(f"   '{name}' - {count}x")

            self._log("\n📁 Анализ папки...")
            self.file_renamer = FileRenamer(folder, dry_run=dry_run)
            self._log(f"   Всего файлов: {len(self.file_renamer.files)}")

            extensions = self.file_renamer.get_file_statistics()
            self._log("\n📎 Расширения:")
            for ext, count in sorted(extensions.items())[:5]:
                self._log(f"   {ext}: {count}")

            self._log("\n🔄 Подготовка...")
            names = analysis['valid_names'].tolist()
            operations = self.file_renamer.prepare_operations(names)

            pending = [op for op in operations if op.status == 'pending']
            errors = [op for op in operations if op.status == 'error']
            skipped = [op for op in operations if op.status == 'skipped']

            self._log(f"   Будет переименовано: {len(pending)}")
            if errors: self._log(f"   Ошибок: {len(errors)}")
            if skipped: self._log(f"   Пропущено: {len(skipped)}")

            self._log("\n📋 Примеры:")
            for op in operations[:5]:
                if op.status == 'pending':
                    self._log(f"   [{op.index}] {op.old_path.name} → {op.new_name}")

            self._log(f"\n{'🔍 ПРЕДПРОСМОТР' if dry_run else '⚡ ВЫПОЛНЕНИЕ'}:")
            stats = self.file_renamer.execute_operations()

            success_count = 0
            for op in operations:
                if op.status == 'success' and op.new_name:
                    success_count += 1
                    prefix = "[DRY]" if dry_run else "✅"
                    self._log(f"{prefix} [{op.index}] {op.old_path.name} → {op.new_name}")
                    if success_count >= 10:
                        remaining = len([o for o in operations if o.status=='success']) - 10
                        if remaining > 0:
                            self._log(f"   ... и еще {remaining}")
                        break

            self._log("\n" + "="*70)
            self._log("🏁 ИТОГИ")
            self._log("="*70)
            self._log(f"✅ Успешно: {stats['success']}")
            self._log(f"❌ Ошибок: {stats['error']}")
            self._log(f"⏹️ Пропущено: {stats['skipped']}")

            duplicates = self.file_renamer.get_duplicate_operations()
            if duplicates:
                self._log(f"🔄 Дубликатов: {len(duplicates)}")

            self._log(f"📎 Суффикс: {CONFIG['file_suffix']}")
            if dry_run:
                self._log("\n🔍 ПРЕДПРОСМОТР - файлы не изменены")

            self.status_var.set(f"Готово! ✅{stats['success']} ❌{stats['error']} ⏹️{stats['skipped']}")

            result = (
                f"{'🔍 ПРЕДПРОСМОТР' if dry_run else '🏁 ГОТОВО'}\n\n"
                f"✅ Успешно: {stats['success']}\n"
                f"❌ Ошибок: {stats['error']}\n"
                f"⏹️ Пропущено: {stats['skipped']}\n\n"
                f"📎 Суффикс {CONFIG['file_suffix']}"
            )
            if dry_run:
                result += "\n\n💡 Снимите 'Dry Run' для переименования"

            messagebox.showinfo("Готово", result)

        except Exception as e:
            self._log(f"\n❌ Ошибка: {str(e)}")
            self.logger.error(f"Ошибка: {str(e)}", exc_info=True)
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.run_button.config(state="normal")
            self.preview_button.config(state="normal")

    def _on_closing(self):
        if messagebox.askokcancel("Выход", "Закрыть программу?"):
            self.logger.info("Закрыто пользователем")
            self.root.destroy()

def main():
    setup_logging()
    root = tk.Tk()
    app = FileRenamerGUI(root)
    logging.info("Запуск mainloop")
    root.mainloop()
    logging.info("Завершено")

if __name__ == "__main__":
    main()
