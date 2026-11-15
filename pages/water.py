import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from custom_calendar import CustomCalendar


class WaterPageMixin:
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
        self.bind_treeview_clicks(self.water_tree)

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

        diff_frame = tk.LabelFrame(bottom_frame, text=" Расчет расхода ",
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.water_calc_mode = tk.StringVar(value="prev")
        calc_frame = tk.Frame(diff_container, bg='#2b2b2b')
        calc_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Radiobutton(calc_frame, text="С начала месяца", variable=self.water_calc_mode, value="month",
                       bg='#2b2b2b', fg='#ffffff', selectcolor='#2b2b2b', activebackground='#2b2b2b', activeforeground='#ffffff',
                       font=('Segoe UI', 9), command=self.refresh_water_diff).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(calc_frame, text="С предыдущей записью", variable=self.water_calc_mode, value="prev",
                       bg='#2b2b2b', fg='#ffffff', selectcolor='#2b2b2b', activebackground='#2b2b2b', activeforeground='#ffffff',
                       font=('Segoe UI', 9), command=self.refresh_water_diff).pack(side=tk.LEFT)

        self.water_diff_hint = tk.Label(diff_container,
                                        text="Укажите нужную дату в таблице для получения разницы",
                                        bg='#2b2b2b', fg='#888888',
                                        font=('Segoe UI', 13),
                                        anchor=tk.CENTER)
        self.water_diff_hint.pack(expand=True, fill=tk.BOTH)

        self.water_diff_content = tk.Frame(diff_container, bg='#2b2b2b')
        font_diff = 10 if self.screen_width < 1024 else 12

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

    def refresh_water_diff(self):
        if hasattr(self, 'water_selected_date') and self.water_selected_date:
            selected = self.water_tree.selection()
            if selected:
                item = selected[0]
                values = self.water_tree.item(item, 'values')
                self.show_water_diff(self.water_selected_date, values)

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
                        except Exception:
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
        except Exception:
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
        except Exception:
            cur_glavny = 0
            cur_kan_v = 0

        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            date_str = dt.strftime('%Y-%m-%d')
        except Exception:
            date_str = ''

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if self.water_calc_mode.get() == "prev":
            c.execute("SELECT glavny, kan_v FROM water WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
            prev = c.fetchone()
        else:
            year_month = date_str[:7]
            c.execute("SELECT glavny, kan_v FROM water WHERE date >= ? AND date < ? ORDER BY date ASC LIMIT 1", (year_month + '-01', date_str))
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
        except Exception:
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
            except Exception:
                return
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM water WHERE date = ?", (date_str,))
            conn.commit()
            conn.close()
            self.load_water_data()
            messagebox.showinfo("Успех", "Запись удалена.")