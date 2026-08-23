import json
import os

from auth import login, register, load_users
from utils import farsi
from transactions import add_transaction,show_user_transactions,show_all_transactions

print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir())


def admin_menu():
    print("ADMIN MENU STARTED")

    while True:
        print("\n--- Admin Panel ---")
        print(farsi("1. مشاهده کاربران"))
        print(farsi("2.مشاهده تراكنش ها "))
        print(farsi("3. تنظیمات"))
        print(farsi("4. خروج"))

        choice = input("Option: ").strip()

        if choice == "1":
            users = load_users()

            if not users:
                print(farsi("هیچ کاربری ثبت نشده است."))
            else:
                print(farsi("\nفهرست کاربران:"))

                for user in users:
                    username = user.get("username", "بدون نام")
                    role = user.get("role", "نامشخص")

                    print(
                        farsi(
                            f"نام کاربری: {username} | نقش: {role}"
                        )
                    )
        elif choice == "2":
            show_all_transactions()
        elif choice == "3":
            print(farsi("بخش تنظیمات هنوز پیاده‌سازی نشده است."))
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
        print(farsi("2. ورود"))
        print(farsi("3. خروج"))

        choice = input(farsi("انتخاب: ")).strip()

        if choice == "1":
            register()

        elif choice == "2":
            user = login()

            if user is None:
                print(
                    farsi(
                        "ورود ناموفق بود. نام کاربری یا رمز عبور اشتباه است."
                    )
                )

            elif user["role"] == "admin":
                admin_menu()

            else:
                user_menu(user)

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()

