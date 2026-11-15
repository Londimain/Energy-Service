import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from custom_calendar import CustomCalendar


class GasPageMixin:
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
        self.bind_treeview_clicks(self.gas_tree)

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

        diff_frame = tk.LabelFrame(bottom_frame, text=" Расчет расхода ",
                                   bg='#2b2b2b', fg='#ffffff', font=('Segoe UI', 9, 'bold'),
                                   bd=1, relief=tk.GROOVE)
        diff_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        diff_container = tk.Frame(diff_frame, bg='#2b2b2b')
        diff_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.gas_calc_mode = tk.StringVar(value="prev")
        calc_frame = tk.Frame(diff_container, bg='#2b2b2b')
        calc_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Radiobutton(calc_frame, text="С начала месяца", variable=self.gas_calc_mode, value="month",
                       bg='#2b2b2b', fg='#ffffff', selectcolor='#2b2b2b', activebackground='#2b2b2b', activeforeground='#ffffff',
                       font=('Segoe UI', 9), command=self.refresh_gas_diff).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(calc_frame, text="С предыдущей записью", variable=self.gas_calc_mode, value="prev",
                       bg='#2b2b2b', fg='#ffffff', selectcolor='#2b2b2b', activebackground='#2b2b2b', activeforeground='#ffffff',
                       font=('Segoe UI', 9), command=self.refresh_gas_diff).pack(side=tk.LEFT)

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

    def refresh_gas_diff(self):
        if hasattr(self, 'gas_selected_date') and self.gas_selected_date:
            selected = self.gas_tree.selection()
            if selected:
                item = selected[0]
                values = self.gas_tree.item(item, 'values')
                self.show_gas_diff(self.gas_selected_date, values)

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
                        self.show_gas_diff(current_date, values)
                        try:
                            dt = datetime.strptime(current_date, '%d.%m.%Y')
                            self.gas_month_cal.set_date(dt)
                        except Exception:
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

    def show_gas_diff(self, date_display, values):
        self.gas_diff_hint.pack_forget()
        self.gas_diff_content.pack(fill=tk.BOTH, expand=True)

        try:
            dt = datetime.strptime(date_display, '%d.%m.%Y')
            self.gas_month_cal.set_date(dt)
            date_str = dt.strftime('%Y-%m-%d')
        except Exception:
            date_str = ''

        try:
            cur = float(values[1]) if values[1] != "—" else 0
        except Exception:
            cur = 0

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if self.gas_calc_mode.get() == "prev":
            c.execute("SELECT reading FROM gas WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
            prev = c.fetchone()
        else:
            year_month = date_str[:7]
            c.execute("SELECT reading FROM gas WHERE date >= ? AND date < ? ORDER BY date ASC LIMIT 1", (year_month + '-01', date_str))
            prev = c.fetchone()
            
        conn.close()

        if prev:
            diff = cur - prev[0]
        else:
            diff = 0

        self.gas_diff_value.config(text=f"{self.format_number(diff)} м³")

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

        self.show_gas_diff(date_display, values)

        if self.gas_editing:
            self.gas_reading_entry.delete(0, tk.END)
            if values[1] != "—":
                self.gas_reading_entry.insert(0, values[1])
            try:
                dt = datetime.strptime(date_display, '%d.%m.%Y')
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
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

        tut = (reading * 1.15) / 1000 if reading is not None else None
        gkal = (tut / coefficient) if tut is not None else None

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

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
        except Exception:
            date_str = ''

        self.gas_reading_entry.delete(0, tk.END)
        if values[1] != "—":
            self.gas_reading_entry.insert(0, values[1])

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
            except Exception:
                return
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM gas WHERE date = ?", (date_str,))
            conn.commit()
            conn.close()
            self.load_gas_data()
            messagebox.showinfo("Успех", "Запись удалена.")