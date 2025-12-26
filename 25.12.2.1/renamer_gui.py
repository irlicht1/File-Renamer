# -*- coding: utf-8 -*-
"""
Программа для переименования файлов по таблице
Графический интерфейс
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
        self.root.title("Переименование файлов по таблице v25.12.3.1")
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        
        # Центрирование окна
        self.center_window(600, 450)
        
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
        info_label = ttk.Label(
            self.root,
            text="В таблице должен быть ОДИН столбец с именами файлов для переименования",
            style='Header.TLabel',
            foreground='blue'
        )
        info_label.pack(pady=(0, 10))
        
        # Фрейм для таблицы
        table_frame = ttk.LabelFrame(self.root, text="1. Выберите таблицу (CSV или Excel) с именами файлов")
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
        
        self.log_text = tk.Text(text_frame, height=10, wrap="word")
        scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Кнопка очистки лога
        ttk.Button(
            log_frame,
            text="Очистить лог",
            command=self.clear_log,
            width=15
        ).pack(pady=5)
    
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
            self.log(f"Выбрана таблица: {filename}")
    
    def browse_folder(self):
        """Выбор папки с файлами"""
        folder = filedialog.askdirectory(
            title="Выберите папку с файлами для переименования"
        )
        
        if folder:
            self.folder_path.set(folder)
            self.log(f"Выбрана папка: {folder}")
    
    def log(self, message):
        """Добавление сообщения в лог"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update()
    
    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete(1.0, "end")
    
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
            f"Папка: {folder}\n\n"
            "ВНИМАНИЕ: Файлы будут переименованы в алфавитном порядке!\n"
            "Первый файл → первое имя из таблицы, второй → второе и т.д.\n"
            "Рекомендуется сделать резервную копию файлов перед началом."
        )
        
        if not confirm:
            return
        
        self.log("\n" + "="*50)
        self.log("Начинаем переименование файлов...")
        
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
            
            self.log(f"Найдено файлов в папке: {len(files)}")
            self.log(f"Найдено новых имен в таблице: {len(new_names)}")
            self.log("Порядок файлов (по алфавиту):")
            for i, file_path in enumerate(files[:5]):  # Показываем первые 5 файлов
                self.log(f"  {i+1}. {file_path.name}")
            if len(files) > 5:
                self.log(f"  ... и еще {len(files) - 5} файлов")
            
            # 3. Проверяем соответствие количества
            if len(files) != len(new_names):
                self.log(f"⚠️  ВНИМАНИЕ: Количество файлов ({len(files)}) не совпадает")
                self.log(f"с количеством имен в таблице ({len(new_names)})!")
                self.log(f"Будут переименованы только первые {min(len(files), len(new_names))} файлов.")
            
            # 4. Переименовываем файлы
            success_count = 0
            error_count = 0
            
            for i, file_path in enumerate(files):
                if i >= len(new_names):
                    self.log(f"⚠️  Закончились имена в таблице. Остановка.")
                    break
                
                old_name = file_path.name
                new_name = new_names.iloc[i]
                
                # Добавляем расширение .mp4 к новому имени
                new_name_without_ext = os.path.splitext(new_name)[0]
                new_name_mp4 = new_name_without_ext + ".mp4"
                
                new_path = folder_path / new_name_mp4
                
                # Проверяем, не существует ли уже файл с новым именем
                if new_path.exists():
                    self.log(f"⚠️  {i+1:03d}: Файл уже существует: {new_name_mp4}")
                    error_count += 1
                    continue
                
                try:
                    file_path.rename(new_path)
                    self.log(f"✓ {i+1:03d}: {old_name} → {new_name_mp4}")
                    success_count += 1
                except Exception as e:
                    self.log(f"✗ {i+1:03d}: Ошибка переименования {old_name} → {str(e)}")
                    error_count += 1
            
            # Выводим итоги
            self.log("\n" + "="*50)
            self.log("ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО")
            self.log(f"Успешно: {success_count} файлов")
            self.log(f"С ошибками: {error_count} файлов")
            self.log("="*50)
            
            self.status_var.set(f"Готово! Успешно: {success_count}, Ошибок: {error_count}")
            
            messagebox.showinfo(
                "Готово",
                f"Переименование завершено!\n\n"
                f"Успешно переименовано: {success_count} файлов\n"
                f"С ошибками: {error_count} файлов\n\n"
                f"Файлы переименованы в алфавитном порядке."
            )
            
        except Exception as e:
            self.log(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
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