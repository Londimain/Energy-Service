import tkinter as tk

from app import EnergyApp
from auth import AuthWindow
from icons import set_app_icon
from config import load_config


def main():
    # Читаем настройки перед запуском
    config = load_config()
    db_path = config.get('db_path', 'Energy.db')

    root = tk.Tk()
    set_app_icon(root)
    root.withdraw()

    login_win = tk.Toplevel(root)
    auth = AuthWindow(login_win)

    root.wait_window(login_win)

    if auth.authenticated:
        # Передаем путь к БД в приложение
        app = EnergyApp(root, db_path=db_path)
        root.deiconify()
        root.mainloop()
    else:
        root.destroy()


if __name__ == "__main__":
    main()