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

class EnergyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ежемесячные отчёты")
        
        self.root.withdraw()
        self.set_app_icon()
        
        # Получаем размер экрана
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Определяем размер окна в зависимости от экрана
        if self.screen_width < 1024:
            # Для маленьких экранов - почти на весь экран
            window_width = self.screen_width - 20
            window_height = self.screen_height - 40
            self.root.geometry(f"{window_width}x{window_height}+10+10")
        else:
            # Для больших экранов - развёрнутое окно
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
        
        # Создаём main_container ПЕРЕД create_navigation
        self.main_container = ttk.Frame(self.root, style='TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.create_navigation()

        self.page_container = ttk.Frame(self.main_container, style='TFrame')
        self.page_container.pack(fill=tk.BOTH, expand=True)

        # Инициализируем last_update ДО загрузки данных
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
            'gas': 'ico/gaz.png'
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
        
        style.configure('Nav.TButton', 
                        background='#2d6a4f',
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        style.map('Nav.TButton', 
                  background=[('active', '#409f6f')],
                  foreground=[('active', '#ffffff')])
        
        style.configure('ActiveNav.TButton',
                        background='#d4851f',
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        style.map('ActiveNav.TButton',
                  background=[('active', '#e8a035')],
                  foreground=[('active', '#ffffff')])
        
        style.configure('Action.TButton', 
                        background='#3a6b8a',
                        foreground='#ffffff',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        padding=nav_padding)
        style.map('Action.TButton', 
                  background=[('active', '#5a8aaa')],
                  foreground=[('active', '#ffffff')])
        
        style.configure('TEntry', fieldbackground='#3c3c3c', foreground=fg, insertcolor=fg,
                        borderwidth=1, relief='solid')
        
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
        c.execute('''CREATE TABLE IF NOT EXISTS electricity (
                        month TEXT PRIMARY KEY,
                        meter1_reading REAL,
                        meter2_reading REAL,
                        meter3_reading REAL
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS water (
                        month TEXT PRIMARY KEY,
                        glavny REAL,
                        du20 REAL,
                        du80 REAL,
                        kan_v REAL,
                        kan_tr REAL,
                        kan_tpr REAL,
                        kupazh REAL
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS gas (
                        month TEXT PRIMARY KEY,
                        reading REAL
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
        title = ttk.Label(nav_frame, text="⚡ ЭНЕРГОСЛУЖБА", font=('Segoe UI', title_font_size, 'bold'))
        title.grid(row=0, column=0, padx=(40, 0), pady=5, sticky='w')

        btn_frame = ttk.Frame(nav_frame, style='TFrame')
        btn_frame.grid(row=0, column=2, padx=(0, 20), pady=5, sticky='e')

        self.nav_buttons = {}
        
        if self.screen_width < 1024:
            buttons = [
                ('Электроэнергия', 'electricity', 'energy'),
                ('Вода', 'water', 'water'),
                ('Газ', 'gas', 'gas')
            ]
        else:
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
        """Получает хеш-сумму всех данных таблицы для проверки изменений"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(f"SELECT {', '.join(columns)} FROM {table_name} ORDER BY month")
            rows = c.fetchall()
            conn.close()
            
            # Преобразуем данные в строку и вычисляем хеш
            data_str = json.dumps(rows, sort_keys=True, default=str)
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception as e:
            print(f"Ошибка получения хеша для {table_name}: {e}")
            return None

    def has_data_changed(self, page_name):
        """Проверяет, изменились ли данные в таблице (по хешу всех данных)"""
        try:
            if page_name == 'electricity':
                columns = ['month', 'meter1_reading', 'meter2_reading', 'meter3_reading']
            elif page_name == 'water':
                columns = ['month', 'glavny', 'du20', 'du80', 'kan_v', 'kan_tr', 'kan_tpr', 'kupazh']
            elif page_name == 'gas':
                columns = ['month', 'reading']
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
            return "0"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        elif isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    # ---------- СТРАНИЦА ЭЛЕКТРОЭНЕРГИИ ----------
    def create_electricity_page(self):
        page = ttk.Frame(self.page_container, style='TFrame')

        font_size = 12 if self.screen_width < 1024 else 14
        title = ttk.Label(page, text="Отчёт по электроэнергии", font=('Segoe UI', font_size, 'bold'))
        title.pack(pady=5)

        tree_frame = ttk.Frame(page, style='TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=5)

        columns = ('Месяц', 'Винзавод 1', 'Винзавод 2', 'Винзавод БН')
        self.electricity_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        col_width = 80 if self.screen_width < 1024 else 120
        
        for col in columns:
            self.electricity_tree.heading(col, text=col)
            self.electricity_tree.column(col, anchor=tk.CENTER, width=col_width, minwidth=60)

        self.electricity_tree.tag_configure('even', background='#3d3d3d')
        self.electricity_tree.tag_configure('odd', background='#353535')

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.electricity_tree.yview)
        self.electricity_tree.configure(yscrollcommand=scroll.set)
        self.electricity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.electricity_tree.bind('<<TreeviewSelect>>', self.on_electricity_select)

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

        fields = [
            ('Месяц:', 'month_entry', 12),
            ('Винзавод 1 (кВт):', 'm1_entry', 12),
            ('Винзавод 2 (кВт):', 'm2_entry', 12),
            ('Винзавод БН (кВт):', 'm3_entry', 12),
        ]
        self.elec_entries = {}
        for i, (label, key, width) in enumerate(fields):
            lbl = tk.Label(input_container, text=label, bg='#2b2b2b', fg='#ffffff', 
                          font=('Segoe UI', 8), anchor=tk.W)
            lbl.grid(row=i, column=0, padx=2, pady=2, sticky=tk.W)
            entry = ttk.Entry(input_container, width=width)
            entry.grid(row=i, column=1, padx=2, pady=2, sticky=tk.W)
            self.elec_entries[key] = entry

        default_month = datetime.now().strftime('%Y-%m')
        self.elec_entries['month_entry'].insert(0, default_month)

        btn_frame = tk.Frame(input_container, bg='#2b2b2b')
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(10, 0))

        if self.screen_width < 1024:
            btn_width = 15
            add_text = "Добавить"
            edit_text = "Редактировать"
            cancel_text = "Очистить"
            del_text = "Удалить"
        else:
            btn_width = 15
            add_text = "Добавить"
            edit_text = "Редактировать"
            cancel_text = "Очистить"
            del_text = "Удалить"
        
        self.elec_add_btn = ttk.Button(btn_frame, style='Action.TButton', text=add_text, command=self.add_electricity_record, width=btn_width)
        self.elec_add_btn.pack(side=tk.LEFT, padx=2)

        self.elec_edit_btn = ttk.Button(btn_frame, style='Action.TButton', text=edit_text, command=self.edit_electricity_record, state=tk.DISABLED, width=btn_width)
        self.elec_edit_btn.pack(side=tk.LEFT, padx=2)

        self.elec_cancel_btn = ttk.Button(btn_frame, style='Action.TButton', text=cancel_text, command=self.cancel_electricity_edit, width=btn_width)
        self.elec_cancel_btn.pack(side=tk.LEFT, padx=2)

        del_btn = ttk.Button(btn_frame, style='Action.TButton', text=del_text, command=self.delete_electricity_record, width=btn_width)
        del_btn.pack(side=tk.LEFT, padx=2)

        diff_frame = tk.LabelFrame(bottom_frame, text=" Разница ", 
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.elec_diff_hint = tk.Label(diff_container, 
                                       text="Укажите нужный месяц в таблице для получения разницы", 
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

        self.elec_selected_month = None
        self.elec_editing = False

        return page

    def load_electricity_data(self):
        try:
            current_selection = self.electricity_tree.selection()
            current_month = None
            if current_selection:
                item = current_selection[0]
                current_month = self.electricity_tree.item(item, 'values')[0]
            
            for row in self.electricity_tree.get_children():
                self.electricity_tree.delete(row)

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT month, meter1_reading, meter2_reading, meter3_reading FROM electricity ORDER BY month DESC")
            rows = c.fetchall()
            conn.close()

            # Обновляем хеш после загрузки
            self.last_update['electricity'] = self.get_table_hash('electricity', ['month', 'meter1_reading', 'meter2_reading', 'meter3_reading'])

            if len(rows) > 0:
                max_rows = 6 if self.screen_height < 768 else 8
                visible_rows = min(len(rows), max_rows)
                self.electricity_tree.configure(height=visible_rows)
            else:
                self.electricity_tree.configure(height=4)

            for i, row in enumerate(rows):
                formatted_row = (
                    row[0],
                    self.format_number(row[1]),
                    self.format_number(row[2]),
                    self.format_number(row[3])
                )
                tag = 'even' if i % 2 == 0 else 'odd'
                self.electricity_tree.insert('', tk.END, values=formatted_row, tags=(tag,))

            if current_month:
                for item in self.electricity_tree.get_children():
                    if self.electricity_tree.item(item, 'values')[0] == current_month:
                        self.electricity_tree.selection_set(item)
                        self.electricity_tree.focus(item)
                        values = self.electricity_tree.item(item, 'values')
                        self.elec_selected_month = current_month
                        self.elec_edit_btn.config(state=tk.NORMAL)
                        self.show_electricity_diff(current_month, values)
                        break
            else:
                self.elec_selected_month = None
                self.elec_editing = False
                self.elec_edit_btn.config(state=tk.DISABLED)
                self.elec_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
                self.elec_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
                self.clear_electricity_diff()
            
            if not self.elec_editing:
                for key in self.elec_entries:
                    if key != 'month_entry':
                        self.elec_entries[key].delete(0, tk.END)
                self.elec_entries['month_entry'].delete(0, tk.END)
                self.elec_entries['month_entry'].insert(0, datetime.now().strftime('%Y-%m'))
            
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
        month = values[0]
        self.elec_selected_month = month
        self.elec_edit_btn.config(state=tk.NORMAL)
        self.show_electricity_diff(month, values)
        
        if self.elec_editing:
            self.elec_entries['month_entry'].delete(0, tk.END)
            self.elec_entries['month_entry'].insert(0, month)
            self.elec_entries['m1_entry'].delete(0, tk.END)
            self.elec_entries['m1_entry'].insert(0, values[1])
            self.elec_entries['m2_entry'].delete(0, tk.END)
            self.elec_entries['m2_entry'].insert(0, values[2])
            self.elec_entries['m3_entry'].delete(0, tk.END)
            self.elec_entries['m3_entry'].insert(0, values[3])

    def clear_electricity_diff(self):
        self.elec_diff_hint.pack(expand=True, fill=tk.BOTH)
        self.elec_diff_content.pack_forget()
        
        self.elec_diff_m1.config(text="Винзавод 1: -- кВт")
        self.elec_diff_m2.config(text="Винзавод 2: -- кВт")
        self.elec_diff_m3.config(text="Винзавод БН: -- кВт")
        self.elec_diff_total.config(text="Общий расход: -- кВт")

    def show_electricity_diff(self, month, values):
        self.elec_diff_hint.pack_forget()
        self.elec_diff_content.pack(fill=tk.BOTH, expand=True)
        
        try:
            cur_m1 = float(values[1]) if values[1] else 0
            cur_m2 = float(values[2]) if values[2] else 0
            cur_m3 = float(values[3]) if values[3] else 0
        except:
            cur_m1 = cur_m2 = cur_m3 = 0

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT meter1_reading, meter2_reading, meter3_reading FROM electricity WHERE month < ? ORDER BY month DESC LIMIT 1", (month,))
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
        self.elec_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
        self.elec_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
        
        for key in self.elec_entries:
            if key != 'month_entry':
                self.elec_entries[key].delete(0, tk.END)
        self.elec_entries['month_entry'].delete(0, tk.END)
        self.elec_entries['month_entry'].insert(0, datetime.now().strftime('%Y-%m'))
        
        self.electricity_tree.selection_remove(self.electricity_tree.selection())
        self.elec_selected_month = None
        self.clear_electricity_diff()

    def add_electricity_record(self):
        month = self.elec_entries['month_entry'].get().strip()
        try:
            m1 = float(self.elec_entries['m1_entry'].get().strip())
            m2 = float(self.elec_entries['m2_entry'].get().strip())
            m3 = float(self.elec_entries['m3_entry'].get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые показания.")
            return

        if not month:
            messagebox.showerror("Ошибка", "Введите месяц в формате ГГГГ-ММ.")
            return
        try:
            datetime.strptime(month, '%Y-%m')
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат месяца. Используйте ГГГГ-ММ.")
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT month FROM electricity WHERE month = ?", (month,))
        if c.fetchone():
            if not messagebox.askyesno("Повтор", f"Запись за {month} уже существует. Перезаписать?"):
                conn.close()
                return
            c.execute("DELETE FROM electricity WHERE month = ?", (month,))

        c.execute("INSERT INTO electricity (month, meter1_reading, meter2_reading, meter3_reading) VALUES (?, ?, ?, ?)",
                  (month, m1, m2, m3))
        conn.commit()
        conn.close()

        self.elec_editing = False
        self.elec_edit_btn.config(state=tk.DISABLED)
        self.elec_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
        self.elec_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
        
        for key in self.elec_entries:
            if key != 'month_entry':
                self.elec_entries[key].delete(0, tk.END)
        self.elec_entries['month_entry'].delete(0, tk.END)
        self.elec_entries['month_entry'].insert(0, datetime.now().strftime('%Y-%m'))

        self.load_electricity_data()
        messagebox.showinfo("Успех", f"Данные за {month} сохранены.")

    def edit_electricity_record(self):
        if not self.elec_selected_month:
            messagebox.showwarning("Предупреждение", "Сначала выберите запись для редактирования.")
            return
        selected = self.electricity_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.electricity_tree.item(item, 'values')
        month = values[0]
        
        self.elec_entries['month_entry'].delete(0, tk.END)
        self.elec_entries['month_entry'].insert(0, month)
        self.elec_entries['m1_entry'].delete(0, tk.END)
        self.elec_entries['m1_entry'].insert(0, values[1])
        self.elec_entries['m2_entry'].delete(0, tk.END)
        self.elec_entries['m2_entry'].insert(0, values[2])
        self.elec_entries['m3_entry'].delete(0, tk.END)
        self.elec_entries['m3_entry'].insert(0, values[3])
        
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
        month = values[0]
        if messagebox.askyesno("Удаление", f"Удалить запись за {month}?"):
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM electricity WHERE month = ?", (month,))
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

        columns = ('Месяц', 'Гл.ввод', 'Ду20', 'Ду80', 'Кан.V', 'Кан.Тр', 'Кан.Тпр', 'Купаж')
        self.water_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        col_width = 60 if self.screen_width < 1024 else 90
        
        for col in columns:
            self.water_tree.heading(col, text=col)
            self.water_tree.column(col, anchor=tk.CENTER, width=col_width, minwidth=50)

        self.water_tree.tag_configure('even', background='#3d3d3d')
        self.water_tree.tag_configure('odd', background='#353535')

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.water_tree.yview)
        self.water_tree.configure(yscrollcommand=scroll.set)
        self.water_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.water_tree.bind('<<TreeviewSelect>>', self.on_water_select)

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

        if self.screen_width < 1024:
            water_fields = [
                ('Месяц (ГГГГ-ММ):', 'month_entry', 12),
                ('Главный ввод (м³):', 'glavny', 12),
                ('Ду20 (м³):', 'du20', 12),
                ('Ду80 (м³):', 'du80', 12),
                ('Канализация V (м³):', 'kan_v', 12),
                ('Канализация Тр (м³):', 'kan_tr', 12),
                ('Канализация Тпр:', 'kan_tpr', 12),
                ('Купаж (м³):', 'kupazh', 12),
            ]
        else:
            water_fields = [
                ('Месяц (ГГГГ-ММ):', 'month_entry', 12),
                ('Главный ввод (м³):', 'glavny', 12),
                ('Ду20 (м³):', 'du20', 12),
                ('Ду80 (м³):', 'du80', 12),
                ('Канализация V (м³):', 'kan_v', 12),
                ('Канализация Тр (м³):', 'kan_tr', 12),
                ('Канализация Тпр:', 'kan_tpr', 12),
                ('Купаж (м³):', 'kupazh', 12),
            ]
        
        self.water_entries = {}
        font_size_label = 8 if self.screen_width < 1024 else 10
        for i, (label, key, width) in enumerate(water_fields):
            lbl = tk.Label(input_container, text=label, bg='#2b2b2b', fg='#ffffff', 
                          font=('Segoe UI', font_size_label), anchor=tk.W)
            lbl.grid(row=i, column=0, padx=2, pady=2, sticky=tk.W)
            entry = ttk.Entry(input_container, width=width)
            entry.grid(row=i, column=1, padx=2, pady=2, sticky=tk.W)
            self.water_entries[key] = entry

        default_month = datetime.now().strftime('%Y-%m')
        self.water_entries['month_entry'].insert(0, default_month)

        btn_frame = tk.Frame(input_container, bg='#2b2b2b')
        btn_frame.grid(row=len(water_fields), column=0, columnspan=2, pady=(10, 0))

        if self.screen_width < 1024:
            btn_width = 15
            add_text = "➕ Добавить"
            edit_text = "Редактировать"
            cancel_text = "Очистить"
            del_text = "Удалить"
        else:
            btn_width = 15
            add_text = "➕ Добавить"
            edit_text = "Редактировать"
            cancel_text = "Очистить"
            del_text = "Удалить"
        
        self.water_add_btn = ttk.Button(btn_frame, style='Action.TButton', text=add_text, command=self.add_water_record, width=btn_width)
        self.water_add_btn.pack(side=tk.LEFT, padx=2)

        self.water_edit_btn = ttk.Button(btn_frame, style='Action.TButton', text=edit_text, command=self.edit_water_record, state=tk.DISABLED, width=btn_width)
        self.water_edit_btn.pack(side=tk.LEFT, padx=2)

        self.water_cancel_btn = ttk.Button(btn_frame, style='Action.TButton', text=cancel_text, command=self.cancel_water_edit, width=btn_width)
        self.water_cancel_btn.pack(side=tk.LEFT, padx=2)

        del_btn = ttk.Button(btn_frame, style='Action.TButton', text=del_text, command=self.delete_water_record, width=btn_width)
        del_btn.pack(side=tk.LEFT, padx=2)

        diff_frame = tk.LabelFrame(bottom_frame, text=" Разница ", 
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.water_diff_hint = tk.Label(diff_container, 
                                        text="Укажите нужный месяц в таблице для получения разницы", 
                                        bg='#2b2b2b', fg='#888888', 
                                        font=('Segoe UI', 13),
                                        anchor=tk.CENTER)
        self.water_diff_hint.pack(expand=True, fill=tk.BOTH)

        self.water_diff_content = tk.Frame(diff_container, bg='#2b2b2b')

        font_diff = 8 if self.screen_width < 1024 else 10
        
        self.water_diff_glavny = tk.Label(self.water_diff_content, text="Главный ввод: -- м³", 
                                          bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                          anchor=tk.W)
        self.water_diff_glavny.pack(fill=tk.X, pady=2)

        self.water_diff_du20 = tk.Label(self.water_diff_content, text="Ду20: -- м³", 
                                        bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                        anchor=tk.W)
        self.water_diff_du20.pack(fill=tk.X, pady=2)

        self.water_diff_du80 = tk.Label(self.water_diff_content, text="Ду80: -- м³", 
                                        bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                        anchor=tk.W)
        self.water_diff_du80.pack(fill=tk.X, pady=2)

        self.water_diff_kan_v = tk.Label(self.water_diff_content, text="Канализация V: -- м³", 
                                         bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                         anchor=tk.W)
        self.water_diff_kan_v.pack(fill=tk.X, pady=2)

        self.water_diff_kan_tr = tk.Label(self.water_diff_content, text="Канализация Тр: -- м³", 
                                          bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                          anchor=tk.W)
        self.water_diff_kan_tr.pack(fill=tk.X, pady=2)

        self.water_diff_kan_tpr = tk.Label(self.water_diff_content, text="Канализация Тпр: --", 
                                           bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                           anchor=tk.W)
        self.water_diff_kan_tpr.pack(fill=tk.X, pady=2)

        self.water_diff_kupazh = tk.Label(self.water_diff_content, text="Купаж: -- м³", 
                                          bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_diff),
                                          anchor=tk.W)
        self.water_diff_kupazh.pack(fill=tk.X, pady=2)

        self.water_selected_month = None
        self.water_editing = False
        return page

    def load_water_data(self):
        try:
            current_selection = self.water_tree.selection()
            current_month = None
            if current_selection:
                item = current_selection[0]
                current_month = self.water_tree.item(item, 'values')[0]
            
            for row in self.water_tree.get_children():
                self.water_tree.delete(row)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT month, glavny, du20, du80, kan_v, kan_tr, kan_tpr, kupazh FROM water ORDER BY month DESC")
            rows = c.fetchall()
            conn.close()

            # Обновляем хеш после загрузки
            self.last_update['water'] = self.get_table_hash('water', ['month', 'glavny', 'du20', 'du80', 'kan_v', 'kan_tr', 'kan_tpr', 'kupazh'])

            if len(rows) > 0:
                max_rows = 6 if self.screen_height < 768 else 8
                visible_rows = min(len(rows), max_rows)
                self.water_tree.configure(height=visible_rows)
            else:
                self.water_tree.configure(height=4)

            for i, row in enumerate(rows):
                formatted_row = (
                    row[0],
                    self.format_number(row[1]),
                    self.format_number(row[2]),
                    self.format_number(row[3]),
                    self.format_number(row[4]),
                    self.format_number(row[5]),
                    self.format_number(row[6]),
                    self.format_number(row[7])
                )
                tag = 'even' if i % 2 == 0 else 'odd'
                self.water_tree.insert('', tk.END, values=formatted_row, tags=(tag,))
            
            if current_month:
                for item in self.water_tree.get_children():
                    if self.water_tree.item(item, 'values')[0] == current_month:
                        self.water_tree.selection_set(item)
                        self.water_tree.focus(item)
                        values = self.water_tree.item(item, 'values')
                        self.water_selected_month = current_month
                        self.water_edit_btn.config(state=tk.NORMAL)
                        self.show_water_diff(current_month, values)
                        break
            else:
                self.water_selected_month = None
                self.water_editing = False
                self.water_edit_btn.config(state=tk.DISABLED)
                self.water_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
                self.water_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
                self.clear_water_diff()
            
            if not self.water_editing:
                for key in self.water_entries:
                    if key != 'month_entry':
                        self.water_entries[key].delete(0, tk.END)
                self.water_entries['month_entry'].delete(0, tk.END)
                self.water_entries['month_entry'].insert(0, datetime.now().strftime('%Y-%m'))
            
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
        month = values[0]
        self.water_selected_month = month
        self.water_edit_btn.config(state=tk.NORMAL)
        self.show_water_diff(month, values)
        
        if self.water_editing:
            keys = ['month_entry', 'glavny', 'du20', 'du80', 'kan_v', 'kan_tr', 'kan_tpr', 'kupazh']
            for i, key in enumerate(keys):
                self.water_entries[key].delete(0, tk.END)
                if i == 0:
                    self.water_entries[key].insert(0, month)
                else:
                    self.water_entries[key].insert(0, values[i])

    def clear_water_diff(self):
        self.water_diff_hint.pack(expand=True, fill=tk.BOTH)
        self.water_diff_content.pack_forget()
        
        self.water_diff_glavny.config(text="Главный ввод: -- м³")
        self.water_diff_du20.config(text="Ду20: -- м³")
        self.water_diff_du80.config(text="Ду80: -- м³")
        self.water_diff_kan_v.config(text="Канализация V: -- м³")
        self.water_diff_kan_tr.config(text="Канализация Тр: -- м³")
        self.water_diff_kan_tpr.config(text="Канализация Тпр: --")
        self.water_diff_kupazh.config(text="Купаж: -- м³")

    def show_water_diff(self, month, values):
        self.water_diff_hint.pack_forget()
        self.water_diff_content.pack(fill=tk.BOTH, expand=True)
        
        try:
            cur = [float(x) if x else 0 for x in values[1:]]
        except:
            cur = [0] * 7
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT glavny, du20, du80, kan_v, kan_tr, kan_tpr, kupazh FROM water WHERE month < ? ORDER BY month DESC LIMIT 1", (month,))
        prev = c.fetchone()
        conn.close()
        
        if prev:
            prev_vals = [float(x) if x is not None else 0 for x in prev]
            diffs = [cur[i] - prev_vals[i] for i in range(7)]
        else:
            diffs = [0] * 7

        self.water_diff_glavny.config(text=f"Главный ввод: {self.format_number(diffs[0])} м³")
        self.water_diff_du20.config(text=f"Ду20: {self.format_number(diffs[1])} м³")
        self.water_diff_du80.config(text=f"Ду80: {self.format_number(diffs[2])} м³")
        self.water_diff_kan_v.config(text=f"Канализация V: {self.format_number(diffs[3])} м³")
        self.water_diff_kan_tr.config(text=f"Канализация Тр: {self.format_number(diffs[4])} м³")
        self.water_diff_kan_tpr.config(text=f"Канализация Тпр: {self.format_number(diffs[5])}")
        self.water_diff_kupazh.config(text=f"Купаж: {self.format_number(diffs[6])} м³")

    def cancel_water_edit(self):
        self.water_editing = False
        self.water_edit_btn.config(state=tk.DISABLED)
        self.water_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
        self.water_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
        
        for key in self.water_entries:
            if key != 'month_entry':
                self.water_entries[key].delete(0, tk.END)
        self.water_entries['month_entry'].delete(0, tk.END)
        self.water_entries['month_entry'].insert(0, datetime.now().strftime('%Y-%m'))
        
        self.water_tree.selection_remove(self.water_tree.selection())
        self.water_selected_month = None
        self.clear_water_diff()

    def add_water_record(self):
        month = self.water_entries['month_entry'].get().strip()
        try:
            vals = [float(self.water_entries[key].get().strip()) for key in ['glavny','du20','du80','kan_v','kan_tr','kan_tpr','kupazh']]
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые показания.")
            return
        if not month:
            messagebox.showerror("Ошибка", "Введите месяц.")
            return
        try:
            datetime.strptime(month, '%Y-%m')
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат месяца.")
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT month FROM water WHERE month = ?", (month,))
        if c.fetchone():
            if not messagebox.askyesno("Повтор", f"Запись за {month} уже существует. Перезаписать?"):
                conn.close()
                return
            c.execute("DELETE FROM water WHERE month = ?", (month,))
        
        c.execute("INSERT INTO water (month, glavny, du20, du80, kan_v, kan_tr, kan_tpr, kupazh) VALUES (?,?,?,?,?,?,?,?)",
                  (month, *vals))
        conn.commit()
        conn.close()

        self.water_editing = False
        self.water_edit_btn.config(state=tk.DISABLED)
        self.water_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
        self.water_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
        
        for key in self.water_entries:
            if key != 'month_entry':
                self.water_entries[key].delete(0, tk.END)
        self.water_entries['month_entry'].delete(0, tk.END)
        self.water_entries['month_entry'].insert(0, datetime.now().strftime('%Y-%m'))
        
        self.load_water_data()
        messagebox.showinfo("Успех", f"Данные за {month} сохранены.")

    def edit_water_record(self):
        if not self.water_selected_month:
            messagebox.showwarning("Предупреждение", "Сначала выберите запись.")
            return
        selected = self.water_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.water_tree.item(item, 'values')
        month = values[0]
        
        keys = ['month_entry', 'glavny', 'du20', 'du80', 'kan_v', 'kan_tr', 'kan_tpr', 'kupazh']
        for i, key in enumerate(keys):
            self.water_entries[key].delete(0, tk.END)
            if i == 0:
                self.water_entries[key].insert(0, month)
            else:
                self.water_entries[key].insert(0, values[i])
        
        self.water_editing = True
        self.water_add_btn.config(text="Обновить")
        self.water_cancel_btn.config(text="Отмена")

    def delete_water_record(self):
        selected = self.water_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись.")
            return
        item = selected[0]
        month = self.water_tree.item(item, 'values')[0]
        if messagebox.askyesno("Удаление", f"Удалить запись за {month}?"):
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM water WHERE month = ?", (month,))
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

        columns = ('Месяц', 'Показания (Гкал)')
        self.gas_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        col_width = 100 if self.screen_width < 1024 else 200
        
        self.gas_tree.heading('Месяц', text='Месяц')
        self.gas_tree.heading('Показания (Гкал)', text='Показания (Гкал)')
        self.gas_tree.column('Месяц', anchor=tk.CENTER, width=col_width, minwidth=60)
        self.gas_tree.column('Показания (Гкал)', anchor=tk.CENTER, width=col_width, minwidth=60)

        self.gas_tree.tag_configure('even', background='#3d3d3d')
        self.gas_tree.tag_configure('odd', background='#353535')

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.gas_tree.yview)
        self.gas_tree.configure(yscrollcommand=scroll.set)
        self.gas_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.gas_tree.bind('<<TreeviewSelect>>', self.on_gas_select)

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

        font_label = 8 if self.screen_width < 1024 else 10
        
        tk.Label(input_container, text="Месяц:", bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_label)).grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.gas_month_entry = ttk.Entry(input_container, width=10)
        self.gas_month_entry.grid(row=0, column=1, padx=2, pady=2, sticky=tk.W)
        self.gas_month_entry.insert(0, datetime.now().strftime('%Y-%m'))

        tk.Label(input_container, text="Показание (Гкал):", bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', font_label)).grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.gas_reading_entry = ttk.Entry(input_container, width=10)
        self.gas_reading_entry.grid(row=1, column=1, padx=2, pady=2, sticky=tk.W)

        btn_frame = tk.Frame(input_container, bg='#2b2b2b')
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        if self.screen_width < 1024:
            btn_width = 15
            add_text = "Добавить"
            edit_text = "Редактировать"
            cancel_text = "Очистить"
            del_text = "Удалить"
        else:
            btn_width = 15
            add_text = "Добавить"
            edit_text = "Редактировать"
            cancel_text = "Очистить"
            del_text = "Удалить"
        
        self.gas_add_btn = ttk.Button(btn_frame, style='Action.TButton', text=add_text, command=self.add_gas_record, width=btn_width)
        self.gas_add_btn.pack(side=tk.LEFT, padx=2)

        self.gas_edit_btn = ttk.Button(btn_frame, style='Action.TButton', text=edit_text, command=self.edit_gas_record, state=tk.DISABLED, width=btn_width)
        self.gas_edit_btn.pack(side=tk.LEFT, padx=2)

        self.gas_cancel_btn = ttk.Button(btn_frame, style='Action.TButton', text=cancel_text, command=self.cancel_gas_edit, width=btn_width)
        self.gas_cancel_btn.pack(side=tk.LEFT, padx=2)

        del_btn = ttk.Button(btn_frame, style='Action.TButton', text=del_text, command=self.delete_gas_record, width=btn_width)
        del_btn.pack(side=tk.LEFT, padx=2)

        diff_frame = tk.LabelFrame(bottom_frame, text=" Разница ", 
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.gas_diff_hint = tk.Label(diff_container, 
                                      text="Укажите нужный месяц в таблице для получения разницы", 
                                      bg='#2b2b2b', fg='#888888', 
                                      font=('Segoe UI', 13),
                                      anchor=tk.CENTER)
        self.gas_diff_hint.pack(expand=True, fill=tk.BOTH)

        self.gas_diff_content = tk.Frame(diff_container, bg='#2b2b2b')
        
        diff_font = ('Segoe UI', 16, 'bold') if self.screen_width < 1024 else ('Segoe UI', 20, 'bold')
        self.gas_diff_value = tk.Label(self.gas_diff_content, text="-- Гкал", 
                                       bg='#2b2b2b', fg='#ffffff', 
                                       font=diff_font,
                                       anchor=tk.CENTER)
        self.gas_diff_value.pack(expand=True, fill=tk.BOTH)

        self.gas_selected_month = None
        self.gas_editing = False
        return page

    def load_gas_data(self):
        try:
            current_selection = self.gas_tree.selection()
            current_month = None
            if current_selection:
                item = current_selection[0]
                current_month = self.gas_tree.item(item, 'values')[0]
            
            for row in self.gas_tree.get_children():
                self.gas_tree.delete(row)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT month, reading FROM gas ORDER BY month DESC")
            rows = c.fetchall()
            conn.close()

            # Обновляем хеш после загрузки
            self.last_update['gas'] = self.get_table_hash('gas', ['month', 'reading'])

            if len(rows) > 0:
                max_rows = 6 if self.screen_height < 768 else 8
                visible_rows = min(len(rows), max_rows)
                self.gas_tree.configure(height=visible_rows)
            else:
                self.gas_tree.configure(height=4)

            for i, row in enumerate(rows):
                formatted_row = (row[0], self.format_number(row[1]))
                tag = 'even' if i % 2 == 0 else 'odd'
                self.gas_tree.insert('', tk.END, values=formatted_row, tags=(tag,))
            
            if current_month:
                for item in self.gas_tree.get_children():
                    if self.gas_tree.item(item, 'values')[0] == current_month:
                        self.gas_tree.selection_set(item)
                        self.gas_tree.focus(item)
                        values = self.gas_tree.item(item, 'values')
                        self.gas_selected_month = current_month
                        self.gas_edit_btn.config(state=tk.NORMAL)
                        self.gas_diff_hint.pack_forget()
                        self.gas_diff_content.pack(fill=tk.BOTH, expand=True)
                        try:
                            cur = float(values[1]) if values[1] else 0
                        except:
                            cur = 0
                        conn2 = sqlite3.connect(self.db_path)
                        c2 = conn2.cursor()
                        c2.execute("SELECT reading FROM gas WHERE month < ? ORDER BY month DESC LIMIT 1", (current_month,))
                        prev = c2.fetchone()
                        conn2.close()
                        if prev:
                            diff = cur - prev[0]
                        else:
                            diff = 0
                        self.gas_diff_value.config(text=f"{self.format_number(diff)} Гкал")
                        break
            else:
                self.gas_selected_month = None
                self.gas_editing = False
                self.gas_edit_btn.config(state=tk.DISABLED)
                self.gas_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
                self.gas_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
                self.clear_gas_diff()
            
            if not self.gas_editing:
                self.gas_reading_entry.delete(0, tk.END)
                self.gas_month_entry.delete(0, tk.END)
                self.gas_month_entry.insert(0, datetime.now().strftime('%Y-%m'))
            
        except Exception as e:
            print(f"Ошибка загрузки газа: {e}")

    def clear_gas_diff(self):
        self.gas_diff_hint.pack(expand=True, fill=tk.BOTH)
        self.gas_diff_content.pack_forget()
        self.gas_diff_value.config(text="-- Гкал")

    def on_gas_select(self, event):
        selected = self.gas_tree.selection()
        if not selected:
            self.gas_edit_btn.config(state=tk.DISABLED)
            self.clear_gas_diff()
            return
        item = selected[0]
        values = self.gas_tree.item(item, 'values')
        month = values[0]
        self.gas_selected_month = month
        self.gas_edit_btn.config(state=tk.NORMAL)
        
        self.gas_diff_hint.pack_forget()
        self.gas_diff_content.pack(fill=tk.BOTH, expand=True)
        
        if self.gas_editing:
            self.gas_month_entry.delete(0, tk.END)
            self.gas_month_entry.insert(0, month)
            self.gas_reading_entry.delete(0, tk.END)
            self.gas_reading_entry.insert(0, values[1])
        
        try:
            cur = float(values[1]) if values[1] else 0
        except:
            cur = 0
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT reading FROM gas WHERE month < ? ORDER BY month DESC LIMIT 1", (month,))
        prev = c.fetchone()
        conn.close()
        
        if prev:
            diff = cur - prev[0]
        else:
            diff = 0
        
        self.gas_diff_value.config(text=f"{self.format_number(diff)} Гкал")

    def cancel_gas_edit(self):
        self.gas_editing = False
        self.gas_edit_btn.config(state=tk.DISABLED)
        self.gas_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
        self.gas_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
        
        self.gas_reading_entry.delete(0, tk.END)
        self.gas_month_entry.delete(0, tk.END)
        self.gas_month_entry.insert(0, datetime.now().strftime('%Y-%m'))
        
        self.gas_tree.selection_remove(self.gas_tree.selection())
        self.gas_selected_month = None
        self.clear_gas_diff()

    def add_gas_record(self):
        month = self.gas_month_entry.get().strip()
        try:
            reading = float(self.gas_reading_entry.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число.")
            return
        if not month:
            messagebox.showerror("Ошибка", "Введите месяц.")
            return
        try:
            datetime.strptime(month, '%Y-%m')
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат месяца.")
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT month FROM gas WHERE month = ?", (month,))
        if c.fetchone():
            if not messagebox.askyesno("Повтор", f"Запись за {month} уже существует. Перезаписать?"):
                conn.close()
                return
            c.execute("DELETE FROM gas WHERE month = ?", (month,))
        c.execute("INSERT INTO gas (month, reading) VALUES (?, ?)", (month, reading))
        conn.commit()
        conn.close()

        self.gas_editing = False
        self.gas_edit_btn.config(state=tk.DISABLED)
        self.gas_add_btn.config(text="Добавить" if self.screen_width >= 1024 else "Доб.")
        self.gas_cancel_btn.config(text="Очистить" if self.screen_width >= 1024 else "Оч.")
        
        self.gas_reading_entry.delete(0, tk.END)
        self.gas_month_entry.delete(0, tk.END)
        self.gas_month_entry.insert(0, datetime.now().strftime('%Y-%m'))
        
        self.load_gas_data()
        messagebox.showinfo("Успех", f"Данные за {month} сохранены.")

    def edit_gas_record(self):
        if not self.gas_selected_month:
            messagebox.showwarning("Предупреждение", "Сначала выберите запись.")
            return
        selected = self.gas_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.gas_tree.item(item, 'values')
        month = values[0]
        
        self.gas_month_entry.delete(0, tk.END)
        self.gas_month_entry.insert(0, month)
        self.gas_reading_entry.delete(0, tk.END)
        self.gas_reading_entry.insert(0, values[1])
        
        self.gas_editing = True
        self.gas_add_btn.config(text="Обновить")
        self.gas_cancel_btn.config(text="Отмена")

    def delete_gas_record(self):
        selected = self.gas_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись.")
            return
        item = selected[0]
        month = self.gas_tree.item(item, 'values')[0]
        if messagebox.askyesno("Удаление", f"Удалить запись за {month}?"):
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM gas WHERE month = ?", (month,))
            conn.commit()
            conn.close()
            self.load_gas_data()
            messagebox.showinfo("Успех", "Запись удалена.")

    def auto_update(self):
        """Фоновая задача для автоматического обновления данных"""
        print("Автообновление запущено")
        while self.running:
            time.sleep(2)
            if not self.running:
                break
            # Проверяем все страницы
            for page_name in ['electricity', 'water', 'gas']:
                try:
                    if self.has_data_changed(page_name):
                        print(f"Обнаружены изменения в {page_name}, обновляем...")
                        self.root.after(0, lambda p=page_name: self.load_page_data(p))
                except Exception as e:
                    print(f"Ошибка автообновления для {page_name}: {e}")
                    pass

    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnergyApp(root)
    root.mainloop()