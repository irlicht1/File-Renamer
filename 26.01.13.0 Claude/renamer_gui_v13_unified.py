# -*- coding: utf-8 -*-
"""
Программа для переименования файлов по таблице
Графический интерфейс - версия 13.0 (улучшенная)

Особенности:
- Модульная архитектура
- Санитизация имен файлов
- Профессиональное логирование
- Dry-run режим
- Специфичная обработка ошибок
- Добавление суффикса _AS к именам файлов
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, List, Any, Tuple
import re
from collections import defaultdict, Counter
from dataclasses import dataclass
import threading

# Проверка pandas
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
    # Настройки окна
    'window': {
        'width': 750,
        'height': 600,
        'title': 'Переименование файлов по таблице v13.0',
        'resizable': False
    },

    # Настройки шрифтов
    'fonts': {
        'title': ('Arial', 14, 'bold'),
        'header': ('Arial', 10, 'bold'),
        'normal': ('Arial', 9),
        'log': ('Consolas', 9),
        'small': ('Arial', 8)
    },

    # Настройки логирования
    'logging': {
        'file': 'file_renamer.log',
        'max_bytes': 10 * 1024 * 1024,  # 10 MB
        'backup_count': 3,
        'format': '%(asctime)s - %(levelname)s - %(message)s'
    },

    # Настройки отображения
    'display': {
        'max_preview_items': 20,
        'max_log_lines': 1000
    },

    # Цвета
    'colors': {
        'info_bg': '#f0f8ff',
        'warning_bg': '#fff0f0',
        'success': 'green',
        'error': 'red'
    },

    # Поддерживаемые форматы таблиц
    'table_formats': [
        ('Excel files', '*.xlsx *.xls'),
        ('CSV files', '*.csv'),
        ('All files', '*.*')
    ],

    # Недопустимые символы в именах файлов (Windows)
    'invalid_chars': '<>:"/\\|?*',

    # Суффикс для добавления к именам файлов
    'file_suffix': '_AS',

    # Настройки dry-run
    'dry_run': {
        'enabled': True,
        'default': False
    }
}

# ============================================================================
# ИСКЛЮЧЕНИЯ
# ============================================================================

class FileRenamerError(Exception):
    """Базовое исключение для File Renamer"""
    pass

class TableError(FileRenamerError):
    """Ошибки при работе с таблицей"""
    pass

class EmptyTableError(TableError):
    """Таблица пуста или не содержит действительных имен"""
    pass

class FileOperationError(FileRenamerError):
    """Ошибки при операциях с файлами"""
    pass

class InvalidFileNameError(FileRenamerError):
    """Недопустимое имя файла"""
    pass

# ============================================================================
# УТИЛИТЫ
# ============================================================================

logger = logging.getLogger(__name__)

def sanitize_filename(name: str) -> str:
    """
    Удаляет недопустимые символы из имени файла

    Args:
        name: Исходное имя файла

    Returns:
        Очищенное имя файла
    """
    if not name or not isinstance(name, str):
        raise InvalidFileNameError("Имя файла не может быть пустым")

    # Удаляем недопустимые символы
    invalid_chars = CONFIG['invalid_chars']
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')

    # Удаляем лишние пробелы
    sanitized = sanitized.strip()

    # Удаляем точки в конце (Windows не позволяет)
    sanitized = sanitized.rstrip('.')

    if not sanitized:
        raise InvalidFileNameError(f"Имя файла '{name}' содержит только недопустимые символы")

    return sanitized

def extract_base_name(name: str) -> str:
    """
    Извлекает базовое имя, удаляя существующий номер в скобках

    Args:
        name: Имя с возможным номером

    Returns:
        Базовое имя без номера
    """
    # Удаляем номер в скобках в конце строки
    pattern = r'\s*\(\d+\)$'
    base_name = re.sub(pattern, '', str(name))
    return base_name.strip()

def format_size(bytes_size: int) -> str:
    """Форматирует размер в человекочитаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

# ============================================================================
# ПРОЦЕССОР ТАБЛИЦ
# ============================================================================

class TableProcessor:
    """Класс для обработки таблиц с именами файлов"""

    def __init__(self, table_path: str):
        self.table_path = Path(table_path)
        self.df = None
        self.names = None
        self._load_table()

    def _load_table(self) -> None:
        """Загружает таблицу из файла"""
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
        """Возвращает только действительные имена"""
        non_empty = self.names.dropna()
        non_empty_str = non_empty.astype(str).str.strip()
        valid = non_empty_str[non_empty_str != '']

        try:
            valid = valid.apply(sanitize_filename)
        except Exception as e:
            logging.warning(f"Ошибка санитизации имен: {str(e)}")

        return valid

    def analyze_content(self) -> Dict[str, Any]:
        """Анализирует содержимое таблицы"""
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
            'total_rows': total_rows,
            'empty_nan': int(empty_nan),
            'whitespace_only': int(whitespace_only),
            'valid_names': valid_names,
            'valid_count': len(valid_names),
            'duplicates_original': duplicates_info,
            'unique_names': len(set(valid_names))
        }

    def get_preview(self, max_items: int = 5) -> List[tuple]:
        """Возвращает предварительный просмотр таблицы"""
        preview = []
        for i, value in enumerate(self.names.head(max_items)):
            if pd.isna(value):
                preview.append((i + 1, "[ПУСТО]"))
            else:
                preview.append((i + 1, str(value)))
        return preview

# ============================================================================
# ПЕРЕИМЕНОВАНИЕ ФАЙЛОВ
# ============================================================================

@dataclass
class RenameOperation:
    """Класс для хранения информации об операции переименования"""
    index: int
    old_path: Path
    new_name: str
    status: str  # 'pending', 'success', 'error', 'skipped'
    error_message: Optional[str] = None
    is_duplicate: bool = False
    duplicate_number: Optional[int] = None

class FileRenamer:
    """Класс для переименования файлов"""

    def __init__(self, folder_path: str, dry_run: bool = False):
        self.folder_path = Path(folder_path)
        self.dry_run = dry_run
        self.operations: List[RenameOperation] = []
        self.files: List[Path] = []
        self._load_files()

    def _load_files(self) -> None:
        """Загружает и сортирует список файлов"""
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Папка не найдена: {self.folder_path}")

        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"Это не папка: {self.folder_path}")

        self.files = [item for item in self.folder_path.iterdir() if item.is_file()]
        self.files.sort(key=lambda x: x.name.lower())

        logging.info(f"Загружено {len(self.files)} файлов из {self.folder_path}")

    def get_file_statistics(self) -> Dict[str, int]:
        """Возвращает статистику по файлам"""
        extensions = {}
        for file_path in self.files:
            ext = file_path.suffix.lower()
            extensions[ext if ext else '[без расширения]'] = extensions.get(ext, 0) + 1
        return extensions

    def prepare_operations(self, new_names: List[str]) -> List[RenameOperation]:
        """Подготавливает операции переименования с добавлением суффикса _AS"""
        self.operations = []

        base_name_counter = defaultdict(int)
        used_final_names = set()

        files_to_process = min(len(self.files), len(new_names))
        suffix = CONFIG['file_suffix']  # _AS

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
                temp_final_name = f"{base_name} ({base_name_counter[base_name] - 1}_{suffix_counter})"
                suffix_counter += 1

            final_name_without_ext = temp_final_name

            # ДОБАВЛЯЕМ СУФФИКС _AS ПЕРЕД РАСШИРЕНИЕМ
            final_name_with_ext = final_name_without_ext + suffix + original_extension

            used_final_names.add(final_name_without_ext)

            new_path = self.folder_path / final_name_with_ext

            if new_path.exists() and new_path != file_path:
                operation = RenameOperation(
                    index=i + 1,
                    old_path=file_path,
                    new_name=final_name_with_ext,
                    status='error',
                    error_message='Файл с таким именем уже существует',
                    is_duplicate=is_duplicate,
                    duplicate_number=duplicate_num
                )
            else:
                operation = RenameOperation(
                    index=i + 1,
                    old_path=file_path,
                    new_name=final_name_with_ext,
                    status='pending',
                    is_duplicate=is_duplicate,
                    duplicate_number=duplicate_num
                )

            self.operations.append(operation)

        for i in range(files_to_process, len(self.files)):
            operation = RenameOperation(
                index=i + 1,
                old_path=self.files[i],
                new_name='',
                status='skipped',
                error_message='Не хватило имен в таблице'
            )
            self.operations.append(operation)

        logging.info(f"Подготовлено {len(self.operations)} операций")
        return self.operations

    def execute_operations(self) -> Dict[str, int]:
        """Выполняет подготовленные операции переименования"""
        stats = {'success': 0, 'error': 0, 'skipped': 0}

        for operation in self.operations:
            if operation.status == 'skipped':
                stats['skipped'] += 1
                continue

            if operation.status == 'error':
                stats['error'] += 1
                continue

            try:
                new_path = self.folder_path / operation.new_name

                if self.dry_run:
                    operation.status = 'success'
                    logging.info(f"[DRY RUN] {operation.old_path.name} -> {operation.new_name}")
                else:
                    operation.old_path.rename(new_path)
                    operation.status = 'success'
                    logging.info(f"Переименован: {operation.old_path.name} -> {operation.new_name}")

                stats['success'] += 1

            except PermissionError as e:
                operation.status = 'error'
                operation.error_message = f"Нет доступа: {str(e)}"
                stats['error'] += 1
                logging.error(f"Ошибка доступа: {operation.old_path.name}")

            except OSError as e:
                operation.status = 'error'
                operation.error_message = f"Ошибка ОС: {str(e)}"
                stats['error'] += 1
                logging.error(f"Ошибка ОС: {operation.old_path.name} - {str(e)}")

            except Exception as e:
                operation.status = 'error'
                operation.error_message = str(e)
                stats['error'] += 1
                logging.error(f"Неожиданная ошибка: {operation.old_path.name} - {str(e)}")

        return stats

    def get_operations_by_status(self, status: str) -> List[RenameOperation]:
        """Возвращает операции с заданным статусом"""
        return [op for op in self.operations if op.status == status]

    def get_duplicate_operations(self) -> List[RenameOperation]:
        """Возвращает операции с дубликатами"""
        return [op for op in self.operations if op.is_duplicate]

# ============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================================

def setup_logging():
    """Настраивает систему логирования"""
    log_config = CONFIG['logging']

    file_handler = RotatingFileHandler(
        log_config['file'],
        maxBytes=log_config['max_bytes'],
        backupCount=log_config['backup_count'],
        encoding='utf-8'
    )
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
    logging.info("File Renamer v13.0 запущен")
    logging.info("="*50)

# ============================================================================
# ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ============================================================================

class FileRenamerGUI:
    """Графический интерфейс для переименования файлов"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = logging.getLogger(self.__class__.__name__)

        self._setup_window()

        # Переменные
        self.table_path = tk.StringVar()
        self.folder_path = tk.StringVar()
        self.dry_run_var = tk.BooleanVar(value=CONFIG['dry_run']['default'])
        self.status_var = tk.StringVar(value="Готов к работе")

        # Процессоры
        self.table_processor: Optional[TableProcessor] = None
        self.file_renamer: Optional[FileRenamer] = None

        # Создание интерфейса
        self._create_widgets()
        self._create_status_bar()

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.logger.info("GUI инициализирован")

    def _setup_window(self) -> None:
        """Настройка главного окна"""
        window_config = CONFIG['window']

        self.root.title(window_config['title'])
        self.root.geometry(f"{window_config['width']}x{window_config['height']}")
        self.root.resizable(window_config['resizable'], window_config['resizable'])

        self._center_window(window_config['width'], window_config['height'])
        self._setup_styles()

    def _center_window(self, width: int, height: int) -> None:
        """Центрирует окно на экране"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _setup_styles(self) -> None:
        """Настраивает стили виджетов"""
        style = ttk.Style()
        fonts = CONFIG['fonts']
        colors = CONFIG['colors']

        style.configure('Title.TLabel', font=fonts['title'])
        style.configure('Header.TLabel', font=fonts['header'])
        style.configure('Success.TLabel', foreground=colors['success'])
        style.configure('Error.TLabel', foreground=colors['error'])

    def _create_widgets(self) -> None:
        """Создает все виджеты интерфейса"""
        self._create_header()
        self._create_info_panel()
        self._create_table_section()
        self._create_folder_section()
        self._create_options_section()
        self._create_action_buttons()
        self._create_log_section()

    def _create_header(self) -> None:
        """Создает заголовок"""
        title_label = ttk.Label(
            self.root,
            text="📁 " + CONFIG['window']['title'],
            style='Title.TLabel'
        )
        title_label.pack(pady=15)

    def _create_info_panel(self) -> None:
        """Создает информационную панель"""
        colors = CONFIG['colors']
        fonts = CONFIG['fonts']

        info_frame = tk.Frame(
            self.root,
            bg=colors['info_bg'],
            relief="solid",
            borderwidth=1
        )
        info_frame.pack(fill="x", padx=20, pady=(0, 10))

        info_text = (
            "📋 ФОРМАТ РАБОТЫ:\n"
            "1. Файлы сортируются ПО АЛФАВИТУ (A-Z, А-Я)\n"
            "2. Первый файл → первое имя из таблицы\n"
            "3. 🔄 ДУБЛИКАТЫ: первый раз без номера, затем (1), (2), ...\n"
            "4. 📎 К имени добавляется _AS перед расширением\n"
            "5. ❗ В таблице НЕТ строки заголовка (данные с 1-й строки)\n"
            "6. ✨ Недопустимые символы заменяются на '_'"
        )

        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=fonts['normal'],
            bg=colors['info_bg'],
            justify="left",
            padx=10,
            pady=10
        )
        info_label.pack()

    def _create_table_section(self) -> None:
        """Создает секцию выбора таблицы"""
        table_frame = ttk.LabelFrame(
            self.root,
            text="1. Выберите таблицу (без строки заголовка)"
        )
        table_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(table_frame, text="Путь к таблице:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )

        table_entry = ttk.Entry(
            table_frame,
            textvariable=self.table_path,
            width=55
        )
        table_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(
            table_frame,
            text="Обзор...",
            command=self._browse_table,
            width=10
        ).grid(row=0, column=2, padx=5, pady=5)

    def _create_folder_section(self) -> None:
        """Создает секцию выбора папки"""
        folder_frame = ttk.LabelFrame(
            self.root,
            text="2. Выберите папку с файлами"
        )
        folder_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(folder_frame, text="Путь к папке:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )

        folder_entry = ttk.Entry(
            folder_frame,
            textvariable=self.folder_path,
            width=55
        )
        folder_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(
            folder_frame,
            text="Обзор...",
            command=self._browse_folder,
            width=10
        ).grid(row=0, column=2, padx=5, pady=5)

    def _create_options_section(self) -> None:
        """Создает секцию опций"""
        options_frame = ttk.LabelFrame(self.root, text="3. Опции")
        options_frame.pack(fill="x", padx=20, pady=10)

        dry_run_check = ttk.Checkbutton(
            options_frame,
            text="🔍 Режим предпросмотра (Dry Run) - показать изменения без переименования",
            variable=self.dry_run_var
        )
        dry_run_check.pack(padx=10, pady=5, anchor="w")

        # Информация о суффиксе
        suffix_label = tk.Label(
            options_frame,
            text=f"✨ К именам файлов будет добавлен суффикс: {CONFIG['file_suffix']}",
            font=CONFIG['fonts']['small'],
            fg='blue'
        )
        suffix_label.pack(padx=10, pady=(0, 5), anchor="w")

    def _create_action_buttons(self) -> None:
        """Создает кнопки действий"""
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)

        self.run_button = ttk.Button(
            button_frame,
            text="🚀 НАЧАТЬ ПЕРЕИМЕНОВАНИЕ",
            command=self._start_renaming_thread,
            width=30
        )
        self.run_button.pack(side="left", padx=5)

        self.preview_button = ttk.Button(
            button_frame,
            text="👁️ ПРЕДПРОСМОТР",
            command=self._preview_renaming,
            width=20
        )
        self.preview_button.pack(side="left", padx=5)

    def _create_log_section(self) -> None:
        """Создает секцию логов"""
        log_frame = ttk.LabelFrame(self.root, text="Лог выполнения")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.log_text = tk.Text(
            text_frame,
            height=12,
            wrap="word",
            font=CONFIG['fonts']['log']
        )
        scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = tk.Frame(log_frame)
        button_frame.pack(fill="x", padx=5, pady=(0, 5))

        ttk.Button(
            button_frame,
            text="Очистить",
            command=self._clear_log,
            width=12
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Копировать",
            command=self._copy_log,
            width=12
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Экспорт",
            command=self._export_log,
            width=12
        ).pack(side="left", padx=5)

    def _create_status_bar(self) -> None:
        """Создает статус-бар"""
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w"
        )
        status_bar.pack(side="bottom", fill="x")

    def _browse_table(self) -> None:
        """Выбор файла таблицы"""
        filename = filedialog.askopenfilename(
            title="Выберите файл таблицы",
            filetypes=CONFIG['table_formats']
        )

        if filename:
            self.table_path.set(filename)
            self._log(f"📋 Выбрана таблица: {os.path.basename(filename)}")

    def _browse_folder(self) -> None:
        """Выбор папки с файлами"""
        folder = filedialog.askdirectory(
            title="Выберите папку с файлами"
        )

        if folder:
            self.folder_path.set(folder)
            self._log(f"📁 Выбрана папка: {os.path.basename(folder)}")

    def _log(self, message: str) -> None:
        """Добавление сообщения в лог"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update()

    def _clear_log(self) -> None:
        """Очистка лога"""
        self.log_text.delete(1.0, "end")

    def _copy_log(self) -> None:
        """Копирование лога в буфер обмена"""
        log_content = self.log_text.get(1.0, "end")
        self.root.clipboard_clear()
        self.root.clipboard_append(log_content)
        self._log("📋 Лог скопирован в буфер обмена")

    def _export_log(self) -> None:
        """Экспорт лога в файл"""
        try:
            log_file = filedialog.asksaveasfilename(
                title="Сохранить лог",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )

            if log_file:
                with open(log_file, 'w', encoding='utf-8') as f:
                    log_content = self.log_text.get(1.0, "end")
                    f.write(log_content)
                self._log(f"📁 Лог сохранен: {os.path.basename(log_file)}")
        except Exception as e:
            self._log(f"❌ Ошибка экспорта: {str(e)}")

    def _preview_renaming(self) -> None:
        """Предпросмотр переименования"""
        original_dry_run = self.dry_run_var.get()
        self.dry_run_var.set(True)
        self._start_renaming()
        self.dry_run_var.set(original_dry_run)

    def _start_renaming_thread(self) -> None:
        """Запуск переименования в отдельном потоке"""
        thread = threading.Thread(target=self._start_renaming, daemon=True)
        thread.start()

    def _start_renaming(self) -> None:
        """Основная логика переименования"""
        table = self.table_path.get()
        folder = self.folder_path.get()

        if not table or not folder:
            messagebox.showerror("Ошибка", "Выберите таблицу и папку!")
            return

        if not os.path.exists(table):
            messagebox.showerror("Ошибка", f"Файл не найден: {table}")
            return

        if not os.path.exists(folder):
            messagebox.showerror("Ошибка", f"Папка не найдена: {folder}")
            return

        dry_run = self.dry_run_var.get()
        mode_text = "ПРЕДПРОСМОТР (DRY RUN)" if dry_run else "ПЕРЕИМЕНОВАНИЕ"

        confirm_text = (
            f"{'🔍 РЕЖИМ ПРЕДПРОСМОТРА' if dry_run else '⚠️ НАЧАТЬ ПЕРЕИМЕНОВАНИЕ'}\n\n"
            f"Таблица: {os.path.basename(table)}\n"
            f"Папка: {os.path.basename(folder)}\n\n"
            f"📎 К именам будет добавлен суффикс: {CONFIG['file_suffix']}\n\n"
            f"{'Файлы НЕ будут переименованы, только показан результат.' if dry_run else 'Файлы будут переименованы! Рекомендуется сделать резервную копию.'}"
        )

        if not messagebox.askyesno("Подтверждение", confirm_text):
            return

        self._log("\n" + "="*70)
        self._log(f"🚀 {mode_text}")
        self._log("="*70)

        try:
            self.run_button.config(state="disabled")
            self.preview_button.config(state="disabled")
            self.status_var.set(f"Выполняется {mode_text.lower()}...")

            # Загрузка таблицы
            self._log("\n📊 Загрузка таблицы...")
            self.table_processor = TableProcessor(table)
            analysis = self.table_processor.analyze_content()

            self._log(f"   Всего строк: {analysis['total_rows']}")
            self._log(f"   Действительных имен: {analysis['valid_count']}")

            if analysis['valid_count'] == 0:
                messagebox.showerror("Ошибка", "В таблице нет действительных имен!")
                return

            # Показываем превью
            self._log("\n📝 Первые 5 имен из таблицы:")
            preview = self.table_processor.get_preview(5)
            for idx, name in preview:
                self._log(f"   {idx}. {name}")

            if analysis['duplicates_original']:
                self._log("\n🔄 Обнаружены дубликаты в таблице:")
                for name, count in list(analysis['duplicates_original'].items())[:5]:
                    self._log(f"   '{name}' - встречается {count} раз")

            # Загрузка файлов
            self._log("\n📁 Анализ папки с файлами...")
            self.file_renamer = FileRenamer(folder, dry_run=dry_run)

            self._log(f"   Всего файлов: {len(self.file_renamer.files)}")

            # Статистика расширений
            extensions = self.file_renamer.get_file_statistics()
            self._log("\n📎 Расширения файлов:")
            for ext, count in sorted(extensions.items())[:5]:
                self._log(f"   {ext}: {count} файлов")

            # Подготовка операций
            self._log("\n🔄 Подготовка операций переименования...")
            names = analysis['valid_names'].tolist()
            operations = self.file_renamer.prepare_operations(names)

            pending_ops = [op for op in operations if op.status == 'pending']
            error_ops = [op for op in operations if op.status == 'error']
            skipped_ops = [op for op in operations if op.status == 'skipped']

            self._log(f"   Будет переименовано: {len(pending_ops)}")
            if error_ops:
                self._log(f"   ⚠️ Ошибок: {len(error_ops)}")
            if skipped_ops:
                self._log(f"   ⏹️ Пропущено: {len(skipped_ops)}")

            # Показываем примеры переименования
            self._log("\n📋 Примеры переименования:")
            for op in operations[:5]:
                if op.status == 'pending':
                    self._log(f"   [{op.index:3d}] {op.old_path.name}")
                    self._log(f"         → {op.new_name}")
                    if op.is_duplicate:
                        self._log(f"         🔄 Дубликат #{op.duplicate_number}")

            # Выполнение операций
            self._log(f"\n{'🔍 ПРЕДПРОСМОТР' if dry_run else '⚡ ВЫПОЛНЕНИЕ'}:")
            self._log("-" * 70)

            stats = self.file_renamer.execute_operations()

            # Детальный вывод результатов
            success_count = 0
            for op in operations:
                if op.status == 'success' and op.new_name:
                    success_count += 1
                    prefix = "✅ [DRY]" if dry_run else "✅"
                    self._log(f"{prefix} [{op.index:3d}] {op.old_path.name} → {op.new_name}")
                    if success_count >= 10 and len(operations) > 15:
                        remaining = len([o for o in operations if o.status == 'success']) - success_count
                        if remaining > 0:
                            self._log(f"   ... и еще {remaining} файлов успешно обработано")
                        break
                elif op.status == 'error':
                    self._log(f"❌ [{op.index:3d}] {op.old_path.name} - {op.error_message}")
                elif op.status == 'skipped':
                    if skipped_ops.index(op) < 3:  # Показываем только первые 3
                        self._log(f"⏹️ [{op.index:3d}] {op.old_path.name} - пропущен")

            # Итоги
            self._log("\n" + "="*70)
            self._log("🏁 ИТОГИ")
            self._log("="*70)
            self._log(f"✅ Успешно: {stats['success']}")
            self._log(f"❌ Ошибок: {stats['error']}")
            self._log(f"⏹️ Пропущено: {stats['skipped']}")

            duplicates = self.file_renamer.get_duplicate_operations()
            if duplicates:
                self._log(f"🔄 Обработано дубликатов: {len(duplicates)}")

            self._log(f"📎 Суффикс добавлен: {CONFIG['file_suffix']}")

            if dry_run:
                self._log("\n🔍 РЕЖИМ ПРЕДПРОСМОТРА - файлы не были изменены")

            self.status_var.set(
                f"Готово! Успешно: {stats['success']}, "
                f"Ошибок: {stats['error']}, "
                f"Пропущено: {stats['skipped']}"
            )

            result_msg = (
                f"{'🔍 ПРЕДПРОСМОТР ЗАВЕРШЕН' if dry_run else '🏁 ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО'}\n\n"
                f"✅ Успешно: {stats['success']}\n"
                f"❌ Ошибок: {stats['error']}\n"
                f"⏹️ Пропущено: {stats['skipped']}\n\n"
                f"📎 Суффикс {CONFIG['file_suffix']} {'будет добавлен' if dry_run else 'добавлен'} к именам"
            )

            if dry_run:
                result_msg += "\n\n💡 Для фактического переименования снимите галочку 'Dry Run'"

            messagebox.showinfo("Готово", result_msg)

        except EmptyTableError as e:
            self._log(f"\n❌ Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", str(e))

        except TableError as e:
            self._log(f"\n❌ Ошибка таблицы: {str(e)}")
            messagebox.showerror("Ошибка таблицы", str(e))

        except FileNotFoundError as e:
            self._log(f"\n❌ Файл не найден: {str(e)}")
            messagebox.showerror("Ошибка", str(e))

        except Exception as e:
            self._log(f"\n❌ Критическая ошибка: {str(e)}")
            self.logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
            messagebox.showerror("Критическая ошибка", f"Произошла ошибка:\n\n{str(e)}")

        finally:
            self.run_button.config(state="normal")
            self.preview_button.config(state="normal")

    def _on_closing(self) -> None:
        """Обработчик закрытия окна"""
        if messagebox.askokcancel("Выход", "Вы уверены?"):
            self.logger.info("Приложение закрыто пользователем")
            self.root.destroy()

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Основная функция запуска"""
    setup_logging()

    root = tk.Tk()
    app = FileRenamerGUI(root)

    logging.info("Главное окно создано, запуск mainloop")
    root.mainloop()

    logging.info("Приложение завершено")

if __name__ == "__main__":
    main()
