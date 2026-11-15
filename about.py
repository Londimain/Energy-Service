import tkinter as tk
from tkinter import ttk
import webbrowser

from icons import set_app_icon
from version import VERSION


class AboutWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.withdraw() # <--- СКРЫВАЕМ ОКНО ДО ПОЛНОЙ ЗАГРУЗКИ
        
        self.top.title("О программе")
        self.top.geometry("500x480")
        self.top.configure(bg='#2b2b2b')
        self.top.resizable(False, False)
        set_app_icon(self.top)
        
        self.top.grab_set()

        # Заголовок
        tk.Label(self.top, text="Ежемесячные отчёты", bg='#2b2b2b', fg='#ffffff', 
                 font=('Segoe UI', 16, 'bold')).pack(pady=(20, 5))
        tk.Label(self.top, text=f"Версия {VERSION}", bg='#2b2b2b', fg='#888888', 
                 font=('Segoe UI', 10)).pack(pady=(0, 15))

        # Контейнер для кнопок (внизу)
        btn_frame = ttk.Frame(self.top, style='TFrame')
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(10, 20))
        
        btn_frame.columnconfigure(0, weight=1, uniform="btn")
        btn_frame.columnconfigure(1, weight=1, uniform="btn")
        
        repo_btn = ttk.Button(btn_frame, text="Перейти в репозиторий", style='Action.TButton', command=self.open_repo)
        repo_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew", ipady=2)
        
        close_btn = ttk.Button(btn_frame, text="Закрыть", style='Action.TButton', command=self.top.destroy)
        close_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew", ipady=2)

        # Текстовое поле для описания
        text_frame = tk.Frame(self.top, bg='#2b2b2b')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=30)

        text = tk.Text(text_frame, bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 10), 
                       bd=0, highlightthickness=0, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)

        text.tag_configure("category", foreground="#00ff88", font=('Segoe UI', 11, 'bold'))
        text.tag_configure("desc", foreground="#dddddd")

        text.insert(tk.END, "Назначение:\n", "category")
        text.insert(tk.END, "Программа предназначена для ведения, учета и анализа ежемесячных отчётов по потреблению электроэнергии, воды и газа.\n\n", "desc")
        
        text.insert(tk.END, "Основные возможности:\n", "category")
        text.insert(tk.END, "• Учет показаний по трем точкам (Винзавод 1, 2, БН)\n", "desc")
        text.insert(tk.END, "• Расчет разницы потребления (с предыдущей записи или с начала месяца)\n", "desc")
        text.insert(tk.END, "• Автоматический пересчет газа в Т.У.Т и Гкал\n", "desc")
        text.insert(tk.END, "• Поддержка локальной и сетевой базы данных\n", "desc")
        text.insert(tk.END, "• Автоматическое обновление данных в реальном времени\n", "desc")
        text.insert(tk.END, "• Защита программы паролем\n\n", "desc")

        text.insert(tk.END, "Техническая информация:\n", "category")
        text.insert(tk.END, "Технологии: Python 3, Tkinter, SQLite\n", "desc")
        text.insert(tk.END, "База данных по умолчанию: Energy.db\n\n", "desc")
        
        text.insert(tk.END, "Разработчик: Ильенков С.М.\n", "desc")
        text.insert(tk.END, "Организация: ОАО \"Компания МогНат\"\n", "desc")
        
        text.config(state=tk.DISABLED)

        # Центрируем окно перед показом
        self.top.update_idletasks()
        x = (self.top.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.top.winfo_screenheight() // 2) - (480 // 2)
        self.top.geometry(f'+{x}+{y}')
        
        self.top.deiconify() # <--- ПОКАЗЫВАЕМ ОКНО

    def open_repo(self):
        webbrowser.open("https://github.com/Londimain/Energy-Service")