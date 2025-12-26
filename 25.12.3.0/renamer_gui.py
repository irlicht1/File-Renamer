# -*- coding: utf-8 -*-
"""
Программа для переименования файлов по таблице
Графический интерфейс - версия с обработкой дубликатов
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from pathlib import Path

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Переименование файлов по таблице v3.0")
        self.root.geometry("650x500")
        self.root.resizable(False, False)
        
        # Центрирование окна
        self.center_window(650, 500)
        
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
            text="📁 Переименование файлов по таблице",
            style='Title.TLabel'
        )
        title_label.pack(pady=20)
        
        # Информация о формате
        info_frame = tk.Frame(self.root, bg="#f0f8ff", relief="solid", borderwidth=1)
        info_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        info_label = tk.Label(
            info_frame,
            text="Формат таблицы: один столбец с новыми именами (без расширения)\n" +
                 "Порядок: файлы в папке берутся по алфавиту, сопоставляются построчно с таблицей\n" +
                 "Дубликаты: одинаковые имена получат номера (1), (2) и т.д.",
            font=('Arial', 9),
            bg="#f0f8ff",
            justify="left",
            padx=10,
            pady=10
        )
        info_label.pack()
        
        # Фрейм для таблицы
        table_frame = ttk.LabelFrame(self.root, text="1. Выберите таблицу (CSV или Excel) с новыми именами")
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
        self.run_button.pack(pady=30)
        
        # Область лога
        log_frame = ttk.LabelFrame(self.root, text="Лог выполнения")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Создаем текстовое поле с прокруткой
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(text_frame, height=12, wrap="word", font=('Consolas', 9))
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
            title="Выберите файл таблицы",
            filetypes=filetypes
        )
        
        if filename:
            self.table_path.set(filename)
            self.log(f"📋 Выбрана таблица: {os.path.basename(filename)}")
    
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
        
        # Подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите начать переименование файлов?\n\n"
            f"Таблица: {os.path.basename(table)}\n"
            f"Папка: {os.path.basename(folder)}\n\n"
            "ВАЖНО:\n"
            "1. Файлы в папке будут отсортированы по алфавиту\n"
            "2. Первый файл → первое имя из таблицы, второй → второе и т.д.\n"
            "3. К именам автоматически добавится .mp4\n"
            "4. Дубликаты имён получат номера (1), (2)...\n\n"
            "Рекомендуется сделать резервную копию файлов перед началом."
        )
        
        if not confirm:
            return
        
        self.log("\n" + "="*60)
        self.log("🚀 Начинаем переименование файлов...")
        
        try:
            # Блокируем кнопку на время выполнения
            self.run_button.config(state="disabled")
            self.status_var.set("Выполняется переименование...")
            
            # 1. Загружаем таблицу (первый столбец = новые имена)
            if table.lower().endswith('.csv'):
                df = pd.read_csv(table, encoding='utf-8')
            else:
                df = pd.read_excel(table)
            
            if len(df.columns) == 0:
                messagebox.showerror("Ошибка", "Таблица пуста!")
                return
            
            # Берем первый столбец как новые имена
            new_names = df.iloc[:, 0]
            new_names = new_names.dropna()  # Убираем пустые строки
            new_names = new_names.astype(str).str.strip()  # Убираем пробелы
            
            if len(new_names) == 0:
                messagebox.showerror("Ошибка", "В таблице нет новых имен для файлов!")
                return
            
            # 2. Получаем список файлов в папке с помощью os.listdir
            folder_path = Path(folder)
            
            # Получаем список всех элементов в папке
            all_items = os.listdir(folder_path)
            
            # Фильтруем только файлы (исключаем папки)
            files = []
            for item in all_items:
                item_path = folder_path / item
                if item_path.is_file():  # Проверяем, что это файл, а не папка
                    files.append(item_path)
            
            # Сортируем файлы по алфавиту (регистронезависимо)
            files.sort(key=lambda x: x.name.lower())
            
            if len(files) == 0:
                messagebox.showerror("Ошибка", f"В папке нет файлов:\n{folder}")
                return
            
            self.log(f"📊 Найдено файлов в папке: {len(files)}")
            self.log(f"📊 Найдено новых имен в таблице: {len(new_names)}")
            self.log("📋 Порядок файлов (по алфавиту):")
            for i, file_path in enumerate(files[:5]):  # Показываем первые 5 файлов
                self.log(f"  {i+1}. {file_path.name}")
            if len(files) > 5:
                self.log(f"  ... и еще {len(files) - 5} файлов")
            
            # 3. Проверяем соответствие количества
            if len(files) != len(new_names):
                self.log(f"⚠️  ВНИМАНИЕ: Количество файлов ({len(files)}) не совпадает")
                self.log(f"с количеством имен в таблице ({len(new_names)})!")
                self.log(f"Будут переименованы только первые {min(len(files), len(new_names))} файлов.")
            
            # 4. Создаем словарь для отслеживания дубликатов имен
            name_counter = {}
            used_names = set()  # Множество для быстрой проверки уникальности
            
            # 5. Переименовываем файлы
            success_count = 0
            error_count = 0
            
            for i, file_path in enumerate(files):
                if i >= len(new_names):
                    self.log(f"⚠️  Закончились имена в таблице. Остановка.")
                    break
                
                old_name = file_path.name
                base_new_name = new_names.iloc[i]
                
                # Проверяем и обрабатываем дубликаты
                final_name = base_new_name
                
                # Если имя уже использовалось, добавляем порядковый номер
                if base_new_name in name_counter:
                    count = name_counter[base_new_name]
                    name_counter[base_new_name] += 1
                    # Добавляем номер только если это не первое вхождение
                    final_name = f"{base_new_name} ({count})"
                else:
                    name_counter[base_new_name] = 1
                
                # Проверяем, не было ли такого имени уже в этой сессии переименования
                # (на случай, если в таблице уже есть имена с номерами)
                if final_name in used_names:
                    # Генерируем уникальное имя с увеличивающимся номером
                    base_for_duplicate = base_new_name
                    duplicate_counter = 1
                    while f"{base_for_duplicate} ({duplicate_counter})" in used_names:
                        duplicate_counter += 1
                    final_name = f"{base_for_duplicate} ({duplicate_counter})"
                    # Обновляем счетчик для базового имени
                    name_counter[base_new_name] = duplicate_counter + 1
                
                # Добавляем расширение .mp4 к новому имени
                final_name_without_ext = os.path.splitext(final_name)[0]
                final_name_mp4 = final_name_without_ext + ".mp4"
                
                # Проверяем, не существует ли уже файл с новым именем
                new_path = folder_path / final_name_mp4
                
                if new_path.exists():
                    self.log(f"⚠️  {i+1:03d}: Файл уже существует: {final_name_mp4}")
                    error_count += 1
                    continue
                
                # Добавляем имя в список использованных
                used_names.add(final_name)
                
                # Переименовываем файл
                try:
                    file_path.rename(new_path)
                    self.log(f"✅ {i+1:03d}: {old_name} → {final_name_mp4}")
                    success_count += 1
                except Exception as e:
                    self.log(f"❌ {i+1:03d}: Ошибка переименования {old_name} → {str(e)}")
                    error_count += 1
            
            # 6. Выводим итоги
            self.log("\n" + "="*60)
            self.log("🏁 ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО")
            
            # Дополнительная информация о дубликатах
            duplicates = {name: count for name, count in name_counter.items() if count > 1}
            if duplicates:
                self.log("📝 Обнаружены дублирующиеся имена в таблице:")
                for name, count in duplicates.items():
                    self.log(f"  '{name}' - использовано {count} раз")
            
            self.log(f"✅ Успешно: {success_count} файлов")
            self.log(f"❌ С ошибками: {error_count} файлов")
            self.log(f"📊 Всего файлов в папке: {len(files)}")
            if len(files) > len(new_names):
                self.log(f"📊 Осталось непереименованных: {len(files) - success_count - error_count} файлов")
            self.log("="*60)
            
            self.status_var.set(f"Готово! Успешно: {success_count}, Ошибок: {error_count}")
            
            # Формируем итоговое сообщение
            result_message = f"Переименование завершено!\n\nУспешно: {success_count} файлов\nОшибки: {error_count} файлов"
            
            if duplicates:
                result_message += f"\n\nОбнаружены дубликаты: {len(duplicates)} имён"
                dup_list = list(duplicates.items())
                for name, count in dup_list[:3]:  # Показываем первые 3
                    result_message += f"\n- '{name}': {count} раза"
                if len(dup_list) > 3:
                    result_message += f"\n... и ещё {len(dup_list) - 3}"
            
            if len(files) > len(new_names):
                result_message += f"\n\n⚠️  Не переименовано: {len(files) - len(new_names)} файлов (не хватило имён в таблице)"
            
            messagebox.showinfo("Готово", result_message)
            
        except Exception as e:
            self.log(f"\n🔥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
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