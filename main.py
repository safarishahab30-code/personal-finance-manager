import os
from auth import login, register, load_users
from auth import change_password , change_username 
from utils import farsi
import secrets
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
from transactions import add_transaction, show_user_transactions, show_all_transactions
def normalize_choice(s):
    return s.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).strip()
print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir())

def admin_settings(current_user):
    while True:
        print(farsi("\n--- تنظیمات ---"))
        print(farsi("1. تغییر نام کاربری"))
        print(farsi("2. تغییر رمز عبور"))
        print(farsi("3. اطلاعات حساب"))
        print(farsi("4. بازگشت"))

        choice = normalize_choice(input(farsi("انتخاب: ")))

        if choice == "1":
            change_username(current_user)
        elif choice == "2":
            change_password(current_user)
        elif choice == "3":
            print(farsi(f"نام کاربری: {current_user['username']} | نقش: {current_user['role']}"))
        elif choice == "4":
            break
        else:
            print(farsi("گزینه نامعتبر است."))

def admin_menu(current_user):
    print("ADMIN MENU STARTED")

    while True:
        print(farsi("\n--- پنل ادمین ---"))
        print(farsi("1. مشاهده کاربران"))
        print(farsi("2. مشاهده تراکنش‌ها"))
        print(farsi("3. تنظیمات"))
        print(farsi("4. خروج"))

        choice = input(farsi("انتخاب: ")).strip()

        if choice == "1":
            users = load_users()

            if not users:
                print(farsi("هیچ کاربری ثبت نشده است."))
            else:
                print(farsi("\nفهرست کاربران:"))
                for user in users:
                    username = user.get("username", "بدون نام")
                    role = user.get("role", "نامشخص")
                    print(farsi(f"نام کاربری: {username} | نقش: {role}"))

        elif choice == "2":
            show_all_transactions()

        elif choice == "3":
            admin_settings(current_user)

        elif choice == "4":
            print(farsi("خروج از پنل ادمین"))
            break

        else:
            print(farsi("گزینه نامعتبر است."))


def user_menu(current_user):
    print("USER MENU STARTED")

    while True:
        print(farsi("\n--- داشبورد کاربر ---"))
        print(farsi("1. افزودن درآمد"))
        print(farsi("2. افزودن مخارج"))
        print(farsi("3. مشاهده تراکنش‌ها"))
        print(farsi("4. خروج"))

        choice = input(farsi("انتخاب: ")).strip()

        if choice == "1":
            add_transaction(current_user["username"], "income")

        elif choice == "2":
            add_transaction(current_user["username"], "expense")

        elif choice == "3":
            show_user_transactions(current_user["username"])

        elif choice == "4":
            print(farsi("از حساب کاربری خارج شدید."))
            break

        else:
            print(farsi("گزینه نامعتبر است."))


def main():
    while True:
        print("\n--- Personal Finance Manager ---")
        print(farsi("1. ثبت نام"))
        print(farsi("     2. ورود"))
        print(farsi("       3. خروج"))

        choice = input(farsi(" : انتخاب")).strip()

        if choice == "1":
            register()

        elif choice == "2":
            current_user = login()

            if current_user is None:
                print(farsi("ورود ناموفق بود. نام کاربری یا رمز عبور اشتباه است."))

            elif current_user.get("role") == "admin":
                admin_menu(current_user)

            else:
                user_menu(current_user)

        elif choice == "3":
            print(farsi("خداحافظ!"))
            break

        else:
            print(farsi("گزینه نامعتبر است."))
            # اگر خواستی همین‌جا هم می‌توانیم انگلیسی را کامل فارسی کنیم


if __name__ == "__main__":
    main()
