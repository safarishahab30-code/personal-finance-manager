import os
import sys
import io
import secrets
from storage import load_data, save_data
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
from auth import login, register, load_users, change_password, change_username
from utils import farsi
from reports import (
    admin_report_summary,
    show_expense_chart,
    export_transactions_csv,
    export_transactions_excel
)
from transactions import (
    add_transaction,
    show_user_transactions,
    edit_transaction,
    delete_transaction,
    show_all_transactions
)


def normalize_choice(s):
    return s.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).strip()


def admin_settings(current_user):
    while True:
        print(farsi("=== تنظیمات حساب ==="))
        print(farsi("1) مشاهده اطلاعات حساب"))
        print(farsi("2) تغییر نام کاربری"))
        print(farsi("3) تغییر رمز عبور"))
        print(farsi("0) بازگشت"))
        choice = normalize_choice(input(farsi("انتخاب: ")))

        if choice == "1":
            print(farsi(f"نام کاربری: {current_user.get('username')} | نقش: {current_user.get('role')}"))
        elif choice == "2":
            change_username(current_user)
        elif choice == "3":
            change_password(current_user)
        elif choice == "0":
            break
        else:
            print(farsi("گزینه نامعتبر است."))


def admin_menu(current_user):
    while True:
        print(farsi("\n--- پنل ادمین ---"))
        print(farsi("1. مشاهده کاربران"))
        print(farsi("2. مشاهده تراکنش‌ها"))
        print(farsi("3. گزارش کلی سیستم"))
        print(farsi("4. خروجی کل تراکنش‌ها (CSV)"))
        print(farsi("5. خروجی کل تراکنش‌ها (Excel)"))
        print(farsi("6. تنظیمات"))
        print(farsi("7. خروج"))

        choice = normalize_choice(input(farsi("انتخاب: ")))

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
            admin_report_summary()
        elif choice == "4":
            export_transactions_csv()
        elif choice == "5":
            export_transactions_excel()
        elif choice == "6":
            admin_settings(current_user)
        elif choice == "7":
            print(farsi("خروج از پنل ادمین"))
            break
        else:
            print(farsi("گزینه نامعتبر است."))

def user_settings(current_user):
    while True:
        print(farsi("\n=== تنظیمات حساب کاربری ==="))
        print(farsi("1) مشاهده اطلاعات حساب"))
        print(farsi("2) تغییر نام کاربری"))
        print(farsi("3) تغییر رمز عبور"))
        print(farsi("0) بازگشت"))
        choice = normalize_choice(input(farsi("انتخاب: ")))

        if choice == "1":
            print(farsi(f"نام کاربری: {current_user.get('username')} | تاریخ ایجاد: {current_user.get('created_at', 'نامشخص')}"))
        elif choice == "2":
            users = load_data("data/users.json")
            txs = load_data("data/transactions.json")
            # پیدا کردن آبجکت دقیق کاربر داخل لیست users
            user_in_db = next((u for u in users if u["username"] == current_user["username"]), current_user)
            if change_username(user_in_db, users, txs):
                current_user["username"] = user_in_db["username"]
                save_data("data/users.json", users)
                save_data("data/transactions.json", txs)
        elif choice == "3":
            users = load_data("data/users.json")
            user_in_db = next((u for u in users if u["username"] == current_user["username"]), current_user)
            if change_password(user_in_db):
                current_user["password"] = user_in_db["password"]
                save_data("data/users.json", users)
        elif choice == "0":
            break
        else:
            print(farsi("گزینه نامعتبر است."))
def user_menu(current_user):
    while True:
        print(farsi("\n--- داشبورد کاربر ---"))
        print(farsi("1. افزودن درآمد"))
        print(farsi("2. افزودن مخارج"))
        print(farsi("3. مشاهده تراکنش‌ها"))
        print(farsi("4. ویرایش تراکنش"))
        print(farsi("5. حذف تراکنش"))
        print(farsi("6. نمایش نمودار هزینه‌ها"))
        print(farsi("7. دریافت خروجی CSV"))
        print(farsi("8. دریافت خروجی Excel"))
        print(farsi("9. تنظیمات حساب"))
        print(farsi("10. خروج"))

        choice = normalize_choice(input(farsi("انتخاب: ")))

        if choice == "1":
            add_transaction(current_user["username"], "income")
        elif choice == "2":
            add_transaction(current_user["username"], "expense")
        elif choice == "3":
            show_user_transactions(current_user["username"])
            input(farsi("\nبرای بازگشت اینتر را بزنید..."))

        elif choice == "4":
            edit_transaction(current_user["username"])
        elif choice == "5":
            delete_transaction(current_user["username"])
        elif choice == "6":
            show_expense_chart(current_user["username"])
        elif choice == "7":
            export_transactions_csv(current_user["username"])
        elif choice == "8":
            export_transactions_excel(current_user["username"])
        elif choice == "9":
            user_settings(current_user)
        elif choice == "10":
            print(farsi("از حساب کاربری خارج شدید."))
            break
        else:
            print(farsi("گزینه نامعتبر است."))

def main():
    while True:
        print("\n--- Personal Finance Manager ---")
        print(farsi("1. ثبت نام"))
        print(farsi("2. ورود"))
        print(farsi("3. خروج"))

        choice = normalize_choice(input(farsi(": انتخاب")))

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


if __name__ == "__main__":
    main()
