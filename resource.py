import os
import sys


def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу (работает и в PyInstaller)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)