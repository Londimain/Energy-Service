import json
import os


def get_config_path():
    # Получаем путь к папке AppData/Roaming текущего пользователя
    appdata = os.getenv('APPDATA')
    if not appdata:
        appdata = os.path.expanduser('~')
    
    # Создаем папку EnergyReport в AppData, если её еще нет
    config_dir = os.path.join(appdata, 'EnergyReport')
    os.makedirs(config_dir, exist_ok=True)
    
    return os.path.join(config_dir, 'config.json')


CONFIG_FILE = get_config_path()


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка чтения конфигурации: {e}")
    return {}


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения конфигурации: {e}")