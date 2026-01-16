# -*- coding: utf-8 -*-
"""
Программа для переименования файлов по таблице
Графический интерфейс - версия 12.0 с сохранением оригинального расширения
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import re

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Переименование файлов по таблице v12.0")
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        
        # Центрирование окна
        self.center_window(700, 550)
        
        # Стиль
        self.setup_styles()
        
        # Переменные
        self.table_path = tk.StringVar()
        self.folder_path = tk.StringVar()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Статус бар
        self.create_status_bar()
        
        # Привязка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self, width, height):
        """Центрирование окна на экране"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
    
    def create_widgets(self):
        """Создание виджетов"""
        # Заголовок
        title_label = ttk.Label(
            self.root, 
            text="📁 Переименование файлов по таблице v12.0",
            style='Title.TLabel'
        )
        title_label.pack(pady=15)
        
        # Информация о формате
        info_frame = tk.Frame(self.root, bg="#f0f8ff", relief="solid", borderwidth=1)
        info_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        info_label = tk.Label(
            info_frame,
            text="📋 ФОРМАТ РАБОТЫ:\n" +
                 "1. Файлы сортируются ПО АЛФАВИТУ (A-Z, А-Я)\n" +
                 "2. Первый файл → первое имя из таблицы\n" +
                 "3. И так далее по порядку\n" +
                 "4. 🔄 ДУБЛИКАТЫ: первый раз без номера, затем (1), (2), ...\n" +
                 "5. 📎 Сохраняется оригинальное расширение файла\n" +
                 "6. ❗ ВАЖНО: В таблице НЕТ строки заголовка (данные с 1-й строки)",
            font=('Arial', 9),
            bg="#f0f8ff",
            justify="left",
            padx=10,
            pady=10
        )
        info_label.pack()
        
        # Фрейм для таблицы
        table_frame = ttk.LabelFrame(self.root, text="1. Выберите таблицу (без строки заголовка)")
        table_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(table_frame, text="Путь к таблице:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        table_entry = ttk.Entry(table_frame, textvariable=self.table_path, width=50)
        table_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            table_frame, 
            text="Обзор...", 
            command=self.browse_table,
            width=10
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Примеры
        examples_frame = tk.Frame(table_frame, bg="#fff0f0", relief="solid", borderwidth=1)
        examples_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        examples_label = tk.Label(
            examples_frame,
            text="❗ ТАБЛИЦА БЕЗ СТРОКИ ЗАГОЛОВКА (данные с первой строки):\n" +
                 "A1='видео1', A2='видео2', A3='видео1', A4='документ'\n" +
                 "→ Файл1.jpg → 'видео1.jpg', Файл2.mp4 → 'видео2.mp4', Файл3.pdf → 'видео1 (1).pdf'",
            font=('Arial', 8),
            bg="#fff0f0",
            justify="left",
            padx=5,
            pady=5
        )
        examples_label.pack()
        
        # Фрейм для папки
        folder_frame = ttk.LabelFrame(self.root, text="2. Выберите папку с файлами для переименования")
        folder_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(folder_frame, text="Путь к папке:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=50)
        folder_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            folder_frame, 
            text="Обзор...", 
            command=self.browse_folder,
            width=10
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Кнопка запуска
        self.run_button = ttk.Button(
            self.root,
            text="🚀 НАЧАТЬ ПЕРЕИМЕНОВАНИЕ",
            command=self.start_renaming,
            width=30
        )
        self.run_button.pack(pady=25)
        
        # Область лога
        log_frame = ttk.LabelFrame(self.root, text="Лог выполнения")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Создаем текстовое поле с прокруткой
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(text_frame, height=15, wrap="word", font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Кнопки под логом
        button_frame = tk.Frame(log_frame)
        button_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        ttk.Button(
            button_frame,
            text="Очистить лог",
            command=self.clear_log,
            width=15
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Скопировать лог",
            command=self.copy_log,
            width=15
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Экспорт лога",
            command=self.export_log,
            width=15
        ).pack(side="left", padx=5)
    
    def create_status_bar(self):
        """Создание статус-бара"""
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w"
        )
        status_bar.pack(side="bottom", fill="x")
    
    def browse_table(self):
        """Выбор файла таблицы"""
        filetypes = [
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Выберите файл таблицы (без строки заголовка)",
            filetypes=filetypes
        )
        
        if filename:
            self.table_path.set(filename)
            self.log(f"📋 Выбрана таблица: {os.path.basename(filename)}")
            self.log("   ❗ Предполагается, что в таблице НЕТ строки заголовка")
    
    def browse_folder(self):
        """Выбор папки с файлами"""
        folder = filedialog.askdirectory(
            title="Выберите папку с файлами для переименования"
        )
        
        if folder:
            self.folder_path.set(folder)
            self.log(f"📁 Выбрана папка: {os.path.basename(folder)}")
    
    def log(self, message):
        """Добавление сообщения в лог"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update()
    
    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete(1.0, "end")
    
    def copy_log(self):
        """Копирование лога в буфер обмена"""
        log_content = self.log_text.get(1.0, "end")
        self.root.clipboard_clear()
        self.root.clipboard_append(log_content)
        self.log("📋 Лог скопирован в буфер обмена")
    
    def export_log(self):
        """Экспорт лога в файл"""
        try:
            log_file = filedialog.asksaveasfilename(
                title="Сохранить лог как",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if log_file:
                with open(log_file, 'w', encoding='utf-8') as f:
                    log_content = self.log_text.get(1.0, "end")
                    f.write(log_content)
                self.log(f"📁 Лог экспортирован в: {os.path.basename(log_file)}")
        except Exception as e:
            self.log(f"❌ Ошибка экспорта лога: {str(e)}")
    
    def analyze_table_content(self, new_names_series):
        """Анализ содержимого таблицы"""
        total_rows = len(new_names_series)
        
        # Подсчет пустых и непустых строк
        empty_rows = new_names_series.isna().sum()
        
        # Преобразование в строки и проверка на пустые строки после удаления пробелов
        non_empty = new_names_series.dropna()
        non_empty_str = non_empty.astype(str).str.strip()
        whitespace_only = (non_empty_str == '').sum()
        
        # Действительные имена
        valid_names = non_empty_str[non_empty_str != '']
        
        # Анализ дубликатов в исходных данных
        duplicates_info = {}
        if len(valid_names) > 0:
            name_counts = Counter(valid_names.tolist())
            duplicates_info = {name: count for name, count in name_counts.items() if count > 1}
        
        return {
            'total_rows': total_rows,
            'empty_nan': int(empty_rows),
            'whitespace_only': int(whitespace_only),
            'valid_names': valid_names,
            'valid_count': len(valid_names),
            'duplicates_original': duplicates_info
        }
    
    def extract_base_name(self, name):
        """Извлекает базовое имя, удаляя уже существующий номер в скобках"""
        # Удаляем номер в скобках в конце строки, если он есть
        pattern = r'\s*\(\d+\)$'
        base_name = re.sub(pattern, '', str(name))
        return base_name.strip()
    
    def start_renaming(self):
        """Запуск процесса переименования"""
        table = self.table_path.get()
        folder = self.folder_path.get()
        
        if not table or not folder:
            messagebox.showerror("Ошибка", "Выберите таблицу и папку с файлами!")
            return
        
        if not os.path.exists(table):
            messagebox.showerror("Ошибка", f"Файл таблицы не найден:\n{table}")
            return
        
        if not os.path.exists(folder):
            messagebox.showerror("Ошибка", f"Папка не найдена:\n{folder}")
            return
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите начать переименование файлов?\n\n"
            f"Таблица: {os.path.basename(table)}\n"
            f"Папка: {os.path.basename(folder)}\n\n"
            "📋 ПОРЯДОК РАБОТЫ:\n"
            "1. Файлы сортируются ПО АЛФАВИТУ (A-Z, А-Я)\n"
            "2. Первый файл → первое имя из таблицы\n"
            "3. И так далее по порядку\n"
            "4. 🔄 ДУБЛИКАТЫ: первый раз без номера, затем (1), (2), ...\n"
            "5. 📎 Сохраняется оригинальное расширение файла\n"
            "6. ❗ В таблице НЕТ строки заголовка (чтение с 1-й строки)\n\n"
            "Рекомендуется сделать резервную копию файлов перед началом."
        )
        
        if not confirm:
            return
        
        self.log("\n" + "="*70)
        self.log("🚀 НАЧАЛО ПЕРЕИМЕНОВАНИЯ ФАЙЛОВ (Версия 12.0)")
        self.log("="*70)
        
        try:
            # Блокируем кнопку на время выполнения
            self.run_button.config(state="disabled")
            self.status_var.set("Выполняется переименование...")
            
            # 1. Загружаем таблицу БЕЗ заголовка (header=None)
            self.log("\n📊 ЗАГРУЗКА ТАБЛИЦЫ:")
            self.log("-" * 50)
            self.log("Режим: Строка заголовка НЕТ (header=None)")
            self.log("❗ Данные читаются с ПЕРВОЙ строки таблицы")
            
            if table.lower().endswith('.csv'):
                df = pd.read_csv(table, encoding='utf-8', header=None)
            else:
                df = pd.read_excel(table, header=None)
            
            if len(df.columns) == 0:
                messagebox.showerror("Ошибка", "Таблица пуста!")
                return
            
            # Берем первый столбец
            original_names = df.iloc[:, 0]
            
            self.log(f"Прочитано строк из таблицы: {len(original_names)}")
            
            # Показываем первые несколько строк для проверки
            self.log("\n📝 ПЕРВЫЕ 5 СТРОК ИЗ ТАБЛИЦЫ (начиная с 1-й строки):")
            for i, value in enumerate(original_names.head(5)):
                if pd.isna(value):
                    self.log(f"  Строка {i+1}: [ПУСТО]")
                else:
                    self.log(f"  Строка {i+1}: '{value}'")
            
            # Анализируем содержимое таблицы
            analysis = self.analyze_table_content(original_names)
            
            # Выводим детальную информацию о таблице
            self.log(f"\n📊 АНАЛИЗ ТАБЛИЦЫ:")
            self.log(f"  Всего строк прочитано: {analysis['total_rows']}")
            self.log(f"  Пустых ячеек (NaN): {analysis['empty_nan']}")
            self.log(f"  Строк только с пробелами: {analysis['whitespace_only']}")
            self.log(f"  Действительных имен: {analysis['valid_count']}")
            
            if analysis['valid_count'] == 0:
                messagebox.showerror("Ошибка", "В таблице нет действительных имен для файлов!")
                return
            
            # Показываем информацию о дубликатах в исходных данных
            if analysis['duplicates_original']:
                self.log("\n📝 ДУБЛИКАТЫ В ТАБЛИЦЕ (исходные данные):")
                for name, count in analysis['duplicates_original'].items():
                    self.log(f"  '{name}' - встречается {count} раз")
            
            # Показываем все действительные имена
            self.log("\n📝 ДЕЙСТВИТЕЛЬНЫЕ ИМЕНА (будут использованы):")
            for i, name in enumerate(analysis['valid_names'].head(20)):
                self.log(f"  Имя {i+1:3d}: '{name}'")
            
            if analysis['valid_count'] > 20:
                self.log(f"  ... и еще {analysis['valid_count'] - 20} имен")
            
            new_names = analysis['valid_names']
            
            # 2. Получаем и анализируем файлы в папке
            self.log("\n📁 АНАЛИЗ ПАПКИ С ФАЙЛАМИ:")
            self.log("-" * 50)
            
            folder_path = Path(folder)
            
            # Получаем список всех файлов в папке
            files = []
            for item in os.listdir(folder_path):
                item_path = folder_path / item
                if item_path.is_file():
                    files.append(item_path)
            
            # СОРТИРОВКА ПО АЛФАВИТУ (A-Z, А-Я, регистронезависимо)
            files.sort(key=lambda x: x.name.lower())
            
            if len(files) == 0:
                messagebox.showerror("Ошибка", f"В папке нет файлов:\n{folder}")
                return
            
            self.log(f"Всего файлов в папке: {len(files)}")
            
            # Анализируем типы файлов в папке
            file_extensions = {}
            for file_path in files:
                ext = file_path.suffix.lower()
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
            
            self.log("\n📎 РАСПРЕДЕЛЕНИЕ ФАЙЛОВ ПО РАСШИРЕНИЯМ:")
            for ext, count in sorted(file_extensions.items()):
                if ext:  # Если есть расширение
                    self.log(f"  {ext}: {count} файлов")
                else:
                    self.log(f"  [без расширения]: {count} файлов")
            
            # Показываем все файлы
            self.log("\n📋 ФАЙЛЫ В ПАПКЕ (отсортированы по алфавиту):")
            for i, file_path in enumerate(files[:10]):  # Только первые 10
                self.log(f"  Файл {i+1:3d}: {file_path.name}")
            
            if len(files) > 10:
                self.log(f"  ... и еще {len(files) - 10} файлов")
            
            # 3. Сравниваем количества
            self.log("\n⚖️  СРАВНЕНИЕ КОЛИЧЕСТВ:")
            self.log("-" * 50)
            
            files_count = len(files)
            names_count = len(new_names)
            
            self.log(f"Файлов в папке: {files_count}")
            self.log(f"Действительных имен в таблице: {names_count}")
            
            if files_count != names_count:
                diff = abs(files_count - names_count)
                self.log(f"⚠️  РАЗНИЦА: {diff} {'файлов' if files_count > names_count else 'имен'}")
                
                if files_count > names_count:
                    self.log(f"⚠️  Будет переименовано: {min(files_count, names_count)} из {files_count} файлов")
                    self.log(f"⚠️  Останется без переименования: {diff} файлов")
                    
                    # Предлагаем возможные решения
                    self.log(f"\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
                    self.log(f"  1. Проверьте пустые строки в таблице")
                    self.log(f"  2. Убедитесь, что в таблице достаточно имен")
                    self.log(f"  3. Проверьте, что первая строка таблицы содержит первое имя файла")
                else:
                    self.log(f"⚠️  Будут использованы: {min(files_count, names_count)} из {names_count} имен")
                    self.log(f"⚠️  Не будут использованы: {diff} имен")
            else:
                self.log("✅ Количества совпадают - все файлы будут переименованы")
            
            # 4. Создаем структуры для отслеживания дубликатов
            # Словарь для отслеживания использования базовых имен
            base_name_counter = defaultdict(int)
            # Множество для отслеживания всех использованных финальных имен (без расширения)
            used_final_names = set()
            
            # 5. Переименовываем файлы строго по порядку
            self.log("\n🔄 ПРОЦЕСС ПЕРЕИМЕНОВАНИЯ:")
            self.log("-" * 50)
            self.log("Формат: [Порядковый номер] Старое имя → Новое имя")
            
            success_count = 0
            error_count = 0
            skipped_count = 0
            
            # Определяем сколько файлов будем переименовывать
            files_to_rename = min(len(files), len(new_names))
            
            # Сначала проходим по всем именам, чтобы определить, какие базовые имена будут использоваться
            # и сколько раз каждое из них встречается
            base_names_usage = []
            for i in range(files_to_rename):
                original_name = new_names.iloc[i]
                base_name = self.extract_base_name(original_name)
                base_names_usage.append(base_name)
            
            # Теперь проходим для переименования
            for i in range(files_to_rename):
                file_path = files[i]
                old_name = file_path.name
                original_name = new_names.iloc[i]
                base_name = base_names_usage[i]
                
                # Получаем оригинальное расширение файла
                original_extension = file_path.suffix
                
                # Увеличиваем счетчик для этого базового имени
                base_name_counter[base_name] += 1
                
                # Формируем финальное имя (без расширения)
                if base_name_counter[base_name] == 1:
                    # Первое использование базового имени - без номера
                    final_base_name = base_name
                else:
                    # Повторное использование - добавляем номер
                    final_base_name = f"{base_name} ({base_name_counter[base_name] - 1})"
                
                # Проверяем уникальность финального имени
                # Если такое имя уже используется, добавляем дополнительный суффикс
                temp_final_name = final_base_name
                suffix_counter = 1
                
                while temp_final_name in used_final_names:
                    temp_final_name = f"{base_name} ({base_name_counter[base_name] - 1}_{suffix_counter})"
                    suffix_counter += 1
                
                final_name_without_ext = temp_final_name
                
                # Добавляем оригинальное расширение файла
                final_name_with_extension = final_name_without_ext + original_extension
                
                # Проверяем существование файла с новым именем в файловой системе
                new_path = folder_path / final_name_with_extension
                
                if new_path.exists():
                    # Файл с таким именем уже существует в папке
                    self.log(f"⚠️  [{i+1:3d}] Файл уже существует: {final_name_with_extension}")
                    error_count += 1
                    continue
                
                # Добавляем имя в список использованных (без расширения)
                used_final_names.add(final_name_without_ext)
                
                # Переименовываем файл
                try:
                    file_path.rename(new_path)
                    self.log(f"✅ [{i+1:3d}] {old_name:35} → {final_name_with_extension}")
                    
                    # Показываем дополнительную информацию для дубликатов
                    if base_name_counter[base_name] > 1:
                        self.log(f"     🔄 Дубликат базового имени '{base_name}' (использование #{base_name_counter[base_name]})")
                    
                    success_count += 1
                except Exception as e:
                    self.log(f"❌ [{i+1:3d}] Ошибка: {old_name} → {str(e)[:50]}...")
                    error_count += 1
            
            # Если остались непереименованные файлы
            if files_count > names_count:
                skipped_count = files_count - names_count
                self.log(f"\n⏹️  ФАЙЛЫ БЕЗ ПЕРЕИМЕНОВАНИЯ (не хватило имен):")
                for i in range(names_count, min(names_count + 5, files_count)):
                    self.log(f"  [{i+1:3d}] {files[i].name}")
                if skipped_count > 5:
                    self.log(f"  ... и еще {skipped_count - 5} файлов")
            
            # 6. Выводим итоги
            self.log("\n" + "="*70)
            self.log("🏁 ИТОГИ ПЕРЕИМЕНОВАНИЯ")
            self.log("="*70)
            
            # Информация о дубликатах (обработанных)
            processed_duplicates = {name: count for name, count in base_name_counter.items() if count > 1}
            if processed_duplicates:
                self.log("\n📝 ОБРАБОТАННЫЕ ДУБЛИКАТЫ:")
                for name, count in processed_duplicates.items():
                    self.log(f"  Базовое имя '{name}' - использовано {count} раз:")
                    
                    # Находим все финальные имена для этого базового имени
                    final_names_for_base = [n for n in used_final_names if n.startswith(name)]
                    # Сортируем для красоты
                    final_names_for_base.sort(key=lambda x: (
                        0 if x == name else 
                        int(re.search(r'\((\d+)\)', x).group(1)) if re.search(r'\((\d+)\)$', x) else
                        9999
                    ))
                    
                    for j, final_name in enumerate(final_names_for_base):
                        suffix = ""
                        if final_name == name:
                            suffix = " (без номера)"
                        elif "(" in final_name:
                            match = re.search(r'\((\d+)\)', final_name)
                            if match:
                                suffix = f" (номер {match.group(1)})"
                        self.log(f"     Вариант {j+1}: '{final_name}[расширение]'{suffix}")
            
            # Статистика
            self.log("\n📊 СТАТИСТИКА:")
            self.log(f"  ✅ Успешно переименовано: {success_count} файлов")
            self.log(f"  ❌ Ошибки при переименовании: {error_count} файлов")
            self.log(f"  ⏹️  Пропущено (не хватило имен): {skipped_count} файлов")
            self.log(f"  📁 Всего файлов в папке: {files_count}")
            self.log(f"  📋 Действительных имен в таблице: {names_count}")
            self.log(f"  🔄 Уникальных базовых имен: {len(base_name_counter)}")
            self.log(f"  📎 Сохранено оригинальных расширений: {len(file_extensions)} различных типов")
            
            if processed_duplicates:
                self.log(f"  🔄 Обработано дубликатов: {len(processed_duplicates)} уникальных имен с повторениями")
                total_duplicates = sum(count - 1 for count in processed_duplicates.values())
                self.log(f"  🔄 Всего добавлено суффиксов: {total_duplicates}")
            
            if skipped_count > 0:
                self.log(f"\n💡 РЕКОМЕНДАЦИИ:")
                self.log(f"  1. Проверьте, что в таблице достаточно имен")
                self.log(f"  2. Убедитесь, что нет пустых строк в таблице")
                self.log(f"  3. Проверьте, что первая строка таблицы содержит первое имя файла")
            
            # Сводка по порядку
            self.log("\n📋 СВОДКА ПО ПОРЯДКУ:")
            self.log(f"  1. Файлы отсортированы по алфавиту (A-Z, А-Я)")
            self.log(f"  2. Переименование: файл №1 → строка №1, файл №2 → строка №2, ...")
            self.log(f"  3. Дубликаты обрабатываются последовательно: имя → имя (1) → имя (2) → ...")
            self.log(f"  4. ❗ Таблица читается БЕЗ строки заголовка (с 1-й строки)")
            self.log(f"  5. 🔄 Нумерация дубликатов не зависит от порядка в таблице")
            self.log(f"  6. 📎 Сохранение оригинального расширения файла")
            
            self.log("="*70)
            
            # Обновляем статус
            status_msg = f"Готово! Успешно: {success_count}"
            if error_count > 0:
                status_msg += f", Ошибок: {error_count}"
            if skipped_count > 0:
                status_msg += f", Пропущено: {skipped_count}"
            if processed_duplicates:
                status_msg += f", Дубликатов: {len(processed_duplicates)}"
            self.status_var.set(status_msg)
            
            # Формируем итоговое сообщение
            result_parts = []
            result_parts.append("🏁 ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО")
            
            if success_count > 0:
                result_parts.append(f"\n✅ Успешно: {success_count} файлов")
            
            if error_count > 0:
                result_parts.append(f"\n❌ Ошибки: {error_count} файлов")
            
            if skipped_count > 0:
                result_parts.append(f"\n⏹️  Пропущено: {skipped_count} файлов")
            
            if processed_duplicates:
                result_parts.append(f"\n🔄 Обработано дубликатов: {len(processed_duplicates)}")
                total_dups = sum(count - 1 for count in processed_duplicates.values())
                result_parts.append(f"\n🔄 Добавлено суффиксов: {total_dups}")
            
            result_parts.append(f"\n📎 Сохранены оригинальные расширения файлов")
            
            if skipped_count > 0:
                result_parts.append(f"\n\n💡 РЕКОМЕНДАЦИЯ:")
                result_parts.append(f"\nДобавьте больше имен в таблицу (всего имен: {names_count}, нужно: {files_count})")
            
            messagebox.showinfo("Готово", "".join(result_parts))
            
        except Exception as e:
            error_msg = f"\n🔥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}"
            self.log(error_msg)
            self.status_var.set("Ошибка при выполнении")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n\n{str(e)}")
        
        finally:
            self.run_button.config(state="normal")
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.root.destroy()

def main():
    """Основная функция запуска"""
    root = tk.Tk()
    app = FileRenamerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()