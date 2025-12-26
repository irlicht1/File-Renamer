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
        self.root.title("Переименование файлов по таблице v1.0")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Центрирование окна
        self.center_window(600, 400)
        
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
        
        # Фрейм для таблицы
        table_frame = ttk.LabelFrame(self.root, text="1. Выберите таблицу (CSV или Excel)")
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
        folder_frame = ttk.LabelFrame(self.root, text="2. Выберите папку с файлами")
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
        
        self.log_text = tk.Text(text_frame, height=8, wrap="word")
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
            
            # Загружаем таблицу
            if table.lower().endswith('.csv'):
                df = pd.read_csv(table, encoding='utf-8')
            else:
                df = pd.read_excel(table)
            
            # Проверяем структуру таблицы
            if len(df.columns) < 2:
                messagebox.showerror("Ошибка", 
                    "В таблице должно быть минимум 2 колонки!\n"
                    "Первая колонка - старые имена, вторая - новые имена.")
                return
            
            # Используем первые две колонки
            if len(df.columns) > 2:
                df = df.iloc[:, :2]
            
            df.columns = ['old_name', 'new_name']
            
            # Преобразуем в строки и убираем пробелы
            df['old_name'] = df['old_name'].astype(str).str.strip()
            df['new_name'] = df['new_name'].astype(str).str.strip()
            
            # Переименовываем файлы
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                old_name = row['old_name']
                new_name = row['new_name']
                
                if pd.isna(old_name) or pd.isna(new_name):
                    self.log(f"⚠️  Строка {index+1}: пропущена (пустые значения)")
                    error_count += 1
                    continue
                
                old_path = Path(folder) / old_name
                new_path = Path(folder) / new_name
                
                if not old_path.exists():
                    self.log(f"✗ Файл не найден: {old_name}")
                    error_count += 1
                    continue
                
                if new_path.exists():
                    self.log(f"⚠️  Файл уже существует: {new_name}")
                    error_count += 1
                    continue
                
                try:
                    old_path.rename(new_path)
                    self.log(f"✓ Переименован: {old_name} → {new_name}")
                    success_count += 1
                except Exception as e:
                    self.log(f"✗ Ошибка: {old_name} → {str(e)}")
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
                f"С ошибками: {error_count} файлов"
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