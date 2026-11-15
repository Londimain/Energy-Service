import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkcalendar import Calendar

from resource import resource_path


class CustomCalendar(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.date_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.date_var, state='readonly', width=12)
        self.entry.pack(side=tk.LEFT, padx=(0, 15))

        self.icon_image = None
        icon_path = resource_path('ico/calendar.png')
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.resize((24, 24), Image.Resampling.LANCZOS)
                self.icon_image = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Не удалось загрузить иконку календаря: {e}")

        self.bg_color = '#2b2b2b'
        self.btn = tk.Button(self, command=self._show_calendar,
                             bd=0, relief='flat', highlightthickness=0,
                             bg=self.bg_color, activebackground=self.bg_color)
        if self.icon_image:
            self.btn.config(image=self.icon_image)
        else:
            self.btn.config(text="📅", font=('Segoe UI', 12))
        self.btn.pack(side=tk.LEFT, padx=(0, 0))
        self._date = None
        self._top = None

    def set_date(self, date):
        if date:
            self._date = date
            self.date_var.set(date.strftime('%d.%m.%Y'))
        else:
            self._date = None
            self.date_var.set('')

    def get_date(self):
        return self._date

    def _show_calendar(self):
        if self._top and self._top.winfo_exists():
            self._top.destroy()
        self._top = tk.Toplevel(self)
        self._top.wm_overrideredirect(True)

        x = self.winfo_rootx()
        y = self.winfo_rooty() - 220
        if y < 0:
            y = self.winfo_rooty() + self.winfo_height() + 5

        self._top.geometry(f"+{x}+{y}")

        cal = Calendar(self._top, selectmode='day', locale='ru_RU',
                       date_pattern='dd.mm.yyyy',
                       background='darkblue', foreground='white',
                       bordercolor='darkblue')
        cal.pack(padx=5, pady=5)
        if self._date:
            cal.selection_set(self._date)

        def set_date_and_close():
            self._date = cal.selection_get()
            self.date_var.set(self._date.strftime('%d.%m.%Y'))
            self._top.destroy()

        cal.bind('<<CalendarSelected>>', lambda e: set_date_and_close())
        self._top.bind("<FocusOut>", lambda e: self._top.destroy())
        self._top.focus_set()