import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3

from icons import set_app_icon


class SettingsWindow:
    def __init__(self, parent, current_path, on_save):
        self.top = tk.Toplevel(parent)
        self.top.title("Настройки")
        # Высота окна немного скорректирована под новые отступы
        self.top.geometry("550x200")
        self.top.configure(bg='#2b2b2b')
        self.top.resizable(False, False)
        set_app_icon(self.top)
        
        self.top.grab_set()
        self.on_save = on_save

        # Центрируем
        self.top.update_idletasks()
        x = (self.top.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.top.winfo_screenheight() // 2) - (215 // 2)
        self.top.geometry(f'+{x}+{y}')

        tk.Label(
            self.top, 
            text="Путь к файлу базы данных (Energy.db):", 
            bg='#2b2b2b', 
            fg='#ffffff', 
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor='w', padx=15, pady=(15, 5))
        
        self.path_var = tk.StringVar(value=current_path)
        self.entry = ttk.Entry(self.top, textvariable=self.path_var, font=('Segoe UI', 10))
        self.entry.pack(fill='x', padx=15, pady=5)

        btn_frame = ttk.Frame(self.top, style='TFrame')
        # Уменьшен нижний отступ (было 15, стало 5), чтобы убрать пустоту
        btn_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        btn_frame.columnconfigure(0, weight=1, uniform="btn")
        btn_frame.columnconfigure(1, weight=1, uniform="btn")

        # Добавлен отступ 5px между верхним и нижним рядом кнопок
        ttk.Button(btn_frame, text="Обзор...", command=self.browse, style='Action.TButton').grid(
            row=0, column=0, padx=3, pady=(0, 5), sticky="ew")
        ttk.Button(btn_frame, text="Использовать локальную", command=self.use_local, style='Action.TButton').grid(
            row=0, column=1, padx=3, pady=(0, 5), sticky="ew")
            
        ttk.Button(btn_frame, text="Сохранить", command=self.save, style='Action.TButton').grid(
            row=1, column=0, padx=3, pady=(15, 0), sticky="ew")
        ttk.Button(btn_frame, text="Отмена", command=self.top.destroy, style='Action.TButton').grid(
            row=1, column=1, padx=3, pady=(15, 0), sticky="ew")

    def browse(self):
        path = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if path:
            self.path_var.set(path)

    def use_local(self):
        self.path_var.set("Energy.db")

    def save(self):
        new_path = self.path_var.get().strip()
        if not new_path:
            messagebox.showerror("Ошибка", "Путь не может быть пустым!", parent=self.top)
            return
        
        try:
            conn = sqlite3.connect(new_path)
            conn.close()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверный путь к БД:\n{e}", parent=self.top)
            return

        self.on_save(new_path)
        self.top.destroy()