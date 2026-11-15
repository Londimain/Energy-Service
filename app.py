import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime
import threading
import time
import hashlib
import json

from version import VERSION
from database import init_db
from styles import setup_style
from icons import set_app_icon, load_icons
from pages import ElectricityPageMixin, WaterPageMixin, GasPageMixin
from config import load_config, save_config
from settings import SettingsWindow
from about import AboutWindow


class ExitDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Выход")
        self.top.geometry("380x150")
        self.top.configure(bg='#2b2b2b')
        self.top.resizable(False, False)
        set_app_icon(self.top)
        self.top.grab_set()
        self.result = False
        
        self.top.update_idletasks()
        x = (self.top.winfo_screenwidth() // 2) - (380 // 2)
        y = (self.top.winfo_screenheight() // 2) - (150 // 2)
        self.top.geometry(f'+{x}+{y}')
        
        tk.Label(self.top, text="Вы уверены, что хотите выйти из программы?", 
                 bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 11)).pack(pady=(30, 20))
                 
        btn_frame = ttk.Frame(self.top, style='TFrame')
        btn_frame.pack(fill=tk.X, padx=40)
        btn_frame.columnconfigure(0, weight=1, uniform="btn")
        btn_frame.columnconfigure(1, weight=1, uniform="btn")
        
        ttk.Button(btn_frame, text="Да", style='Action.TButton', command=self.yes).grid(row=0, column=0, padx=(0, 10), sticky="ew", ipady=2)
        ttk.Button(btn_frame, text="Нет", style='Action.TButton', command=self.no).grid(row=0, column=1, padx=(10, 0), sticky="ew", ipady=2)
        
        self.top.protocol("WM_DELETE_WINDOW", self.no)
        
    def yes(self):
        self.result = True
        self.top.destroy()
        
    def no(self):
        self.result = False
        self.top.destroy()


class EnergyApp(ElectricityPageMixin, WaterPageMixin, GasPageMixin):
    def __init__(self, root, db_path='Energy.db'):
        self.root = root
        self.db_path = db_path
        self.root.title(f"Ежемесячные отчёты (v{VERSION})")

        self.root.withdraw()
        set_app_icon(self.root)

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Устанавливаем минимальный размер окна, чтобы кнопки и заголовок не наезжали
        self.root.minsize(1024, 600)

        if self.screen_width < 1024:
            window_width = self.screen_width - 20
            window_height = self.screen_height - 40
            self.root.geometry(f"{window_width}x{window_height}+10+10")
        else:
            try:
                self.root.state('zoomed')
            except Exception:
                self.root.attributes('-fullscreen', True)

        self.root.configure(bg='#2b2b2b')
        self.root.deiconify()

        setup_style(self.screen_width)
        init_db(self.db_path)
        self.icons = load_icons(self.screen_width)

        self.main_container = ttk.Frame(self.root, style='TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 1. Навигация (вверху)
        self.create_navigation()

        # 2. Статус-бар (внизу экрана)
        self.create_status_bar()

        # 3. Контейнер для страниц (посередине)
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

    def create_navigation(self):
        nav_frame = ttk.Frame(self.main_container, style='TFrame')
        nav_frame.pack(fill=tk.X, padx=3, pady=(15, 5))

        # --- 1. СНАЧАЛА ПАКУЕМ КНОПКИ СПРАВА ---
        # Это зарезервирует их ширину, и заголовок не сможет их сдвинуть
        btn_frame = ttk.Frame(nav_frame, style='TFrame')
        btn_frame.pack(side=tk.RIGHT, padx=(10, 20), pady=5)

        buttons = [
            ('Электроэнергия', 'electricity', 'energy'),
            ('Вода', 'water', 'water'),
            ('Газ', 'gas', 'gas'),
            ('Настройки', None, 'settings'),
            ('О программе', None, 'about')
        ]
        
        self.nav_buttons = {}
        for text, page, icon_key in buttons:
            if page:
                btn = ttk.Button(btn_frame, text=f" {text}", style='Nav.TButton', 
                                 command=lambda p=page: self.show_page(p))
                if self.icons.get(icon_key):
                    btn.config(image=self.icons[icon_key], compound=tk.LEFT)
                self.nav_buttons[page] = btn
            else:
                cmd = self.open_settings if text == "Настройки" else self.open_about
                btn = ttk.Button(btn_frame, text=f" {text}", style='Nav.TButton', command=cmd)
                if self.icons.get(icon_key):
                    btn.config(image=self.icons[icon_key], compound=tk.LEFT)
            
            # Упаковываем кнопки слева внутри правого фрейма
            btn.pack(side=tk.LEFT, padx=3, ipady=2)
            
        self.set_active_button('electricity')

        # --- 2. ТЕПЕРЬ ПАКУЕМ ЗАГОЛОВОК СЛЕВА ---
        # Он займет всё оставшееся пространство
        title_font_size = 14 if self.screen_width < 1024 else 16
        flash_icon = self.icons.get('flash')
        
        if flash_icon:
            title = ttk.Label(nav_frame, text=" ЭНЕРГОСЛУЖБА", image=flash_icon, compound=tk.LEFT, font=('Segoe UI', title_font_size, 'bold'))
        else:
            title = ttk.Label(nav_frame, text="⚡ ЭНЕРГОСЛУЖБА", font=('Segoe UI', title_font_size, 'bold'))

        title.pack(side=tk.LEFT, padx=(20, 10), pady=5, fill=tk.X, expand=True)

    def create_status_bar(self):
        self.status_bar = ttk.Frame(self.main_container, style='TFrame')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=5)
        
        self.db_canvas = tk.Canvas(self.status_bar, width=14, height=14, bg='#2b2b2b', highlightthickness=0)
        self.db_canvas.pack(side=tk.LEFT, padx=(0, 5), pady=2)
        self.db_circle = self.db_canvas.create_oval(2, 2, 12, 12, fill="#00ff88", outline="#ffffff", width=1)
        
        self.db_lbl1 = tk.Label(self.status_bar, text="База: ", fg="#ffffff", bg='#2b2b2b', font=('Segoe UI', 9))
        self.db_lbl1.pack(side=tk.LEFT)
        
        self.db_lbl2 = tk.Label(self.status_bar, text="", bg='#2b2b2b', font=('Segoe UI', 9, 'bold'))
        self.db_lbl2.pack(side=tk.LEFT)
        
        self.update_db_status()

    def update_db_status(self):
        is_local = self.db_path == 'Energy.db' or \
                   os.path.dirname(os.path.abspath(self.db_path)) == os.path.dirname(os.path.abspath(__file__))
        
        if is_local:
            self.db_canvas.itemconfig(self.db_circle, fill="#00ff88")
            self.db_lbl2.config(text="Локальная", fg="#00ff88")
        else:
            self.db_canvas.itemconfig(self.db_circle, fill="#ff4444")
            self.db_lbl2.config(text="Сетевая", fg="#ff4444")

    def open_settings(self):
        def on_save(new_path):
            if new_path != self.db_path:
                self.db_path = new_path
                cfg = load_config()
                cfg['db_path'] = new_path
                save_config(cfg)
                
                init_db(self.db_path)
                self.update_db_status()
                
                for name, page in self.pages.items():
                    if page.winfo_ismapped():
                        self.load_page_data(name)
                        break
                        
        SettingsWindow(self.root, self.db_path, on_save)

    def open_about(self):
        AboutWindow(self.root)

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
        except Exception:
            return date_str

    def on_enter_pressed(self, event):
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

    def bind_treeview_clicks(self, tree):
        tree.bind('<Button-1>', self.on_tree_left_click, add='+')
        tree.bind('<Button-3>', self.on_tree_right_click, add='+')

    def on_tree_left_click(self, event):
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region in ("nothing", "heading", "separator"):
            tree.selection_remove(tree.selection())

    def on_tree_right_click(self, event):
        event.widget.selection_remove(event.widget.selection())

    def auto_update(self):
        while self.running:
            time.sleep(2)
            if not self.running:
                break
            for page_name in ['electricity', 'water', 'gas']:
                try:
                    if self.has_data_changed(page_name):
                        self.root.after(0, lambda p=page_name: self.load_page_data(p))
                except Exception:
                    pass

    def on_closing(self):
        dialog = ExitDialog(self.root)
        self.root.wait_window(dialog.top)
        if dialog.result:
            self.running = False
            self.root.destroy()