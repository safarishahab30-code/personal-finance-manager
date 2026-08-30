import os
from datetime import datetime
from storage import load_data, save_data
from utils import (
    DEFAULT_ACCOUNTS,
    farsi,
    format_money,
    parse_farsi_number,
)

TRANSACTIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "transactions.json")
INCOME_CATEGORIES = ["حقوق", "یارانه", "فروش", "سایر"]
EXPENSE_CATEGORIES = ["خوراک", "اجاره", "حمل و نقل", "تفریح", "سایر"]


def validate_amount(val):
    try:
        clean_val = parse_farsi_number(str(val)).replace(",", "")
        amount = int(clean_val)
        return amount if amount > 0 else None
    except (ValueError, TypeError):
        return None


def generate_transaction_id(transactions):
    if not transactions:
        return 1
    return max(t.get("id", 0) for t in transactions) + 1


def select_account():
    print(farsi("\n--- انتخاب حساب / کارت ---"))
    for idx, acc in enumerate(DEFAULT_ACCOUNTS, 1):
        print(farsi(f"{idx}. {acc}"))
    print(farsi("0. سایر / حساب جدید"))

    choice = parse_farsi_number(input(farsi("انتخاب حساب: ")))
    if choice.isdigit() and 1 <= int(choice) <= len(DEFAULT_ACCOUNTS):
        return DEFAULT_ACCOUNTS[int(choice) - 1]
    elif choice == "0":
        custom = input(farsi("نام حساب جدید: ")).strip()
        return custom if custom else "نامشخص"
    return "کارت اصلی"


def add_transaction(username, transaction_type):
    type_mapping = {
        "درآمد": "income",
        "مخارج": "expense",
        "income": "income",
        "expense": "expense",
    }
    normalized_type = type_mapping.get(transaction_type)

    if not normalized_type:
        print(farsi("خطا: نوع تراکنش باید 'درآمد' یا 'مخارج' باشد."))
        return

    transactions = load_data(TRANSACTIONS_FILE)

    # دریافت و اعتبارسنجی مبلغ
    amount_input = input(
        farsi(f"مبلغ را برای {transaction_type} وارد کنید: ")
    ).strip()
    amount = validate_amount(amount_input)
    if not amount:
        print(farsi("خطا: مبلغ باید عددی و بزرگ‌تر از صفر باشد."))
        return

    # انتخاب حساب
    account = select_account()

    # نمایش و انتخاب دسته‌بندی
    categories = (
        INCOME_CATEGORIES
        if normalized_type == "income"
        else EXPENSE_CATEGORIES
    )
    print(farsi(f"\nدسته‌بندی‌های {transaction_type}:"))
    for index, cat in enumerate(categories, 1):
        print(farsi(f"{index}. {cat}"))

    choice = parse_farsi_number(input(farsi("یک گزینه انتخاب کنید: ")))
    selected_category = ""
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(categories):
            selected_category = categories[idx]
            if selected_category == "سایر":
                selected_category = input(
                    farsi("نام دسته‌بندی جدید را وارد کنید: ")
                ).strip()
                if not selected_category:
                    selected_category = "سایر"
        else:
            print(farsi("خطا: گزینه خارج از محدوده است."))
            return
    else:
        print(farsi("خطا: ورودی معتبر نیست."))
        return

    # دریافت توضیحات
    note = input(farsi("توضیحات (اختیاری): ")).strip()
    if not note:
        note = "بدون توضیح"

    # استخراج نام کاربری دقیق
    clean_username = username.get("username") if isinstance(username, dict) else str(username)

    # ثبت تراکنش
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_transaction = {
        "id": generate_transaction_id(transactions),
        "username": clean_username.strip(),
        "type": normalized_type,
        "amount": amount,
        "category": selected_category,
        "account": account,
        "note": note,
        "date": current_date,
    }

    transactions.append(new_transaction)
    save_data(TRANSACTIONS_FILE, transactions)
    print(
        farsi(
            f"تراکنش با شناسه {new_transaction['id']} و مبلغ {format_money(amount)} با موفقیت ثبت شد."
        )
    )

    type_mapping = {"income": "درآمد", "expense": "مخارج"}
    for index, tx in enumerate(user_transactions, 1):
        t_type = type_mapping.get(tx.get("type"), tx.get("type", "نامشخص"))
        account = tx.get("account", "کارت اصلی")
        amt = tx.get("amount", 0)
        cat = tx.get("category", "-")
        note = tx.get("note", "بدون توضیح")
        date = tx.get("date", "-")

        print(farsi(f"تراکنش {index}: نوع: {t_type} | حساب: {account}"))
        print(farsi(f"مبلغ: {amt} | دسته: {cat} | تاریخ: {date}"))
        print(farsi(f"توضیحات: {note}"))
        print("-" * 35)


def show_all_transactions():
    transactions = load_data(TRANSACTIONS_FILE)

    print(farsi("\n--- همه تراکنش‌ها (ادمین) ---"))
    if not transactions:
        print(farsi("هیچ تراکنشی ثبت نشده است."))
        return

    type_mapping = {"income": "درآمد", "expense": "مخارج"}

    for index, tx in enumerate(transactions, 1):
        t_type = type_mapping.get(tx.get("type"), tx.get("type", "نامشخص"))
        account = tx.get("account", "نامشخص")
        print(
            farsi(
                f"\nتراکنش شماره {index} (شناسه: {tx.get('id')})\n"
                f"کاربر: {tx.get('username', 'نامشخص')} | نوع: {t_type} | حساب: {account}\n"
                f"مبلغ: {format_money(tx.get('amount', 0))}\n"
                f"دسته‌بندی: {tx.get('category', 'نامشخص')}\n"
                f"توضیحات: {tx.get('note', 'بدون توضیح')}\n"
                f"تاریخ: {tx.get('date', 'نامشخص')}\n"
                f"------------------------------"
            )
        )
def show_user_transactions(username):
    transactions = load_data(TRANSACTIONS_FILE)
    
    clean_username = username.get("username") if isinstance(username, dict) else str(username)
    clean_username = clean_username.strip().lower()

    user_transactions = [
        t for t in transactions
        if str(t.get("username", "")).strip().lower() == clean_username
    ]

    print(farsi("\n--- تراکنش‌های شما ---"))
    if not user_transactions:
        print(farsi("هنوز هیچ تراکنشی برای این حساب ثبت نشده است."))
        return

    type_mapping = {"income": "درآمد", "expense": "مخارج"}
    for index, tx in enumerate(user_transactions, 1):
        t_type = type_mapping.get(tx.get("type"), tx.get("type", "نامشخص"))
        account = tx.get("account", "کارت اصلی")
        amt = tx.get("amount", 0)
        cat = tx.get("category", "-")
        note = tx.get("note", "بدون توضیح")
        date = tx.get("date", "-")

        print(farsi(f"تراکنش {index}: نوع: {t_type} | حساب: {account}"))
        print(farsi(f"مبلغ: {amt} | دسته: {cat} | تاریخ: {date}"))
        print(farsi(f"توضیحات: {note}"))
        print("-" * 35)

def delete_transaction(username):
    transactions = load_data(TRANSACTIONS_FILE)
    clean_username = username.get("username") if isinstance(username, dict) else str(username)
    clean_username = clean_username.strip().lower()

    user_txs = [
        t for t in transactions
        if str(t.get("username", "")).strip().lower() == clean_username
    ]

    if not user_txs:
        print(farsi("شما هیچ تراکنشی برای حذف ندارید."))
        return

    print(farsi("\n--- لیست تراکنش‌های شما جهت حذف ---"))
    for t in user_txs:
        t_type = "درآمد" if t.get("type") == "income" else "مخارج"
        print(
            farsi(
                f"شناسه: {t.get('id')} | نوع: {t_type} | مبلغ: {format_money(t.get('amount', 0))} | دسته: {t.get('category')} | تاریخ: {t.get('date')}"
            )
        )
    print(farsi("----------------------------------"))

    target_id_input = parse_farsi_number(
        input(
            farsi(
                "شناسه (ID) تراکنش مورد نظر برای حذف را وارد کنید (یا 0 برای انصراف): "
            )
        )
    )
    if target_id_input == "0" or not target_id_input.isdigit():
        print(farsi("عملیات حذف لغو شد."))
        return

    target_id = int(target_id_input)
    tx_to_delete = next((t for t in user_txs if t.get("id") == target_id), None)

    if not tx_to_delete:
        print(farsi("خطا: تراکنشی با این شناسه متعلق به شما یافت نشد."))
        return

    confirm = (
        input(
            farsi(
                f"آیا از حذف تراکنش شناسه {target_id} مطمئن هستید؟ (y/n): "
            )
        )
        .strip()
        .lower()
    )
    if confirm == "y":
        updated_transactions = [
            t for t in transactions if t.get("id") != target_id
        ]
        save_data(TRANSACTIONS_FILE, updated_transactions)
        print(farsi("تراکنش با موفقیت حذف شد."))
    else:
        print(farsi("حذف تراکنش لغو شد."))


def edit_transaction(username):
    transactions = load_data(TRANSACTIONS_FILE)
    clean_username = username.get("username") if isinstance(username, dict) else str(username)
    clean_username = clean_username.strip().lower()

    user_txs = [
        t for t in transactions
        if str(t.get("username", "")).strip().lower() == clean_username
    ]

    if not user_txs:
        print(farsi("شما هیچ تراکنشی برای ویرایش ندارید."))
        return

    print(farsi("\n--- لیست تراکنش‌های شما جهت ویرایش ---"))
    for t in user_txs:
        t_type = "درآمد" if t.get("type") == "income" else "مخارج"
        print(
            farsi(
                f"شناسه: {t.get('id')} | نوع: {t_type} | مبلغ: {format_money(t.get('amount', 0))} | دسته: {t.get('category')} | تاریخ: {t.get('date')}"
            )
        )
    print(farsi("-----------------------------------"))

    target_id_input = parse_farsi_number(
        input(farsi("شناسه (ID) تراکنش را وارد کنید (یا 0 برای انصراف): "))
    )
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
    new_amount_input = input(
        farsi(f"مبلغ جدید (فعلی: {format_money(tx.get('amount', 0))}): ")
    ).strip()
    if new_amount_input:
        val = validate_amount(new_amount_input)
        if val:
            tx["amount"] = val
        else:
            print(farsi("مبلغ نامعتبر بود؛ مقدار قبلی حفظ شد."))

    # ۲. ویرایش دسته‌بندی
    t_type = tx.get("type")
    categories = (
        INCOME_CATEGORIES if t_type == "income" else EXPENSE_CATEGORIES
    )
    print(
        farsi(
            f"\nدسته‌بندی‌های موجود برای {('درآمد' if t_type == 'income' else 'مخارج')}:"
        )
    )
    for idx, cat in enumerate(categories, 1):
        print(farsi(f"{idx}. {cat}"))

    cat_choice = parse_farsi_number(
        input(farsi(f"انتخاب دسته‌بندی جدید (فعلی: {tx.get('category')}): "))
    )
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
    new_note = input(
        farsi(f"توضیحات جدید (فعلی: {tx.get('note')}): ")
    ).strip()
    if new_note:
        tx["note"] = new_note

    save_data(TRANSACTIONS_FILE, transactions)
    print(farsi("تراکنش با موفقیت ویرایش شد."))
