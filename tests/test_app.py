import os
import sqlite3
import pytest
from app import app, init_db
import app as app_module

# تنظیم دیتابیس ایزوله برای اجرای تست‌ها
@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_finance.db")
    monkeypatch.setattr(app_module, "DB_PATH", test_db)

    # ایجاد جداول پایه مورد نیاز برنامه
    conn = sqlite3.connect(test_db)
    conn.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        );
    ''')
    conn.commit()
    conn.close()

    init_db()

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        yield client

# ----------------- تست‌های احراز هویت -----------------

def test_register_and_login_flow(client):
    # ۱. ثبت نام موفق
    res = client.post('/register', data={'username': 'shahab', 'password': 'Password123'}, follow_redirects=True)
    assert res.status_code == 200

    # ۲. خطای نام کاربری تکراری
    res_dup = client.post('/register', data={'username': 'shahab', 'password': 'Password123'}, follow_redirects=True)
    assert 'قبلاً ثبت شده است'.encode('utf-8') in res_dup.data

    # ۳. ورود با رمز اشتباه
    res_wrong = client.post('/login', data={'username': 'shahab', 'password': 'wrongpass'}, follow_redirects=True)
    assert 'اشتباه است'.encode('utf-8') in res_wrong.data

    # ۴. ورود موفق
    res_login = client.post('/login', data={'username': 'shahab', 'password': 'Password123'}, follow_redirects=True)
    assert res_login.status_code == 200

    # ۵. خروج
    res_logout = client.get('/logout', follow_redirects=True)
    assert res_logout.status_code == 200

def test_forgot_password(client):
    client.post('/register', data={'username': 'shahab', 'password': 'OldPassword123'})
    res = client.post('/forgot-password', data={'username': 'shahab'}, follow_redirects=True)
    assert res.status_code == 200
    assert 'رمز موقت شما:'.encode('utf-8') in res.data

# ----------------- تست‌های تراکنش و داشبورد -----------------

def test_transactions_and_dashboard(client):
    # ثبت نام و ورود
    client.post('/register', data={'username': 'shahab', 'password': 'Password123'})
    client.post('/login', data={'username': 'shahab', 'password': 'Password123'})

    # ثبت درآمد
    res_inc = client.post('/add_transaction', data={
        'title': 'حقوق تیرماه',
        'amount': '5000000',
        'type': 'income',
        'category': 'حقوق',
        'date': '2026-10-01'
    }, follow_redirects=True)
    assert res_inc.status_code == 200

    # ثبت هزینه
    res_exp = client.post('/add_transaction', data={
        'title': 'خرید کتاب',
        'amount': '250000',
        'type': 'expense',
        'category': 'پوشاک',
        'date': '2026-10-02'
    }, follow_redirects=True)
    assert res_exp.status_code == 200

    # اعتبارسنجی مبلغ نامعتبر
    res_invalid = client.post('/add_transaction', data={
        'title': 'تست نامعتبر',
        'amount': '-100',
        'type': 'expense'
    }, follow_redirects=True)
    assert 'معتبر نیست'.encode('utf-8') in res_invalid.data

    # تست فیلترهای داشبورد
    res_dash = client.get('/dashboard?search=کتاب&type=expense')
    assert res_dash.status_code == 200
    assert 'خرید کتاب'.encode('utf-8') in res_dash.data

    # ویرایش تراکنش (تراکنش با ID=2 مربوط به خرید کتاب)
    res_edit = client.post('/edit_transaction/2', data={
        'title': 'خرید ۲ جلد کتاب',
        'amount': '300000',
        'type': 'expense',
        'category': 'پوشاک',
        'date': '2026-10-02'
    }, follow_redirects=True)
    assert res_edit.status_code == 200

    # حذف تراکنش
    res_del = client.post('/delete_transaction/2', follow_redirects=True)
    assert res_del.status_code == 200

# ----------------- تست‌های مدیریت بودجه -----------------

def test_budget_management(client):
    client.post('/register', data={'username': 'shahab', 'password': 'Password123'})
    client.post('/login', data={'username': 'shahab', 'password': 'Password123'})

    # تنظیم بودجه
    res_set = client.post('/set_budget', data={
        'category': 'خوراکی و سوپرمارکت',
        'limit_amount': '1000000',
        'month': '2026-10'
    }, follow_redirects=True)
    assert res_set.status_code == 200

    # ویرایش بودجه
    res_edit_b = client.post('/edit_budget/1', data={
        'limit_amount': '1200000',
        'alert_threshold': '80'
    }, follow_redirects=True)
    assert res_edit_b.status_code == 200

    # حذف بودجه
    res_del_b = client.post('/delete_budget/1', follow_redirects=True)
    assert res_del_b.status_code == 200

# ----------------- تست خروجی‌های CSV و PDF -----------------

def test_exports(client):
    client.post('/register', data={'username': 'shahab', 'password': 'Password123'})
    client.post('/login', data={'username': 'shahab', 'password': 'Password123'})

    # افزودن یک تراکنش برای فعال بودن خروجی
    client.post('/add_transaction', data={
        'title': 'فروش کتاب دست دوم',
        'amount': '150000',
        'type': 'income',
        'category': 'فروش کتاب',
        'date': '2026-10-15'
    })

    # تست خروجی CSV
    res_csv = client.get('/export_transactions')
    assert res_csv.status_code == 200
    assert res_csv.headers['Content-Type'].startswith('text/csv')

    # تست خروجی PDF
    res_pdf = client.get('/export_pdf')
    assert res_pdf.status_code == 200
    assert res_pdf.headers['Content-Type'] == 'application/pdf'

# ----------------- تست‌های پروفایل کاربری -----------------

def test_profile_updates(client):
    client.post('/register', data={'username': 'shahab', 'password': 'Password123'})
    client.post('/login', data={'username': 'shahab', 'password': 'Password123'})

    # تغییر نام کاربری
    res_u = client.post('/change_username', data={'new_username': 'shahab_new'}, follow_redirects=True)
    assert res_u.status_code == 200
    assert 'با موفقیت تغییر کرد'.encode('utf-8') in res_u.data

    # تغییر رمز عبور
    res_p = client.post('/change_password', data={
        'current_password': 'Password123',
        'new_password': 'NewPassword123',
        'confirm_password': 'NewPassword123'
    }, follow_redirects=True)
    assert res_p.status_code == 200
    assert 'به‌روزرسانی شد'.encode('utf-8') in res_p.data
