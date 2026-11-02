import sqlite3

import pytest

from app import app, init_db
import app as app_module


# =========================================================
# Fixture: دیتابیس ایزوله و کلاینت تست
# =========================================================

@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_finance.db")

    # جایگزین‌کردن دیتابیس اصلی با دیتابیس موقت تست
    monkeypatch.setattr(app_module, "DB_PATH", test_db)

    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    # ساخت تمام جداول در دیتابیس موقت
    init_db()

    with app.test_client() as test_client:
        yield test_client


# =========================================================
# توابع کمکی
# =========================================================
def register_user(client, username="shahab", password="Password123!"):
    return client.post(
        "/register",
        data={
            "username": username,
            "password": password,
        },
        follow_redirects=True,
    )

def login_user(client, username="shahab", password="Password123!"):
    response = client.post(
        "/login",
        data={
            "username": username,
            "password": password,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    return response

def register_and_login(client, username="shahab", password="Password123!"):
    register_response = register_user(client, username=username, password=password)
    assert register_response.status_code == 200

    login_response = login_user(client, username=username, password=password)
    assert login_response.status_code == 200

    return login_response


def get_last_inserted_id(table_name):
    allowed_tables = {"transactions", "budgets"}

    if table_name not in allowed_tables:
        raise ValueError("نام جدول برای تست مجاز نیست.")

    connection = sqlite3.connect(app_module.DB_PATH)

    try:
        row = connection.execute(
            f"SELECT id FROM {table_name} ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        connection.close()

    assert row is not None, f"هیچ رکوردی در جدول {table_name} پیدا نشد."
    return row[0]


# =========================================================
# تست‌های احراز هویت
# =========================================================

def test_register_and_login_flow(client):
    # ۱. ثبت‌نام موفق
    register_response = register_user(client)
    assert register_response.status_code == 200

    # ۲. خطای نام کاربری تکراری
    duplicate_response = register_user(client)
    assert duplicate_response.status_code == 200
    assert "قبلاً ثبت شده است".encode("utf-8") in duplicate_response.data

    # اگر ثبت‌نام باعث ورود خودکار شده باشد، ابتدا خارج می‌شویم
    client.get("/logout", follow_redirects=True)

    # ۳. ورود با رمز اشتباه
    wrong_password_response = login_user(
        client,
        username="shahab",
        password="wrongpass",
    )
    assert wrong_password_response.status_code == 200
    assert "اشتباه است".encode("utf-8") in wrong_password_response.data

    # ۴. ورود موفق
    login_response = login_user(
        client,
        username="shahab",
        password="Password123",
    )
    assert login_response.status_code == 200

    # ۵. خروج موفق
    logout_response = client.get(
        "/logout",
        follow_redirects=True,
    )
    assert logout_response.status_code == 200


def test_forgot_password(client):
    register_response = register_user(
        client,
        username="shahab",
        password="OldPassword123",
    )
    assert register_response.status_code == 200

    response = client.post(
        "/forgot-password",
        data={"username": "shahab"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "رمز موقت شما:".encode("utf-8") in response.data


# =========================================================
# تست‌های تراکنش و داشبورد
# =========================================================

def test_transactions_and_dashboard(client):
    register_and_login(client)

    # ثبت درآمد
    income_response = client.post(
        "/add_transaction",
        data={
            "title": "حقوق تیرماه",
            "amount": "5000000",
            "type": "income",
            "category": "حقوق",
            "date": "2026-10-01",
        },
        follow_redirects=True,
    )

    assert income_response.status_code == 200

    income_id = get_last_inserted_id("transactions")
    assert income_id is not None

    # ثبت هزینه
    expense_response = client.post(
        "/add_transaction",
        data={
            "title": "خرید کتاب",
            "amount": "250000",
            "type": "expense",
            "category": "پوشاک",
            "date": "2026-10-02",
        },
        follow_redirects=True,
    )

    assert expense_response.status_code == 200

    expense_id = get_last_inserted_id("transactions")

    # اعتبارسنجی مبلغ نامعتبر
    invalid_response = client.post(
        "/add_transaction",
        data={
            "title": "تست نامعتبر",
            "amount": "-100",
            "type": "expense",
            "category": "پوشاک",
            "date": "2026-10-03",
        },
        follow_redirects=True,
    )

    assert invalid_response.status_code == 200
    assert "معتبر نیست".encode("utf-8") in invalid_response.data

    # تست فیلترهای داشبورد
    dashboard_response = client.get(
        "/dashboard?search=کتاب&type=expense",
        follow_redirects=True,
    )

    assert dashboard_response.status_code == 200
    assert "خرید کتاب".encode("utf-8") in dashboard_response.data

    # ویرایش تراکنش هزینه
    edit_response = client.post(
        f"/edit_transaction/{expense_id}",
        data={
            "title": "خرید ۲ جلد کتاب",
            "amount": "300000",
            "type": "expense",
            "category": "پوشاک",
            "date": "2026-10-02",
        },
        follow_redirects=True,
    )

    assert edit_response.status_code == 200

    # بررسی ثبت تغییرات در داشبورد
    edited_dashboard_response = client.get(
        "/dashboard?search=۲ جلد&type=expense",
        follow_redirects=True,
    )

    assert edited_dashboard_response.status_code == 200
    assert "خرید ۲ جلد کتاب".encode("utf-8") in edited_dashboard_response.data

    # حذف تراکنش
    delete_response = client.post(
        f"/delete_transaction/{expense_id}",
        follow_redirects=True,
    )

    assert delete_response.status_code == 200

    # بررسی حذف‌شدن تراکنش
    connection = sqlite3.connect(app_module.DB_PATH)

    try:
        deleted_transaction = connection.execute(
            "SELECT id FROM transactions WHERE id = ?",
            (expense_id,),
        ).fetchone()
    finally:
        connection.close()

    assert deleted_transaction is None


# =========================================================
# تست‌های مدیریت بودجه
# =========================================================

def test_budget_management(client):
    register_and_login(client)

    # تنظیم بودجه
    set_budget_response = client.post(
        "/set_budget",
        data={
            "category": "خوراکی و سوپرمارکت",
            "limit_amount": "1000000",
            "month": "2026-10",
        },
        follow_redirects=True,
    )

    assert set_budget_response.status_code == 200

    budget_id = get_last_inserted_id("budgets")

    # ویرایش بودجه
    edit_budget_response = client.post(
        f"/edit_budget/{budget_id}",
        data={
            "limit_amount": "1200000",
            "alert_threshold": "80",
        },
        follow_redirects=True,
    )

    assert edit_budget_response.status_code == 200

    # حذف بودجه
    delete_budget_response = client.post(
        f"/delete_budget/{budget_id}",
        follow_redirects=True,
    )

    assert delete_budget_response.status_code == 200

    # بررسی حذف‌شدن بودجه از دیتابیس
    connection = sqlite3.connect(app_module.DB_PATH)

    try:
        deleted_budget = connection.execute(
            "SELECT id FROM budgets WHERE id = ?",
            (budget_id,),
        ).fetchone()
    finally:
        connection.close()

    assert deleted_budget is None


# =========================================================
# تست خروجی‌های CSV و PDF
# =========================================================

def test_exports(client):
    register_and_login(client)

    # افزودن تراکنش برای فعال‌بودن خروجی‌ها
    transaction_response = client.post(
        "/add_transaction",
        data={
            "title": "فروش کتاب دست دوم",
            "amount": "150000",
            "type": "income",
            "category": "فروش کتاب",
            "date": "2026-10-15",
        },
        follow_redirects=True,
    )

    assert transaction_response.status_code == 200

    # تست خروجی CSV
    csv_response = client.get(
        "/export_transactions",
        follow_redirects=False,
    )

    assert csv_response.status_code == 200
    assert csv_response.headers.get(
        "Content-Type",
        "",
    ).startswith("text/csv")

    # تست خروجی PDF
    pdf_response = client.get(
        "/export_pdf",
        follow_redirects=False,
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers.get(
        "Content-Type",
        "",
    ).startswith("application/pdf")


# =========================================================
# تست‌های پروفایل کاربری
# =========================================================
def test_profile_updates(client):
    register_and_login(client)

    # تغییر نام کاربری
    username_response = client.post(
        "/change_username",
        data={
            "new_username": "shahab_new",
        },
        follow_redirects=True,
    )

    assert username_response.status_code == 200
    assert "با موفقیت تغییر کرد".encode("utf-8") in username_response.data

    # تغییر رمز عبور
    password_response = client.post(
        "/change_password",
        data={
            "current_password": "Password123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123",
        },
        follow_redirects=True,
    )

    assert password_response.status_code == 200
    assert (
        b"\xd8\xa8\xd9\x87\xe2\x80\x8c\xd8\xb1\xd9\x88\xd8\xb2\xd8\xb1\xd8\xa7\xd9\x86\xdb\x8c \xd8\xb4\xd8\xaf" in password_response.data or
        b"\xd8\xb1\xd9\x85\xd8\xb2 \xd8\xb9\xd8\xa8\xd9\x88\xd8\xb1" in password_response.data
    )

    # خروج و بررسی ورود با نام کاربری و رمز جدید
    logout_response = client.get(
        "/logout",
        follow_redirects=True,
    )
    assert logout_response.status_code == 200

    new_login_response = login_user(
        client,
        username="shahab_new",
        password="NewPassword123",
    )

    assert new_login_response.status_code == 200


def test_change_password(client):
    register_and_login(client)
    response = client.post('/change_password', data={
        'current_password': 'Password123',
        'new_password': 'new_secure_password123',
        'confirm_password': 'new_secure_password123'
    }, follow_redirects=True)
    assert (
        b"\xd8\xa8\xd9\x87\xe2\x80\x8c\xd8\xb1\xd9\x88\xd8\xb2\xd8\xb1\xd8\xa7\xd9\x86\xdb\x8c \xd8\xb4\xd8\xaf" in response.data or
        b"\xd8\xb1\xd9\x85\xd8\xb2 \xd8\xb9\xd8\xa8\xd9\x88\xd8\xb1" in response.data
    )

