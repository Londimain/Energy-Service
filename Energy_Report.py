import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
import threading
import time
from PIL import Image, ImageTk
import hashlib
import json
from tkcalendar import Calendar

class CustomCalendar(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.date_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.date_var, state='readonly', width=12)
        self.entry.pack(side=tk.LEFT, padx=(0, 15))
        
        self.icon_image = None
        icon_path = 'ico/calendar.png'
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

class EnergyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ежемесячные отчёты")
        
        self.root.withdraw()
        self.set_app_icon()
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        if self.screen_width < 1024:
            window_width = self.screen_width - 20
            window_height = self.screen_height - 40
            self.root.geometry(f"{window_width}x{window_height}+10+10")
        else:
            try:
                self.root.state('zoomed')
            except:
                self.root.attributes('-fullscreen', True)
        
        self.root.configure(bg='#2b2b2b')
        self.root.deiconify()

        self.setup_style()
        self.db_path = 'Energy.db'
        self.init_db()
        self.load_icons()
        
        self.main_container = ttk.Frame(self.root, style='TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.create_navigation()

        self.page_container = ttk.Frame(self.main_container, style='TFrame')
        self.page_container.pack(fill=tk.BOTH, expand=True)

        self.last_update = {}
        self.last_update['electricity'] = None
        self.last_update['water'] = None
        self.last_update['gas'] = None
        
        self.pages = {}
        self.create_pages()
        self.show_page('electricity')

        self.update_lock = threading.Lock()
        self.running = True
        self.first_load = True
        self.update_thread = threading.Thread(target=self.auto_update, daemon=True)
        self.update_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def set_app_icon(self):
        try:
            if os.path.exists('ico/appEnergy.ico'):
                self.root.iconbitmap('ico/appEnergy.ico')
            elif os.path.exists('appEnergy.ico'):
                self.root.iconbitmap('appEnergy.ico')
        except:
            pass

    def load_icons(self):
        self.icons = {}
        icon_files = {
            'energy': 'ico/energy.png',
            'water': 'ico/water.png',
            'gas': 'ico/gaz.png',
            'flash': 'ico/flash.png'  # <--- ДОБАВЛЕНА СТРОКА
        }
        icon_size = 16 if self.screen_width < 1024 else 20
        
        for key, path in icon_files.items():
            try:
                if os.path.exists(path):
                    img = Image.open(path)
                    img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                    self.icons[key] = ImageTk.PhotoImage(img)
                else:
                    self.icons[key] = None
            except:
                self.icons[key] = None

    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')

        bg = '#2b2b2b'
        fg = '#ffffff'
        select_bg = '#1e6b9e'
        select_fg = '#ffffff'
        heading_bg = "#5c3377"
        heading_fg = '#ffffff'

        font_size = 9 if self.screen_width < 1024 else 10
        heading_font_size = 8 if self.screen_width < 1024 else 10

        style.configure('TFrame', background=bg)
        style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI', font_size))
        
        nav_padding = (5, 3) if self.screen_width < 1024 else (10, 5)
        
        # --- Цвета нажатия (кнопки не будут светлеть до белого!) ---
        nav_pressed_bg = '#4a5a6a'
        active_nav_pressed_bg = '#5a6a7a'
        action_pressed_bg = '#4d6a7a'
        
        # Обычные навигационные кнопки
        style.configure('Nav.TButton', 
                        background='#2c3e50',
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        style.map('Nav.TButton', 
                  background=[('active', '#3a5a6a'), ('pressed', nav_pressed_bg)],
                  foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
        
        # Активная навигационная кнопка
        style.configure('ActiveNav.TButton',
                        background='#3a4a5a',
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        style.map('ActiveNav.TButton',
                  background=[('active', '#4a5a6a'), ('pressed', active_nav_pressed_bg)],
                  foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
        
        # Кнопки действий (Добавить, Редактировать, Удалить)
        style.configure('Action.TButton', 
                        background='#2d4a5a',
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        style.map('Action.TButton', 
                  background=[('active', '#3d5a6a'), ('pressed', action_pressed_bg)],
                  foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
        
        # Дополнительные Pressed стили (если вдруг понадобятся)
        PRESSED_COLOR = '#4a5a6a'
        style.configure('NavPressed.TButton',
                        background=PRESSED_COLOR,
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        style.configure('ActiveNavPressed.TButton',
                        background=PRESSED_COLOR,
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        style.configure('ActionPressed.TButton',
                        background=PRESSED_COLOR,
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        
        # Поля ввода
        style.configure('TEntry', fieldbackground='#3c3c3c', foreground=fg, insertcolor=fg,
                        borderwidth=1, relief='solid')
        
        # Таблица
        row_height = 26 if self.screen_width < 1024 else 28
        
        style.configure('Treeview', 
                        background='#3c3c3c', 
                        foreground=fg,
                        fieldbackground='#3c3c3c', 
                        rowheight=row_height,
                        bordercolor='#888888',
                        borderwidth=2)
        style.map('Treeview', 
                  background=[('selected', select_bg)],
                  foreground=[('selected', select_fg)],
                  fieldbackground=[('selected', select_bg)])
        
        style.configure('Treeview.Heading', 
                        background=heading_bg, 
                        foreground=heading_fg,
                        relief='raised',
                        borderwidth=3,
                        font=('Segoe UI', heading_font_size, 'bold'))
        style.map('Treeview.Heading', 
                  background=[('active', "#713a9e")],
                  foreground=[('active', '#ffffff')])
        
        style.configure('TLabelframe', background=bg, foreground=fg, borderwidth=2,
                        relief='groove')
        style.configure('TLabelframe.Label', background=bg, foreground=fg, font=('Segoe UI', heading_font_size, 'bold'))
        style.configure('TScrollbar', background='#3c3c3c', troughcolor='#2b2b2b',
                        arrowcolor=fg, borderwidth=0)

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        tables = ['electricity', 'water', 'gas']
        for table in tables:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if c.fetchone():
                c.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in c.fetchall()]
                if 'month' in columns:
                    print(f"Миграция таблицы {table}: month -> date")
                    c.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
                    if table == 'electricity':
                        c.execute('''CREATE TABLE electricity (
                                        date TEXT PRIMARY KEY,
                                        meter1_reading REAL,
                                        meter2_reading REAL,
                                        meter3_reading REAL
                                     )''')
                    elif table == 'water':
                        c.execute('''CREATE TABLE water (
                                        date TEXT PRIMARY KEY,
                                        glavny REAL,
                                        kan_v REAL
                                     )''')
                    elif table == 'gas':
                        c.execute('''CREATE TABLE gas (
                                        date TEXT PRIMARY KEY,
                                        reading REAL,
                                        coefficient REAL DEFAULT 0.185,
                                        tut REAL,
                                        gkal REAL
                                     )''')
                    if table == 'electricity':
                        c.execute('''INSERT INTO electricity (date, meter1_reading, meter2_reading, meter3_reading)
                                     SELECT month || '-01', meter1_reading, meter2_reading, meter3_reading 
                                     FROM electricity_old''')
                    elif table == 'water':
                        c.execute('''INSERT INTO water (date, glavny, kan_v)
                                     SELECT month || '-01', glavny, kan_v FROM water_old''')
                    elif table == 'gas':
                        c.execute('''INSERT INTO gas (date, reading, coefficient)
                                     SELECT month || '-01', reading, 0.185 FROM gas_old''')
                    c.execute(f"DROP TABLE {table}_old")
                    conn.commit()
                    print(f"Миграция {table} завершена.")

        # Проверка и добавление новых колонок в существующую таблицу gas
        c.execute("PRAGMA table_info(gas)")
        gas_cols = [col[1] for col in c.fetchall()]
        if 'coefficient' not in gas_cols:
            c.execute("ALTER TABLE gas ADD COLUMN coefficient REAL DEFAULT 0.185")
        if 'tut' not in gas_cols:
            c.execute("ALTER TABLE gas ADD COLUMN tut REAL")
        if 'gkal' not in gas_cols:
            c.execute("ALTER TABLE gas ADD COLUMN gkal REAL")

        c.execute('''CREATE TABLE IF NOT EXISTS electricity (
                        date TEXT PRIMARY KEY,
                        meter1_reading REAL,
                        meter2_reading REAL,
                        meter3_reading REAL
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS water (
                        date TEXT PRIMARY KEY,
                        glavny REAL,
                        kan_v REAL
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS gas (
                        date TEXT PRIMARY KEY,
                        reading REAL,
                        coefficient REAL DEFAULT 0.185,
                        tut REAL,
                        gkal REAL
                     )''')
        conn.commit()
        conn.close()

    def create_navigation(self):
        nav_frame = ttk.Frame(self.main_container, style='TFrame')
        nav_frame.pack(fill=tk.X, padx=3, pady=(20, 5))
        nav_frame.columnconfigure(0, weight=1)
        nav_frame.columnconfigure(1, weight=1)
        nav_frame.columnconfigure(2, weight=0)

        title_font_size = 14 if self.screen_width < 1024 else 16

        # Проверяем, загрузилась ли иконка flash
        flash_icon = self.icons.get('flash')
        if flash_icon:
            title = ttk.Label(nav_frame, text=" ЭНЕРГОСЛУЖБА", image=flash_icon, compound=tk.LEFT, font=('Segoe UI', title_font_size, 'bold'))
        else:
            # Если файла нет, показываем эмодзи
            title = ttk.Label(nav_frame, text="⚡ ЭНЕРГОСЛУЖБА", font=('Segoe UI', title_font_size, 'bold'))
        
        title.grid(row=0, column=0, padx=(40, 0), pady=5, sticky='w')

        btn_frame = ttk.Frame(nav_frame, style='TFrame')
        btn_frame.grid(row=0, column=2, padx=(0, 20), pady=5, sticky='e')

        self.nav_buttons = {}
        buttons = [
            ('Электроэнергия', 'electricity', 'energy'),
            ('Вода', 'water', 'water'),
            ('Газ', 'gas', 'gas')
        ]
        for text, page, icon_key in buttons:
            btn = ttk.Button(btn_frame, style='Nav.TButton', command=lambda p=page: self.show_page(p))
            if self.icons.get(icon_key):
                btn.config(image=self.icons[icon_key], compound=tk.LEFT, text=f" {text}")
            else:
                btn.config(text=text)
            btn.pack(side=tk.LEFT, padx=3)
            self.nav_buttons[page] = btn
        self.set_active_button('electricity')

    def set_active_button(self, active_page):
        for page, btn in self.nav_buttons.items():
            if page == active_page:
                btn.configure(style='ActiveNav.TButton')
            else:
                btn.configure(style='Nav.TButton')

    def create_pages(self):
        self.pages['electricity'] = self.create_electricity_page()
        self.pages['water'] = self.create_water_page()
        self.pages['gas'] = self.create_gas_page()

    def show_page(self, page_name):
        self.set_active_button(page_name)
        for name, page in self.pages.items():
            if name == page_name:
                page.pack(fill=tk.BOTH, expand=True)
                self.load_page_data(page_name)
            else:
                page.pack_forget()

    def load_page_data(self, page_name):
        if page_name == 'electricity':
            self.load_electricity_data()
        elif page_name == 'water':
            self.load_water_data()
        elif page_name == 'gas':
            self.load_gas_data()

    def get_table_hash(self, table_name, columns):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(f"SELECT {', '.join(columns)} FROM {table_name} ORDER BY date")
            rows = c.fetchall()
            conn.close()
            data_str = json.dumps(rows, sort_keys=True, default=str)
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception as e:
            print(f"Ошибка получения хеша для {table_name}: {e}")
            return None

    def has_data_changed(self, page_name):
        try:
            if page_name == 'electricity':
                columns = ['date', 'meter1_reading', 'meter2_reading', 'meter3_reading']
            elif page_name == 'water':
                columns = ['date', 'glavny', 'kan_v']
            elif page_name == 'gas':
                columns = ['date', 'reading', 'coefficient', 'tut', 'gkal']
            else:
                return False
            current_hash = self.get_table_hash(page_name, columns)
            if current_hash is None:
                return False
            if self.last_update.get(page_name) is None:
                self.last_update[page_name] = current_hash
                return True
            if current_hash != self.last_update.get(page_name):
                self.last_update[page_name] = current_hash
                return True
            return False
        except Exception as e:
            print(f"Ошибка проверки изменений для {page_name}: {e}")
            return False

    def format_number(self, value):
        if value is None:
            return "—"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        elif isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    def format_date_display(self, date_str):
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%d.%m.%Y')
        except:
            return date_str

    # ---------- СТРАНИЦА ЭЛЕКТРОЭНЕРГИИ ----------
    def create_electricity_page(self):
        page = ttk.Frame(self.page_container, style='TFrame')
        font_size = 12 if self.screen_width < 1024 else 14
        title = ttk.Label(page, text="Отчёт по электроэнергии", font=('Segoe UI', font_size, 'bold'))
        title.pack(pady=5)

        tree_frame = ttk.Frame(page, style='TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=5)

        columns = ('Дата', 'Винзавод 1', 'Винзавод 2', 'Винзавод БН')
        self.electricity_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        col_width = 90 if self.screen_width < 1024 else 130
        for col in columns:
            self.electricity_tree.heading(col, text=col)
            self.electricity_tree.column(col, anchor=tk.CENTER, width=col_width, minwidth=70)

        self.electricity_tree.tag_configure('even', background='#3d3d3d')
        self.electricity_tree.tag_configure('odd', background='#353535')

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.electricity_tree.yview)
        self.electricity_tree.configure(yscrollcommand=scroll.set)
        self.electricity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.electricity_tree.bind('<<TreeviewSelect>>', self.on_electricity_select)
        self.electricity_tree.bind('<Delete>', lambda e: self.delete_electricity_record())

        bottom_frame = ttk.Frame(page, style='TFrame')
        bottom_frame.pack(fill=tk.X, padx=3, pady=3)
        bottom_frame.columnconfigure(0, weight=0)
        bottom_frame.columnconfigure(1, weight=1)

        input_frame = tk.LabelFrame(bottom_frame, text=" Добавить / Редактировать ", 
                                    bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                    bd=1, relief=tk.GROOVE)
        input_frame.grid(row=0, column=0, sticky='nw', padx=(0, 3))
        if self.screen_width < 1024:
            input_frame.config(width=280)
        else:
            input_frame.config(width=350)

        input_container = tk.Frame(input_frame, bg='#2b2b2b')
        input_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(input_container, text="Дата:", bg='#2b2b2b', fg='#ffffff', 
                 font=('Segoe UI', 8), anchor=tk.W).grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.elec_month_cal = CustomCalendar(input_container)
        self.elec_month_cal.grid(row=0, column=1, padx=2, pady=2, sticky=tk.W)
        self.elec_month_cal.set_date(datetime.now())

        fields = [
            ('Винзавод 1 (кВт):', 'm1_entry', 12),
            ('Винзавод 2 (кВт):', 'm2_entry', 12),
            ('Винзавод БН (кВт):', 'm3_entry', 12),
        ]
        self.elec_entries = {}
        for i, (label, key, width) in enumerate(fields, start=1):
            lbl = tk.Label(input_container, text=label, bg='#2b2b2b', fg='#ffffff', 
                          font=('Segoe UI', 8), anchor=tk.W)
            lbl.grid(row=i, column=0, padx=2, pady=2, sticky=tk.W)
            entry = ttk.Entry(input_container, width=width)
            entry.grid(row=i, column=1, padx=2, pady=2, sticky=tk.W)
            entry.bind('<Return>', lambda e: self.add_electricity_record())
            self.elec_entries[key] = entry

        btn_frame = tk.Frame(input_container, bg='#2b2b2b')
        btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=(10, 0))

        btn_width = 15
        
        self.elec_add_btn = ttk.Button(btn_frame, style='Action.TButton', text="Добавить", command=self.add_electricity_record, width=btn_width)
        self.elec_add_btn.pack(side=tk.LEFT, padx=2)
        self.elec_add_btn.bind('<Return>', lambda e: self.add_electricity_record())

        self.elec_edit_btn = ttk.Button(btn_frame, style='Action.TButton', text="Редактировать", command=self.edit_electricity_record, state=tk.DISABLED, width=btn_width)
        self.elec_edit_btn.pack(side=tk.LEFT, padx=2)

        self.elec_cancel_btn = ttk.Button(btn_frame, style='Action.TButton', text="Очистить", command=self.cancel_electricity_edit, width=btn_width)
        self.elec_cancel_btn.pack(side=tk.LEFT, padx=2)

        del_btn = ttk.Button(btn_frame, style='Action.TButton', text="Удалить", command=self.delete_electricity_record, width=btn_width)
        del_btn.pack(side=tk.LEFT, padx=2)

        diff_frame = tk.LabelFrame(bottom_frame, text=" Разница между последними данными ", 
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.elec_diff_hint = tk.Label(diff_container, 
                                       text="Укажите нужную дату в таблице для получения разницы", 
                                       bg='#2b2b2b', fg='#888888', 
                                       font=('Segoe UI', 13),
                                       anchor=tk.CENTER)
        self.elec_diff_hint.pack(expand=True, fill=tk.BOTH)

        self.elec_diff_content = tk.Frame(diff_container, bg='#2b2b2b')
        diff_font = ('Segoe UI', 9) if self.screen_width < 1024 else ('Segoe UI', 11)

        diff_row = tk.Frame(self.elec_diff_content, bg='#2b2b2b')
        diff_row.pack(fill=tk.X, pady=3)

        self.elec_diff_m1 = tk.Label(diff_row, text="Винзавод 1: -- кВт", 
                                     bg='#2b2b2b', fg='#ffffff', font=diff_font,
                                     anchor=tk.CENTER)
        self.elec_diff_m1.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.elec_diff_m2 = tk.Label(diff_row, text="Винзавод 2: -- кВт", 
                                     bg='#2b2b2b', fg='#ffffff', font=diff_font,
                                     anchor=tk.CENTER)
        self.elec_diff_m2.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.elec_diff_m3 = tk.Label(diff_row, text="Винзавод БН: -- кВт", 
                                     bg='#2b2b2b', fg='#ffffff', font=diff_font,
                                     anchor=tk.CENTER)
        self.elec_diff_m3.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        total_font = ('Segoe UI', 11, 'bold') if self.screen_width < 1024 else ('Segoe UI', 13, 'bold')
        separator = tk.Frame(self.elec_diff_content, bg='#555555', height=1)
        separator.pack(fill=tk.X, pady=3)

        self.elec_diff_total = tk.Label(self.elec_diff_content, text="Общий расход: -- кВт", 
                                        bg='#2b2b2b', fg='#00ff88', font=total_font,
                                        anchor=tk.CENTER)
        self.elec_diff_total.pack(fill=tk.X, pady=2)

        self.elec_selected_date = None
        self.elec_editing = False
        return page

    def load_electricity_data(self):
        try:
            current_selection = self.electricity_tree.selection()
            current_date = None
            if current_selection:
                item = current_selection[0]
                current_date = self.electricity_tree.item(item, 'values')[0]

            for row in self.electricity_tree.get_children():
                self.electricity_tree.delete(row)

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT date, meter1_reading, meter2_reading, meter3_reading FROM electricity ORDER BY date DESC")
            rows = c.fetchall()
            conn.close()

            self.last_update['electricity'] = self.get_table_hash('electricity', ['date', 'meter1_reading', 'meter2_reading', 'meter3_reading'])

            if len(rows) > 0:
                max_rows = 6 if self.screen_height < 768 else 8
                visible_rows = min(len(rows), max_rows)
                self.electricity_tree.configure(height=visible_rows)
            else:
                self.electricity_tree.configure(height=4)

            for i, row in enumerate(rows):
                formatted_row = (
                    self.format_date_display(row[0]),
                    self.format_number(row[1]),
                    self.format_number(row[2]),
                    self.format_number(row[3])
                )
                tag = 'even' if i % 2 == 0 else 'odd'
                self.electricity_tree.insert('', tk.END, values=formatted_row, tags=(tag,))

            if current_date:
                for item in self.electricity_tree.get_children():
                    if self.electricity_tree.item(item, 'values')[0] == current_date:
                        self.electricity_tree.selection_set(item)
                        self.electricity_tree.focus(item)
                        values = self.electricity_tree.item(item, 'values')
                        self.elec_selected_date = current_date
                        self.elec_edit_btn.config(state=tk.NORMAL)
                        self.show_electricity_diff(current_date, values)
                        try:
                            dt = datetime.strptime(current_date, '%d.%m.%Y')
                            self.elec_month_cal.set_date(dt)
                        except:
                            pass
                        break
            else:
                self.elec_selected_date = None
                self.elec_editing = False
                self.elec_edit_btn.config(state=tk.DISABLED)
                self.elec_add_btn.config(text="Добавить")
                self.elec_cancel_btn.config(text="Очистить")
                self.clear_electricity_diff()
                self.elec_month_cal.set_date(datetime.now())

            if not self.elec_editing:
                for key in self.elec_entries:
                    self.elec_entries[key].delete(0, tk.END)

        except Exception as e:
            print(f"Ошибка загрузки электроэнергии: {e}")

    def on_electricity_select(self, event):
        selected = self.electricity_tree.selection()
        if not selected:
            self.elec_edit_btn.config(state=tk.DISABLED)
            self.clear_electricity_diff()
            return
        item = selected[0]
        values = self.electricity_tree.item(item, 'values')
        date_display = values[0]
        self.elec_selected_date = date_display
        self.elec_edit_btn.config(state=tk.NORMAL)
        self.show_electricity_diff(date_display, values)
        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            self.elec_month_cal.set_date(dt)
        except:
            pass

        if self.elec_editing:
            for idx, key in enumerate(['m1_entry', 'm2_entry', 'm3_entry']):
                self.elec_entries[key].delete(0, tk.END)
                if values[idx+1] != "—":
                    self.elec_entries[key].insert(0, values[idx+1])

    def clear_electricity_diff(self):
        self.elec_diff_hint.pack(expand=True, fill=tk.BOTH)
        self.elec_diff_content.pack_forget()
        self.elec_diff_m1.config(text="Винзавод 1: -- кВт")
        self.elec_diff_m2.config(text="Винзавод 2: -- кВт")
        self.elec_diff_m3.config(text="Винзавод БН: -- кВт")
        self.elec_diff_total.config(text="Общий расход: -- кВт")

    def show_electricity_diff(self, date_display, values):
        self.elec_diff_hint.pack_forget()
        self.elec_diff_content.pack(fill=tk.BOTH, expand=True)

        try:
            cur_m1 = float(values[1]) if values[1] != "—" else 0
            cur_m2 = float(values[2]) if values[2] != "—" else 0
            cur_m3 = float(values[3]) if values[3] != "—" else 0
        except:
            cur_m1 = cur_m2 = cur_m3 = 0

        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = ''

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT meter1_reading, meter2_reading, meter3_reading FROM electricity WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
        prev = c.fetchone()
        conn.close()

        if prev:
            p1, p2, p3 = prev
            diff1 = cur_m1 - p1 if p1 is not None else 0
            diff2 = cur_m2 - p2 if p2 is not None else 0
            diff3 = cur_m3 - p3 if p3 is not None else 0
        else:
            diff1 = diff2 = diff3 = 0

        k1, k2, k3 = 80, 80, 40
        total = diff1 * k1 + diff2 * k2 + diff3 * k3

        self.elec_diff_m1.config(text=f"Винзавод 1: {self.format_number(diff1)} кВт")
        self.elec_diff_m2.config(text=f"Винзавод 2: {self.format_number(diff2)} кВт")
        self.elec_diff_m3.config(text=f"Винзавод БН: {self.format_number(diff3)} кВт")
        self.elec_diff_total.config(text=f"Общий расход: {self.format_number(total)} кВт")

    def cancel_electricity_edit(self):
        self.elec_editing = False
        self.elec_edit_btn.config(state=tk.DISABLED)
        self.elec_add_btn.config(text="Добавить")
        self.elec_cancel_btn.config(text="Очистить")
        for key in self.elec_entries:
            self.elec_entries[key].delete(0, tk.END)
        self.elec_month_cal.set_date(datetime.now())
        self.electricity_tree.selection_remove(self.electricity_tree.selection())
        self.elec_selected_date = None
        self.clear_electricity_diff()

    def add_electricity_record(self):
        selected_date = self.elec_month_cal.get_date()
        if not selected_date:
            messagebox.showerror("Ошибка", "Выберите дату.")
            return
        date_str = selected_date.strftime('%Y-%m-%d')
        def get_float_or_none(val):
            val = val.strip()
            if val == '':
                return None
            try:
                return float(val)
            except ValueError:
                raise ValueError(f"Некорректное число: '{val}'")
        try:
            m1 = get_float_or_none(self.elec_entries['m1_entry'].get())
            m2 = get_float_or_none(self.elec_entries['m2_entry'].get())
            m3 = get_float_or_none(self.elec_entries['m3_entry'].get())
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Если это редактирование, удаляем старую запись
        if self.elec_editing:
            old_date_str = datetime.strptime(self.elec_selected_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            c.execute("DELETE FROM electricity WHERE date = ?", (old_date_str,))

        c.execute("SELECT date FROM electricity WHERE date = ?", (date_str,))
        if c.fetchone():
            if not messagebox.askyesno("Повтор", f"Запись за {date_str} уже существует. Перезаписать?"):
                conn.close()
                return
            c.execute("DELETE FROM electricity WHERE date = ?", (date_str,))

        c.execute("INSERT INTO electricity (date, meter1_reading, meter2_reading, meter3_reading) VALUES (?, ?, ?, ?)",
                  (date_str, m1, m2, m3))
        conn.commit()
        conn.close()

        self.elec_editing = False
        self.elec_edit_btn.config(state=tk.DISABLED)
        self.elec_add_btn.config(text="Добавить")
        self.elec_cancel_btn.config(text="Очистить")
        for key in self.elec_entries:
            self.elec_entries[key].delete(0, tk.END)
        self.elec_month_cal.set_date(datetime.now())
        self.load_electricity_data()
        messagebox.showinfo("Успех", f"Данные за {date_str} сохранены.")

    def edit_electricity_record(self):
        if not self.elec_selected_date:
            messagebox.showwarning("Предупреждение", "Сначала выберите запись для редактирования.")
            return
        selected = self.electricity_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.electricity_tree.item(item, 'values')
        date_display = values[0]
        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            self.elec_month_cal.set_date(dt)
        except:
            pass
        for idx, key in enumerate(['m1_entry', 'm2_entry', 'm3_entry']):
            self.elec_entries[key].delete(0, tk.END)
            if values[idx+1] != "—":
                self.elec_entries[key].insert(0, values[idx+1])
        self.elec_editing = True
        self.elec_add_btn.config(text="Обновить")
        self.elec_cancel_btn.config(text="Отмена")

    def delete_electricity_record(self):
        selected = self.electricity_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления.")
            return
        item = selected[0]
        values = self.electricity_tree.item(item, 'values')
        date_display = values[0]
        if messagebox.askyesno("Удаление", f"Удалить запись за {date_display}?"):
            try:
                dt = datetime.strptime(date_display, '%d.%m.%Y')
                date_str = dt.strftime('%Y-%m-%d')
            except:
                return
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM electricity WHERE date = ?", (date_str,))
            conn.commit()
            conn.close()
            self.load_electricity_data()
            messagebox.showinfo("Успех", "Запись удалена.")

    # ---------- СТРАНИЦА ВОДЫ ----------
    def create_water_page(self):
        page = ttk.Frame(self.page_container, style='TFrame')
        font_size = 12 if self.screen_width < 1024 else 14
        title = ttk.Label(page, text="Отчёт по воде", font=('Segoe UI', font_size, 'bold'))
        title.pack(pady=5)

        tree_frame = ttk.Frame(page, style='TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=5)

        columns = ('Дата', 'Главный ввод', 'Канализация')
        self.water_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        col_width = 100 if self.screen_width < 1024 else 140
        for col in columns:
            self.water_tree.heading(col, text=col)
            self.water_tree.column(col, anchor=tk.CENTER, width=col_width, minwidth=80)

        self.water_tree.tag_configure('even', background='#3d3d3d')
        self.water_tree.tag_configure('odd', background='#353535')

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.water_tree.yview)
        self.water_tree.configure(yscrollcommand=scroll.set)
        self.water_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.water_tree.bind('<<TreeviewSelect>>', self.on_water_select)
        self.water_tree.bind('<Delete>', lambda e: self.delete_water_record())

        bottom_frame = ttk.Frame(page, style='TFrame')
        bottom_frame.pack(fill=tk.X, padx=3, pady=3)
        bottom_frame.columnconfigure(0, weight=0)
        bottom_frame.columnconfigure(1, weight=1)

        input_frame = tk.LabelFrame(bottom_frame, text=" Добавить / Редактировать ", 
                                    bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                    bd=1, relief=tk.GROOVE)
        input_frame.grid(row=0, column=0, sticky='nw', padx=(0, 3))
        if self.screen_width < 1024:
            input_frame.config(width=280)
        else:
            input_frame.config(width=350)

        input_container = tk.Frame(input_frame, bg='#2b2b2b')
        input_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(input_container, text="Дата:", bg='#2b2b2b', fg='#ffffff', 
                 font=('Segoe UI', 8), anchor=tk.W).grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.water_month_cal = CustomCalendar(input_container)
        self.water_month_cal.grid(row=0, column=1, padx=2, pady=2, sticky=tk.W)
        self.water_month_cal.set_date(datetime.now())

        water_fields = [
            ('Главный ввод (м³):', 'glavny', 12),
            ('Канализация V (м³):', 'kan_v', 12),
        ]

        self.water_entries = {}
        font_size_label = 8 if self.screen_width < 1024 else 10
        for i, (label, key, width) in enumerate(water_fields, start=1):
            lbl = tk.Label(input_container, text=label, bg='#2b2b2b', fg='#ffffff', 
                          font=('Segoe UI', font_size_label), anchor=tk.W)
            lbl.grid(row=i, column=0, padx=2, pady=2, sticky=tk.W)
            entry = ttk.Entry(input_container, width=width)
            entry.grid(row=i, column=1, padx=2, pady=2, sticky=tk.W)
            entry.bind('<Return>', lambda e: self.add_water_record())
            self.water_entries[key] = entry

        btn_frame = tk.Frame(input_container, bg='#2b2b2b')
        btn_frame.grid(row=len(water_fields)+1, column=0, columnspan=2, pady=(10, 0))

        btn_width = 15
        
        self.water_add_btn = ttk.Button(btn_frame, style='Action.TButton', text="➕ Добавить", command=self.add_water_record, width=btn_width)
        self.water_add_btn.pack(side=tk.LEFT, padx=2)
        self.water_add_btn.bind('<Return>', lambda e: self.add_water_record())

        self.water_edit_btn = ttk.Button(btn_frame, style='Action.TButton', text="Редактировать", command=self.edit_water_record, state=tk.DISABLED, width=btn_width)
        self.water_edit_btn.pack(side=tk.LEFT, padx=2)

        self.water_cancel_btn = ttk.Button(btn_frame, style='Action.TButton', text="Очистить", command=self.cancel_water_edit, width=btn_width)
        self.water_cancel_btn.pack(side=tk.LEFT, padx=2)

        del_btn = ttk.Button(btn_frame, style='Action.TButton', text="Удалить", command=self.delete_water_record, width=btn_width)
        del_btn.pack(side=tk.LEFT, padx=2)

        diff_frame = tk.LabelFrame(bottom_frame, text=" Разница между последними данными ", 
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.water_diff_hint = tk.Label(diff_container, 
                                        text="Укажите нужную дату в таблице для получения разницы", 
                                        bg='#2b2b2b', fg='#888888', 
                                        font=('Segoe UI', 13),
                                        anchor=tk.CENTER)
        self.water_diff_hint.pack(expand=True, fill=tk.BOTH)

        self.water_diff_content = tk.Frame(diff_container, bg='#2b2b2b')
        font_diff = 10 if self.screen_width < 1024 else 12

        # Создаем контейнер для размещения в одну строку
        water_diff_row = tk.Frame(self.water_diff_content, bg='#2b2b2b')
        water_diff_row.pack(expand=True, fill=tk.BOTH, pady=10)

        self.water_diff_glavny = tk.Label(water_diff_row, text="Главный ввод: -- м³", 
                                          bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                          anchor=tk.CENTER)
        self.water_diff_glavny.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=15)

        self.water_diff_kan_v = tk.Label(water_diff_row, text="Канализация V: -- м³", 
                                         bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                         anchor=tk.CENTER)
        self.water_diff_kan_v.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=15)

        self.water_selected_date = None
        self.water_editing = False
        return page

    def load_water_data(self):
        try:
            current_selection = self.water_tree.selection()
            current_date = None
            if current_selection:
                item = current_selection[0]
                current_date = self.water_tree.item(item, 'values')[0]

            for row in self.water_tree.get_children():
                self.water_tree.delete(row)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT date, glavny, kan_v FROM water ORDER BY date DESC")
            rows = c.fetchall()
            conn.close()

            self.last_update['water'] = self.get_table_hash('water', ['date', 'glavny', 'kan_v'])

            if len(rows) > 0:
                max_rows = 6 if self.screen_height < 768 else 8
                visible_rows = min(len(rows), max_rows)
                self.water_tree.configure(height=visible_rows)
            else:
                self.water_tree.configure(height=4)

            for i, row in enumerate(rows):
                formatted_row = (
                    self.format_date_display(row[0]),
                    self.format_number(row[1]),
                    self.format_number(row[2])
                )
                tag = 'even' if i % 2 == 0 else 'odd'
                self.water_tree.insert('', tk.END, values=formatted_row, tags=(tag,))

            if current_date:
                for item in self.water_tree.get_children():
                    if self.water_tree.item(item, 'values')[0] == current_date:
                        self.water_tree.selection_set(item)
                        self.water_tree.focus(item)
                        values = self.water_tree.item(item, 'values')
                        self.water_selected_date = current_date
                        self.water_edit_btn.config(state=tk.NORMAL)
                        self.show_water_diff(current_date, values)
                        try:
                            dt = datetime.strptime(current_date, '%d.%m.%Y')
                            self.water_month_cal.set_date(dt)
                        except:
                            pass
                        break
            else:
                self.water_selected_date = None
                self.water_editing = False
                self.water_edit_btn.config(state=tk.DISABLED)
                self.water_add_btn.config(text="➕ Добавить")
                self.water_cancel_btn.config(text="Очистить")
                self.clear_water_diff()
                self.water_month_cal.set_date(datetime.now())

            if not self.water_editing:
                for key in self.water_entries:
                    self.water_entries[key].delete(0, tk.END)

        except Exception as e:
            print(f"Ошибка загрузки воды: {e}")

    def on_water_select(self, event):
        selected = self.water_tree.selection()
        if not selected:
            self.water_edit_btn.config(state=tk.DISABLED)
            self.clear_water_diff()
            return
        item = selected[0]
        values = self.water_tree.item(item, 'values')
        date_display = values[0]
        self.water_selected_date = date_display
        self.water_edit_btn.config(state=tk.NORMAL)
        self.show_water_diff(date_display, values)
        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            self.water_month_cal.set_date(dt)
        except:
            pass

        if self.water_editing:
            keys = ['glavny', 'kan_v']
            for i, key in enumerate(keys):
                self.water_entries[key].delete(0, tk.END)
                if values[i+1] != "—":
                    self.water_entries[key].insert(0, values[i+1])

    def clear_water_diff(self):
        self.water_diff_hint.pack(expand=True, fill=tk.BOTH)
        self.water_diff_content.pack_forget()
        self.water_diff_glavny.config(text="Главный ввод: -- м³")
        self.water_diff_kan_v.config(text="Канализация V: -- м³")

    def show_water_diff(self, date_display, values):
        self.water_diff_hint.pack_forget()
        self.water_diff_content.pack(fill=tk.BOTH, expand=True)

        try:
            cur_glavny = float(values[1]) if values[1] != "—" else 0
            cur_kan_v = float(values[2]) if values[2] != "—" else 0
        except:
            cur_glavny = 0
            cur_kan_v = 0

        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = ''

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT glavny, kan_v FROM water WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
        prev = c.fetchone()
        conn.close()

        if prev:
            prev_glavny, prev_kan_v = prev
            diff_glavny = cur_glavny - prev_glavny if prev_glavny is not None else 0
            diff_kan_v = cur_kan_v - prev_kan_v if prev_kan_v is not None else 0
        else:
            diff_glavny = 0
            diff_kan_v = 0

        self.water_diff_glavny.config(text=f"Главный ввод: {self.format_number(diff_glavny)} м³")
        self.water_diff_kan_v.config(text=f"Канализация V: {self.format_number(diff_kan_v)} м³")

    def cancel_water_edit(self):
        self.water_editing = False
        self.water_edit_btn.config(state=tk.DISABLED)
        self.water_add_btn.config(text="➕ Добавить")
        self.water_cancel_btn.config(text="Очистить")
        for key in self.water_entries:
            self.water_entries[key].delete(0, tk.END)
        self.water_month_cal.set_date(datetime.now())
        self.water_tree.selection_remove(self.water_tree.selection())
        self.water_selected_date = None
        self.clear_water_diff()

    def add_water_record(self):
        selected_date = self.water_month_cal.get_date()
        if not selected_date:
            messagebox.showerror("Ошибка", "Выберите дату.")
            return
        date_str = selected_date.strftime('%Y-%m-%d')

        def get_float_or_none(val):
            val = val.strip()
            if val == '':
                return None
            try:
                return float(val)
            except ValueError:
                raise ValueError(f"Некорректное число: '{val}'")

        try:
            vals = [get_float_or_none(self.water_entries[key].get()) 
                    for key in ['glavny', 'kan_v']]
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Если это редактирование, удаляем старую запись
        if self.water_editing:
            old_date_str = datetime.strptime(self.water_selected_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            c.execute("DELETE FROM water WHERE date = ?", (old_date_str,))

        c.execute("SELECT date FROM water WHERE date = ?", (date_str,))
        if c.fetchone():
            if not messagebox.askyesno("Повтор", f"Запись за {date_str} уже существует. Перезаписать?"):
                conn.close()
                return
            c.execute("DELETE FROM water WHERE date = ?", (date_str,))

        c.execute("INSERT INTO water (date, glavny, kan_v) VALUES (?, ?, ?)",
                  (date_str, vals[0], vals[1]))
        conn.commit()
        conn.close()

        self.water_editing = False
        self.water_edit_btn.config(state=tk.DISABLED)
        self.water_add_btn.config(text="➕ Добавить")
        self.water_cancel_btn.config(text="Очистить")
        for key in self.water_entries:
            self.water_entries[key].delete(0, tk.END)
        self.water_month_cal.set_date(datetime.now())
        self.load_water_data()
        messagebox.showinfo("Успех", f"Данные за {date_str} сохранены.")

    def edit_water_record(self):
        if not self.water_selected_date:
            messagebox.showwarning("Предупреждение", "Сначала выберите запись.")
            return
        selected = self.water_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.water_tree.item(item, 'values')
        date_display = values[0]
        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            self.water_month_cal.set_date(dt)
        except:
            pass
        keys = ['glavny', 'kan_v']
        for i, key in enumerate(keys):
            self.water_entries[key].delete(0, tk.END)
            if values[i+1] != "—":
                self.water_entries[key].insert(0, values[i+1])
        self.water_editing = True
        self.water_add_btn.config(text="Обновить")
        self.water_cancel_btn.config(text="Отмена")

    def delete_water_record(self):
        selected = self.water_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись.")
            return
        item = selected[0]
        date_display = self.water_tree.item(item, 'values')[0]
        if messagebox.askyesno("Удаление", f"Удалить запись за {date_display}?"):
            try:
                dt = datetime.strptime(date_display, '%d.%m.%Y')
                date_str = dt.strftime('%Y-%m-%d')
            except:
                return
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM water WHERE date = ?", (date_str,))
            conn.commit()
            conn.close()
            self.load_water_data()
            messagebox.showinfo("Успех", "Запись удалена.")

    # ---------- СТРАНИЦА ГАЗА ----------
    def create_gas_page(self):
        page = ttk.Frame(self.page_container, style='TFrame')
        font_size = 12 if self.screen_width < 1024 else 14
        title = ttk.Label(page, text="Отчёт по газу", font=('Segoe UI', font_size, 'bold'))
        title.pack(pady=5)

        tree_frame = ttk.Frame(page, style='TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=5)

        columns = ('Дата', 'Показания (м³)', 'Т.У.Т', 'Гкал')
        self.gas_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        col_width = 100 if self.screen_width < 1024 else 130
        for col in columns:
            self.gas_tree.heading(col, text=col)
            self.gas_tree.column(col, anchor=tk.CENTER, width=col_width, minwidth=80)

        self.gas_tree.tag_configure('even', background='#3d3d3d')
        self.gas_tree.tag_configure('odd', background='#353535')

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.gas_tree.yview)
        self.gas_tree.configure(yscrollcommand=scroll.set)
        self.gas_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.gas_tree.bind('<<TreeviewSelect>>', self.on_gas_select)
        self.gas_tree.bind('<Delete>', lambda e: self.delete_gas_record())

        bottom_frame = ttk.Frame(page, style='TFrame')
        bottom_frame.pack(fill=tk.X, padx=3, pady=3)
        bottom_frame.columnconfigure(0, weight=0)
        bottom_frame.columnconfigure(1, weight=1)

        input_frame = tk.LabelFrame(bottom_frame, text=" Добавить / Редактировать ", 
                                    bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                    bd=1, relief=tk.GROOVE)
        input_frame.grid(row=0, column=0, sticky='nw', padx=(0, 3))
        if self.screen_width < 1024:
            input_frame.config(width=300)
        else:
            input_frame.config(width=380)

        input_container = tk.Frame(input_frame, bg='#2b2b2b')
        input_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        font_label = 8 if self.screen_width < 1024 else 10
        
        tk.Label(input_container, text="Дата:", bg='#2b2b2b', fg='#ffffff', 
                 font=('Segoe UI', font_label)).grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.gas_month_cal = CustomCalendar(input_container)
        self.gas_month_cal.grid(row=0, column=1, padx=2, pady=2, sticky=tk.W)
        self.gas_month_cal.set_date(datetime.now())

        tk.Label(input_container, text="Показание (м³):", bg='#2b2b2b', fg='#ffffff', 
                 font=('Segoe UI', font_label)).grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.gas_reading_entry = ttk.Entry(input_container, width=12)
        self.gas_reading_entry.grid(row=1, column=1, padx=2, pady=2, sticky=tk.W)
        self.gas_reading_entry.bind('<Return>', lambda e: self.add_gas_record())

        tk.Label(input_container, text="Коэффициент пересчета (Гкал):", bg='#2b2b2b', fg='#ffffff', 
                 font=('Segoe UI', font_label)).grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        self.gas_coef_entry = ttk.Entry(input_container, width=12)
        self.gas_coef_entry.insert(0, "0.185")
        self.gas_coef_entry.grid(row=2, column=1, padx=2, pady=2, sticky=tk.W)
        self.gas_coef_entry.bind('<Return>', lambda e: self.add_gas_record())

        btn_frame = tk.Frame(input_container, bg='#2b2b2b')
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        btn_width = 15
        
        self.gas_add_btn = ttk.Button(btn_frame, style='Action.TButton', text="Добавить", command=self.add_gas_record, width=btn_width)
        self.gas_add_btn.pack(side=tk.LEFT, padx=2)
        self.gas_add_btn.bind('<Return>', lambda e: self.add_gas_record())

        self.gas_edit_btn = ttk.Button(btn_frame, style='Action.TButton', text="Редактировать", command=self.edit_gas_record, state=tk.DISABLED, width=btn_width)
        self.gas_edit_btn.pack(side=tk.LEFT, padx=2)

        self.gas_cancel_btn = ttk.Button(btn_frame, style='Action.TButton', text="Очистить", command=self.cancel_gas_edit, width=btn_width)
        self.gas_cancel_btn.pack(side=tk.LEFT, padx=2)

        del_btn = ttk.Button(btn_frame, style='Action.TButton', text="Удалить", command=self.delete_gas_record, width=btn_width)
        del_btn.pack(side=tk.LEFT, padx=2)

        diff_frame = tk.LabelFrame(bottom_frame, text=" Разница между последними данными ", 
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.gas_diff_hint = tk.Label(diff_container, 
                                      text="Разница рассчитывается по м³", 
                                      bg='#2b2b2b', fg='#888888', 
                                      font=('Segoe UI', 13),
                                      anchor=tk.CENTER)
        self.gas_diff_hint.pack(expand=True, fill=tk.BOTH)

        self.gas_diff_content = tk.Frame(diff_container, bg='#2b2b2b')
        diff_font = ('Segoe UI', 16, 'bold') if self.screen_width < 1024 else ('Segoe UI', 20, 'bold')
        self.gas_diff_value = tk.Label(self.gas_diff_content, text="-- м³", 
                                       bg='#2b2b2b', fg='#ffffff', 
                                       font=diff_font,
                                       anchor=tk.CENTER)
        self.gas_diff_value.pack(expand=True, fill=tk.BOTH)

        self.gas_selected_date = None
        self.gas_editing = False
        return page

    def load_gas_data(self):
        try:
            current_selection = self.gas_tree.selection()
            current_date = None
            if current_selection:
                item = current_selection[0]
                current_date = self.gas_tree.item(item, 'values')[0]

            for row in self.gas_tree.get_children():
                self.gas_tree.delete(row)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT date, reading, tut, gkal FROM gas ORDER BY date DESC")
            rows = c.fetchall()
            conn.close()

            self.last_update['gas'] = self.get_table_hash('gas', ['date', 'reading', 'coefficient', 'tut', 'gkal'])

            if len(rows) > 0:
                max_rows = 6 if self.screen_height < 768 else 8
                visible_rows = min(len(rows), max_rows)
                self.gas_tree.configure(height=visible_rows)
            else:
                self.gas_tree.configure(height=4)

            for i, row in enumerate(rows):
                formatted_row = (
                    self.format_date_display(row[0]),
                    self.format_number(row[1]),
                    self.format_number(row[2]),
                    self.format_number(row[3])
                )
                tag = 'even' if i % 2 == 0 else 'odd'
                self.gas_tree.insert('', tk.END, values=formatted_row, tags=(tag,))

            if current_date:
                for item in self.gas_tree.get_children():
                    if self.gas_tree.item(item, 'values')[0] == current_date:
                        self.gas_tree.selection_set(item)
                        self.gas_tree.focus(item)
                        values = self.gas_tree.item(item, 'values')
                        self.gas_selected_date = current_date
                        self.gas_edit_btn.config(state=tk.NORMAL)
                        self.gas_diff_hint.pack_forget()
                        self.gas_diff_content.pack(fill=tk.BOTH, expand=True)
                        
                        # Разница по м³
                        try:
                            cur = float(values[1]) if values[1] != "—" else 0
                        except:
                            cur = 0
                        try:
                            dt = datetime.strptime(current_date, '%d.%m.%Y')
                            date_str = dt.strftime('%Y-%m-%d')
                        except:
                            date_str = ''
                        conn2 = sqlite3.connect(self.db_path)
                        c2 = conn2.cursor()
                        c2.execute("SELECT reading FROM gas WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
                        prev = c2.fetchone()
                        conn2.close()
                        if prev:
                            diff = cur - prev[0]
                        else:
                            diff = 0
                        self.gas_diff_value.config(text=f"{self.format_number(diff)} м³")
                        
                        try:
                            self.gas_month_cal.set_date(dt)
                        except:
                            pass
                        break
            else:
                self.gas_selected_date = None
                self.gas_editing = False
                self.gas_edit_btn.config(state=tk.DISABLED)
                self.gas_add_btn.config(text="Добавить")
                self.gas_cancel_btn.config(text="Очистить")
                self.clear_gas_diff()
                self.gas_month_cal.set_date(datetime.now())

            if not self.gas_editing:
                self.gas_reading_entry.delete(0, tk.END)
                self.gas_coef_entry.delete(0, tk.END)
                self.gas_coef_entry.insert(0, "0.185")

        except Exception as e:
            print(f"Ошибка загрузки газа: {e}")

    def clear_gas_diff(self):
        self.gas_diff_hint.pack(expand=True, fill=tk.BOTH)
        self.gas_diff_content.pack_forget()
        self.gas_diff_value.config(text="-- м³")

    def on_gas_select(self, event):
        selected = self.gas_tree.selection()
        if not selected:
            self.gas_edit_btn.config(state=tk.DISABLED)
            self.clear_gas_diff()
            return
        item = selected[0]
        values = self.gas_tree.item(item, 'values')
        date_display = values[0]
        self.gas_selected_date = date_display
        self.gas_edit_btn.config(state=tk.NORMAL)

        self.gas_diff_hint.pack_forget()
        self.gas_diff_content.pack(fill=tk.BOTH, expand=True)

        # Заполняем поля для редактирования
        if self.gas_editing:
            self.gas_reading_entry.delete(0, tk.END)
            if values[1] != "—":
                self.gas_reading_entry.insert(0, values[1])
            # Загружаем коэффициент из базы
            try:
                dt = datetime.strptime(date_display, '%d.%m.%Y')
                date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = ''
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT coefficient FROM gas WHERE date = ?", (date_str,))
            res = c.fetchone()
            conn.close()
            self.gas_coef_entry.delete(0, tk.END)
            if res:
                self.gas_coef_entry.insert(0, str(res[0]))
            else:
                self.gas_coef_entry.insert(0, "0.185")

        # Разница по м³
        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            self.gas_month_cal.set_date(dt)
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = ''

        try:
            cur = float(values[1]) if values[1] != "—" else 0
        except:
            cur = 0

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT reading FROM gas WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
        prev = c.fetchone()
        conn.close()

        if prev:
            diff = cur - prev[0]
        else:
            diff = 0

        self.gas_diff_value.config(text=f"{self.format_number(diff)} м³")

    def cancel_gas_edit(self):
        self.gas_editing = False
        self.gas_edit_btn.config(state=tk.DISABLED)
        self.gas_add_btn.config(text="Добавить")
        self.gas_cancel_btn.config(text="Очистить")
        self.gas_reading_entry.delete(0, tk.END)
        self.gas_coef_entry.delete(0, tk.END)
        self.gas_coef_entry.insert(0, "0.185")
        self.gas_month_cal.set_date(datetime.now())
        self.gas_tree.selection_remove(self.gas_tree.selection())
        self.gas_selected_date = None
        self.clear_gas_diff()

    def add_gas_record(self):
        selected_date = self.gas_month_cal.get_date()
        if not selected_date:
            messagebox.showerror("Ошибка", "Выберите дату.")
            return
        date_str = selected_date.strftime('%Y-%m-%d')

        def get_float_or_none(val):
            val = val.strip()
            if val == '':
                return None
            try:
                return float(val)
            except ValueError:
                raise ValueError(f"Некорректное число: '{val}'")

        try:
            reading = get_float_or_none(self.gas_reading_entry.get())
            coefficient = get_float_or_none(self.gas_coef_entry.get())
            if coefficient is None or coefficient == 0:
                coefficient = 0.185
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        # Расчёт: Т.У.Т = (м³ * 1.15) / 1000, Гкал = Т.У.Т / Коэффициент
        tut = (reading * 1.15) / 1000 if reading is not None else None
        gkal = (tut / coefficient) if tut is not None else None

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Если это редактирование, удаляем старую запись
        if self.gas_editing:
            old_date_str = datetime.strptime(self.gas_selected_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            c.execute("DELETE FROM gas WHERE date = ?", (old_date_str,))

        c.execute("SELECT date FROM gas WHERE date = ?", (date_str,))
        if c.fetchone():
            if not messagebox.askyesno("Повтор", f"Запись за {date_str} уже существует. Перезаписать?"):
                conn.close()
                return
            c.execute("DELETE FROM gas WHERE date = ?", (date_str,))
        c.execute("INSERT INTO gas (date, reading, coefficient, tut, gkal) VALUES (?, ?, ?, ?, ?)",
                  (date_str, reading, coefficient, tut, gkal))
        conn.commit()
        conn.close()

        self.gas_editing = False
        self.gas_edit_btn.config(state=tk.DISABLED)
        self.gas_add_btn.config(text="Добавить")
        self.gas_cancel_btn.config(text="Очистить")
        self.gas_reading_entry.delete(0, tk.END)
        self.gas_coef_entry.delete(0, tk.END)
        self.gas_coef_entry.insert(0, "0.185")
        self.gas_month_cal.set_date(datetime.now())
        self.load_gas_data()
        messagebox.showinfo("Успех", f"Данные за {date_str} сохранены.")

    def edit_gas_record(self):
        if not self.gas_selected_date:
            messagebox.showwarning("Предупреждение", "Сначала выберите запись.")
            return
        selected = self.gas_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.gas_tree.item(item, 'values')
        date_display = values[0]
        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            self.gas_month_cal.set_date(dt)
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = ''

        self.gas_reading_entry.delete(0, tk.END)
        if values[1] != "—":
            self.gas_reading_entry.insert(0, values[1])

        # Загружаем коэффициент из БД
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT coefficient FROM gas WHERE date = ?", (date_str,))
        res = c.fetchone()
        conn.close()
        self.gas_coef_entry.delete(0, tk.END)
        if res and res[0]:
            self.gas_coef_entry.insert(0, str(res[0]))
        else:
            self.gas_coef_entry.insert(0, "0.185")

        self.gas_editing = True
        self.gas_add_btn.config(text="Обновить")
        self.gas_cancel_btn.config(text="Отмена")

    def delete_gas_record(self):
        selected = self.gas_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись.")
            return
        item = selected[0]
        date_display = self.gas_tree.item(item, 'values')[0]
        if messagebox.askyesno("Удаление", f"Удалить запись за {date_display}?"):
            try:
                dt = datetime.strptime(date_display, '%d.%m.%Y')
                date_str = dt.strftime('%Y-%m-%d')
            except:
                return
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM gas WHERE date = ?", (date_str,))
            conn.commit()
            conn.close()
            self.load_gas_data()
            messagebox.showinfo("Успех", "Запись удалена.")
            
    def on_enter_pressed(self, event):
        # Определяем, какая страница сейчас открыта
        active_page = None
        for name, page in self.pages.items():
            if page.winfo_ismapped():
                active_page = name
                break

        if active_page == 'electricity':
            self.add_electricity_record()
        elif active_page == 'water':
            self.add_water_record()
        elif active_page == 'gas':
            self.add_gas_record()

    def auto_update(self):
        while self.running:
            time.sleep(2)
            if not self.running:
                break
            for page_name in ['electricity', 'water', 'gas']:
                try:
                    if self.has_data_changed(page_name):
                        # Убрали print с сообщением об изменениях
                        self.root.after(0, lambda p=page_name: self.load_page_data(p))
                except Exception as e:
                    # Убрали print с ошибкой
                    pass

    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnergyApp(root)
    root.mainloop()