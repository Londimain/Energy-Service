import os
from PIL import Image, ImageTk

from resource import resource_path


def set_app_icon(root):
    try:
        icon_path = resource_path('ico/appEnergy.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Не удалось установить иконку приложения: {e}")


def load_icons(screen_width):
    icons = {}
    icon_files = {
        'energy': 'ico/energy.png',
        'water': 'ico/water.png',
        'gas': 'ico/gaz.png',
        'flash': 'ico/flash.png',
        'settings': 'ico/settings.png', # <--- Добавьте файл
        'about': 'ico/about.png'        # <--- Добавьте файл
    }
    icon_size = 16 if screen_width < 1024 else 20

    for key, path in icon_files.items():
        try:
            full_path = resource_path(path)
            if os.path.exists(full_path):
                img = Image.open(full_path)
                img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                icons[key] = ImageTk.PhotoImage(img)
            else:
                icons[key] = None
        except Exception as e:
            print(f"Ошибка загрузки иконки {key}: {e}")
            icons[key] = None
    return icons