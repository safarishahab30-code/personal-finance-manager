import os
import tempfile
import pytest
from app import app, init_db, DB_PATH

@pytest.fixture
def client():
    # ساخت دیتابیس موقت برای تست‌ها تا داده‌های اصلی دست‌نخورده بمانند
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

def test_register_and_login(client):
    # تست ثبت نام
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200

    # تست لاگین
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'dashboard' in response.data or b'\xd8\xaf\xd8\xa7\xd8\xb4\xd8\xa8\xd9\x88\xd8\xb1\xd8\xaf' in response.data

def test_set_budget(client):
    # ابتدا ثبت‌نام و لاگین برای احراز هویت
    client.post('/register', data={'username': 'budgetuser', 'password': 'password123'})
    client.post('/login', data={'username': 'budgetuser', 'password': 'password123'})

    # تست افزودن بودجه
    response = client.post('/set_budget', data={
        'category': 'خواربار',
        'limit_amount': '5000000',
        'month': '2026-10'
    }, follow_redirects=True)
    
    assert response.status_code == 200
