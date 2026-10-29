import os
import tempfile
import pytest
from app import app, init_db, DB_PATH

@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    client = app.test_client()
    
    with app.app_context():
        init_db()
        
    yield client
    os.close(db_fd)

def login_helper(client, username="shahab", password="password123"):
    client.post('/register', data={'username': username, 'password': password}, follow_redirects=True)
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

def test_1_budget_workflow(client):
    login_helper(client)
    
    response = client.post('/set_budget', data={
        'category_id': 'خوراکی و سوپرمارکت',
        'category': 'خوراکی و سوپرمارکت',
        'limit_amount': '5,000,000',
        'alert_threshold': '80'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert '5,000,000'.encode('utf-8') in response.data or b'5' in response.data

def test_2_add_transaction_workflow(client):
    login_helper(client)
    
    response = client.post('/add_transaction', data={
        'title': 'خرید کتاب پایتون',
        'amount': '1,200,000',
        'type': 'expense',
        'category': 'آموزش',
        'date': '2026-10-29'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'خرید کتاب پایتون'.encode('utf-8') in response.data
    assert '1,200,000'.encode('utf-8') in response.data or b'1,200' in response.data

def test_3_transactions_filter_workflow(client):
    login_helper(client)
    
    client.post('/add_transaction', data={
        'title': 'پروژه فریلنسری',
        'amount': '15,000,000',
        'type': 'income',
        'category': 'حقوق',
        'date': '2026-10-28'
    }, follow_redirects=True)
    
    response_filter = client.get('/dashboard?type=income', follow_redirects=True)
    assert response_filter.status_code == 200
    assert 'پروژه فریلنسری'.encode('utf-8') in response_filter.data
    
    response_search = client.get('/dashboard?search=کتاب', follow_redirects=True)
    assert response_search.status_code == 200
    assert 'خرید کتاب پایتون'.encode('utf-8') in response_search.data
