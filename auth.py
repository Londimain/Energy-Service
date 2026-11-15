import tkinter as tk
from tkinter import messagebox

from icons import set_app_icon


class AuthWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Авторизация")
        self.root.geometry("300x160")
        self.root.configure(bg='#2b2b2b')
        self.root.resizable(False, False)
        
        # Устанавливаем иконку для окна авторизации
        set_app_icon(self.root)
        
        self.authenticated = False

        # Центрируем окно на экране
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.root.winfo_screenheight() // 2) - (160 // 2)
        self.root.geometry(f'300x160+{x}+{y}')

        # Запрещаем открывать другие окна, пока открыто это
        self.root.grab_set()

        tk.Label(
            self.root, 
            text="Введите пароль:", 
            bg='#2b2b2b', 
            fg='#ffffff', 
            font=('Segoe UI', 12)
        ).pack(pady=(25, 5))
        
        self.pwd_entry = tk.Entry(
            self.root, 
            show='*', 
            font=('Segoe UI', 12), 
            justify='left', # <--- ИЗМЕНЕНО НА 'left'
            bg='#3c3c3c', 
            fg='#ffffff', 
            insertbackground='#ffffff'
        )
        self.pwd_entry.pack(pady=5, padx=20, fill='x') # Добавлен padx и fill, чтобы поле выглядело аккуратно
        self.pwd_entry.focus_set()

        self.pwd_entry.bind('<Return>', lambda e: self.check_password())

        tk.Button(
            self.root, 
            text="Войти", 
            command=self.check_password, 
            bg='#2d4a5a', 
            fg='#ffffff', 
            font=('Segoe UI', 10), 
            relief='flat', 
            width=10
        ).pack(pady=15)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def check_password(self):
        if self.pwd_entry.get() == "1111":
            self.authenticated = True
            self.root.destroy()
        else:
            # Указываем parent=self.root, чтобы messagebox унаследовал иконку
            messagebox.showerror("Ошибка", "Неверный пароль!", parent=self.root)
            self.pwd_entry.delete(0, tk.END)
            self.pwd_entry.focus_set()

    def on_close(self):
        self.authenticated = False
        self.root.destroy()