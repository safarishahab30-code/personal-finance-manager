import json
import os

def load_data(file_path):
    if not os.path.exists(file_path): return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# مسیر فایل‌ها در پوشه data
USERS_FILE = 'data/users.json'
TRANSACTIONS_FILE = 'data/transactions.json'

def ensure_data_dir():
    """مطمئن می‌شود که پوشه data وجود دارد"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # ایجاد فایل‌های خالی در صورت عدم وجود برای جلوگیری از خطا
    for file_path in [USERS_FILE, TRANSACTIONS_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

def load_json(file_path):
    """خواندن داده‌ها از فایل JSON"""
    ensure_data_dir()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(file_path, data):
    """ذخیره داده‌ها در فایل JSON"""
    ensure_data_dir()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# اجرای اولیه برای اطمینان از وجود پوشه‌ها و فایل‌ها
ensure_data_dir()