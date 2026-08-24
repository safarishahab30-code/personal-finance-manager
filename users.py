from utils import farsi
from storage import load_data, save_data

USERS_FILE = "data/users.json"


def get_all_users():
    """دریافت تمام کاربران از دیتابیس فایل"""
    return load_data(USERS_FILE)


def save_all_users(users):
    """ذخیره تمام کاربران در دیتابیس فایل"""
    save_data(USERS_FILE, users)


def find_user_by_username(username):
    """یافتن کاربر بر اساس نام کاربری"""
    users = get_all_users()
    for user in users:
        if user.get("username") == username:
            return user
    return None