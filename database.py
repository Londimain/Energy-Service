import sqlite3


def init_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 1. СНАЧАЛА СОЗДАЕМ ТАБЛИЦЫ, ЕСЛИ ИХ НЕТ
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

        # 2. ТЕПЕРЬ ПРОВЕРЯЕМ И ДОБАВЛЯЕМ НОВЫЕ КОЛОНКИ (миграции)
        c.execute("PRAGMA table_info(gas)")
        gas_cols = [col[1] for col in c.fetchall()]
        if 'coefficient' not in gas_cols:
            c.execute("ALTER TABLE gas ADD COLUMN coefficient REAL DEFAULT 0.185")
        if 'tut' not in gas_cols:
            c.execute("ALTER TABLE gas ADD COLUMN tut REAL")
        if 'gkal' not in gas_cols:
            c.execute("ALTER TABLE gas ADD COLUMN gkal REAL")

        # 3. МИГРАЦИЯ СТАРОГО ФОРМАТА (month -> date)
        tables = ['electricity', 'water', 'gas']
        for table in tables:
            c.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in c.fetchall()]
            if 'month' in columns:
                print(f"Миграция таблицы {table}: month -> date")
                c.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
                
                # Пересоздаем таблицу
                if table == 'electricity':
                    c.execute('''CREATE TABLE electricity (
                                    date TEXT PRIMARY KEY,
                                    meter1_reading REAL,
                                    meter2_reading REAL,
                                    meter3_reading REAL
                                 )''')
                    c.execute('''INSERT INTO electricity (date, meter1_reading, meter2_reading, meter3_reading)
                                 SELECT month || '-01', meter1_reading, meter2_reading, meter3_reading
                                 FROM electricity_old''')
                elif table == 'water':
                    c.execute('''CREATE TABLE water (
                                    date TEXT PRIMARY KEY,
                                    glavny REAL,
                                    kan_v REAL
                                 )''')
                    c.execute('''INSERT INTO water (date, glavny, kan_v)
                                 SELECT month || '-01', glavny, kan_v FROM water_old''')
                elif table == 'gas':
                    c.execute('''CREATE TABLE gas (
                                    date TEXT PRIMARY KEY,
                                    reading REAL,
                                    coefficient REAL DEFAULT 0.185,
                                    tut REAL,
                                    gkal REAL
                                 )''')
                    c.execute('''INSERT INTO gas (date, reading, coefficient)
                                 SELECT month || '-01', reading, 0.185 FROM gas_old''')
                
                c.execute(f"DROP TABLE {table}_old")
                conn.commit()
                print(f"Миграция {table} завершена.")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")