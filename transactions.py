import os
import json
from datetime import datetime
from storage import load_data, save_data
from utils import farsi

TRANSACTIONS_FILE = "data/transactions.json"
INCOME_CATEGORIES = ["حقوق", "یارانه", "فروش", "سایر"]
EXPENSE_CATEGORIES = ["خوراک", "اجاره", "حمل و نقل", "تفریح", "سایر"]

def add_transaction(username, transaction_type):
    type_mapping = {"درآمد": "income", "مخارج": "expense", "income": "income", "expense": "expense"}
    normalized_type = type_mapping.get(transaction_type)

    if not normalized_type:
        print(farsi("خطا: نوع تراکنش باید 'درآمد' یا 'مخارج' باشد."))
        return

    transactions = load_data(TRANSACTIONS_FILE)

    # دریافت مبلغ
    amount_input = input(farsi(f" : مبلغ را برای {transaction_type} وارد کنید ")).strip()
    try:
        amount = float(amount_input)
        if amount <= 0:
            print(farsi(" !!!  مبلغ بايد بزرگتر از صفر باشد  "))
            return 
    except ValueError: return print(farsi("خطا: لطفاً فقط عدد وارد کنید."))

    # نمایش دسته‌بندی‌ها
    categories = INCOME_CATEGORIES if normalized_type == "income" else EXPENSE_CATEGORIES
    for index, cat in enumerate(categories, 1):
        print(farsi(f"{index}. {cat}")) # اصلاح: ارسال کل خط به farsi

    choice = input(farsi("یک گزینه انتخاب کنید: "))
    
    selected_category = ""
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(categories):
            selected_category = categories[idx]
            if selected_category == "سایر":
                selected_category = input(farsi("نام دسته‌بندی جدید را وارد کنید: ")).strip()
        else:
            print(farsi("خطا: گزینه خارج از محدوده است."))
            return
    else:
        print(farsi("خطا: ورودی معتبر نیست."))
        return

    # دریافت توضیحات
    note = input(farsi("توضیحات (اختیاری): ")).strip()
    if not note: note = "بدون توضیح"

    # ثبت نهایی
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_transaction = {
        "username": username,
        "type": normalized_type,
        "amount": amount,
        "category": selected_category, # استفاده از متغیر نهایی
        "note": note,
        "date": current_date
    }

    transactions.append(new_transaction)
    save_data(TRANSACTIONS_FILE, transactions)
    print(farsi(f"تراکنش با موفقیت ثبت شد!"))


def show_user_transactions(username):
    transactions = load_data(TRANSACTIONS_FILE)

    print(farsi("\n--- تراکنش‌های شما ---"))

    user_transactions = []

    for transaction in transactions:
        if transaction.get("username") == username:
            user_transactions.append(transaction)

    if not user_transactions:
        print(farsi("هنوز هیچ تراکنشی ثبت نکرده‌اید."))
        return

    type_mapping = {
        "income": "درآمد",
        "expense": "مخارج"
    }

    for index, transaction in enumerate(user_transactions, 1):
        transaction_type = type_mapping.get(
            transaction.get("type"),
            transaction.get("type")
        )

        print(farsi(f"""
تراکنش شماره {index}
نوع: {transaction_type}
مبلغ: {transaction.get("amount"):,.0f} تومان
دسته‌بندی: {transaction.get("category")}
توضیحات: {transaction.get("note")}
تاریخ: {transaction.get("date")}
------------------------------
"""))
def show_all_transactions():
    transactions = load_data(TRANSACTIONS_FILE)

    print(farsi("\n--- همه تراکنش‌ها ---"))

    if not transactions:
        print(farsi("هیچ تراکنشی ثبت نشده است."))
        return

    type_mapping = {
        "income": "درآمد",
        "expense": "مخارج"
    }

    for index, transaction in enumerate(transactions, 1):
        transaction_type = type_mapping.get(
            transaction.get("type"),
            transaction.get("type", "نامشخص")
        )

        print(
            farsi(
                f"\nتراکنش شماره {index}\n"
                f"نام کاربری: {transaction.get('username', 'نامشخص')}\n"
                f"نوع: {transaction_type}\n"
                f"مبلغ: {transaction.get('amount', 0):,.0f} تومان\n"
                f"دسته‌بندی: {transaction.get('category', 'نامشخص')}\n"
                f"توضیحات: {transaction.get('note', 'بدون توضیح')}\n"
                f"تاریخ: {transaction.get('date', 'نامشخص')}\n"
                f"------------------------------"
            )
        )