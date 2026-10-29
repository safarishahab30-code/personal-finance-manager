import pytest
from app import app, init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = ':memory:'
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def login(client, username, password):
    """تابع کمکی برای لاگین در تست‌ها"""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_full_finance_app_workflow(client):
    """تست جامع کل سناریوهای اپلیکیشن مدیریت مالی شخصی"""
    
    # ۱. تست ریدایرکت صفحه اصلی به لاگین
    res = client.get('/')
    assert res.status_code == 302

    # ۲. تست ثبت‌نام کاربر جدید
    res = client.post('/register', data={
        'username': 'shahab',
        'password': 'password123'
    }, follow_redirects=True)
    assert res.status_code == 200

    # ۳. تست ورود با اطلاعات ثبت‌شده
    res = login(client, 'shahab', 'password123')
    assert res.status_code == 200

    # ۴. تست بارگذاری داشبورد
    res = client.get('/dashboard')
    assert res.status_code == 200

    # ۵. تست ثبت تراکنش جدید (درآمد/هزینه)
    res = client.post('/add_transaction', data={
        'type': 'income',
        'amount': '5000000',
        'category': 'حقوق',
        'description': 'حقوق ماهانه'
    }, follow_redirects=True)
    assert res.status_code == 200
    # ۶. تست تنظیم یا به‌روزرسانی بودجه ماهانه
    res = client.post('/set_budget', data={
        'category': 'خوراک',
        'limit_amount': '2000000'
    }, follow_redirects=True)
    assert res.status_code == 200

    # ۷. تست بخش پروفایل و تغییرات تنظیمات کاربری
    res = client.get('/profile')
    assert res.status_code == 200
