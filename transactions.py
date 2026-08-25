import os
import json
from datetime import datetime
from storage import load_data, save_data
from utils import farsi

TRANSACTIONS_FILE = "data/transactions.json"
INCOME_CATEGORIES = ["حقوق", "یارانه", "فروش", "سایر"]
EXPENSE_CATEGORIES = ["خوراک", "اجاره", "حمل و نقل", "تفریح", "سایر"]
def generate_transaction_id(transactions):
    if not transactions:
        return 1
    # پیدا کردن بزرگ‌ترین id موجود و یکی افزودن به آن
    return max(t.get("id", 0) for t in transactions) + 1
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
        "id": generate_transaction_id(transactions),
        "username": username,
        "type": normalized_type,
        "amount": amount,
        "category": selected_category,
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
def delete_transaction(username):
    transactions = load_data(TRANSACTIONS_FILE)
    
    # فیلتر تراکنش‌های کاربر جاری
    user_txs = [t for t in transactions if t.get("username") == username]
    
    if not user_txs:
        print(farsi("شما هیچ تراکنشی برای حذف ندارید."))
        return

    # نمایش لیست با شناسه
    print(farsi("\n--- لیست تراکنش‌های شما جهت حذف ---"))
    for t in user_txs:
        t_type = "درآمد" if t.get("type") == "income" else "مخارج"
        print(farsi(f"شناسه: {t.get('id')} | نوع: {t_type} | مبلغ: {t.get('amount', 0):,.0f} | دسته: {t.get('category')} | تاریخ: {t.get('date')}"))
    print(farsi("----------------------------------"))

    target_id_input = input(farsi("شناسه (ID) تراکنش مورد نظر برای حذف را وارد کنید (یا 0 برای انصراف): ")).strip()
    
    if target_id_input == "0" or not target_id_input.isdigit():
        print(farsi("عملیات حذف لغو شد."))
        return

    target_id = int(target_id_input)

    # بررسی مالکیت تراکنش
    tx_to_delete = next((t for t in user_txs if t.get("id") == target_id), None)
    
    if not tx_to_delete:
        print(farsi("خطا: تراکنشی با این شناسه متعلق به شما یافت نشد."))
        return

    # تأیید نهایی
    confirm = input(farsi(f"آیا از حذف تراکنش شناسه {target_id} مطمئن هستید؟ (y/n): ")).strip().lower()
    if confirm == 'y':
        updated_transactions = [t for t in transactions if t.get("id") != target_id]
        save_data(TRANSACTIONS_FILE, updated_transactions)
        print(farsi("تراکنش با موفقیت حذف شد."))
    else:
        print(farsi("حذف تراکنش لغو شد."))
def edit_transaction(username):
    transactions = load_data(TRANSACTIONS_FILE)
    user_txs = [t for t in transactions if t.get("username") == username]

    if not user_txs:
        print(farsi("شما هیچ تراکنشی برای ویرایش ندارید."))
        return

    print(farsi("\n--- لیست تراکنش‌های شما جهت ویرایش ---"))
    for t in user_txs:
        t_type = "درآمد" if t.get("type") == "income" else "مخارج"
        print(farsi(f"شناسه: {t.get('id')} | نوع: {t_type} | مبلغ: {t.get('amount', 0):,.0f} | دسته: {t.get('category')} | تاریخ: {t.get('date')}"))
    print(farsi("-----------------------------------"))

    target_id_input = input(farsi("شناسه (ID) تراکنش را وارد کنید (یا 0 برای انصراف): ")).strip()
    if target_id_input == "0" or not target_id_input.isdigit():
        print(farsi("عملیات ویرایش لغو شد."))
        return

    target_id = int(target_id_input)
    tx = next((t for t in user_txs if t.get("id") == target_id), None)

    if not tx:
        print(farsi("خطا: تراکنشی با این شناسه متعلق به شما یافت نشد."))
        return

    print(farsi("\n(در صورت عدم تمایل به تغییر هر بخش، Enter بزنید)"))

    # ۱. ویرایش مبلغ
    new_amount_input = input(farsi(f"مبلغ جدید (فعلی: {tx.get('amount'):,.0f}): ")).strip()
    if new_amount_input:
        try:
            val = float(new_amount_input)
            if val > 0:
                tx["amount"] = val
            else:
                print(farsi("مبلغ نامعتبر بود؛ مقدار قبلی حفظ شد."))
        except ValueError:
            print(farsi("ورودی عدد نبود؛ مقدار قبلی حفظ شد."))

    # ۲. ویرایش دسته‌بندی
    t_type = tx.get("type")
    categories = INCOME_CATEGORIES if t_type == "income" else EXPENSE_CATEGORIES
    print(farsi(f"\nدسته‌بندی‌های موجود برای {('درآمد' if t_type == 'income' else 'مخارج')}:"))
    for idx, cat in enumerate(categories, 1):
        print(farsi(f"{idx}. {cat}"))

    cat_choice = input(farsi(f"انتخاب دسته‌بندی جدید (فعلی: {tx.get('category')}): ")).strip()
    if cat_choice.isdigit():
        idx = int(cat_choice) - 1
        if 0 <= idx < len(categories):
            selected = categories[idx]
            if selected == "سایر":
                custom = input(farsi("نام دسته‌بندی دلخواه: ")).strip()
                if custom:
                    tx["category"] = custom
            else:
                tx["category"] = selected

    # ۳. ویرایش توضیحات
    new_note = input(farsi(f"توضیحات جدید (فعلی: {tx.get('note')}): ")).strip()
    if new_note:
        tx["note"] = new_note

    save_data(TRANSACTIONS_FILE, transactions)
    print(farsi("تراکنش با موفقیت ویرایش شد."))
def validate_amount(val):
    try:
        amount = int(val)
        return amount if amount > 0 else None
    except (ValueError, TypeError):
        return None
