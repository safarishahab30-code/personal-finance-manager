import json
import os
from utils import farsi
USERS_FILE = "data/users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    os.makedirs("data", exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)

def register():
    users = load_users()
    username = input("Username: ").strip()
    password = input("Password: ")

    if not username or not password:
        print(farsi("نام کاربری و رمز عبور نمی‌تواند خالی باشد."))
        return

    for user in users:
        if user["username"] == username:
            print(farsi("این نام کاربری قبلاً ثبت شده است."))
            return

    # اولین نفر ادمین، بقیه کاربر عادی
    role = "admin" if len(users) == 0 else "user"
    
    new_user = {
        "username": username,
        "password": password,
        "role": role
    }
    
    users.append(new_user)
    save_users(users)
    print(farsi(f"ثبت‌نام با موفقیت انجام شد. نقش شما: {role}"))

def login():
    users = load_users()
    username = input("Username: ").strip()
    password = input("Password: ")

    for user in users:
        if user["username"] == username and user["password"] == password:
            return user

    print(farsi("نام کاربری یا رمز عبور اشتباه است."))
    return None
