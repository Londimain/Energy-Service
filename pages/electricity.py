import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from custom_calendar import CustomCalendar


class ElectricityPageMixin:
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
        self.bind_treeview_clicks(self.electricity_tree)

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

        diff_frame = tk.LabelFrame(bottom_frame, text=" Расчет расхода ",
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Возвращенные радиокнопки ---
        self.elec_calc_mode = tk.StringVar(value="prev")
        calc_frame = tk.Frame(diff_container, bg='#2b2b2b')
        calc_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Radiobutton(calc_frame, text="С начала месяца", variable=self.elec_calc_mode, value="month",
                       bg='#2b2b2b', fg='#ffffff', selectcolor='#2b2b2b', activebackground='#2b2b2b', activeforeground='#ffffff',
                       font=('Segoe UI', 9), command=self.refresh_electricity_diff).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(calc_frame, text="С предыдущей записью", variable=self.elec_calc_mode, value="prev",
                       bg='#2b2b2b', fg='#ffffff', selectcolor='#2b2b2b', activebackground='#2b2b2b', activeforeground='#ffffff',
                       font=('Segoe UI', 9), command=self.refresh_electricity_diff).pack(side=tk.LEFT)
        # -------------------------------

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

    def refresh_electricity_diff(self):
        if hasattr(self, 'elec_selected_date') and self.elec_selected_date:
            selected = self.electricity_tree.selection()
            if selected:
                item = selected[0]
                values = self.electricity_tree.item(item, 'values')
                self.show_electricity_diff(self.elec_selected_date, values)

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
                        except Exception:
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
        except Exception:
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
        except Exception:
            cur_m1 = cur_m2 = cur_m3 = 0

        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            date_str = dt.strftime('%Y-%m-%d')
        except Exception:
            date_str = ''

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if self.elec_calc_mode.get() == "prev":
            c.execute("SELECT meter1_reading, meter2_reading, meter3_reading FROM electricity WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
            prev = c.fetchone()
        else:
            year_month = date_str[:7]
            c.execute("SELECT meter1_reading, meter2_reading, meter3_reading FROM electricity WHERE date >= ? AND date < ? ORDER BY date ASC LIMIT 1", (year_month + '-01', date_str))
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
        except Exception:
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
            except Exception:
                return
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM electricity WHERE date = ?", (date_str,))
            conn.commit()
            conn.close()
            self.load_electricity_data()
            messagebox.showinfo("Успех", "Запись удалена.")