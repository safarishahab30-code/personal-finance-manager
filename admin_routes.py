from flask import Blueprint, render_template, redirect, url_for, session, flash, request, make_response
import sqlite3
import csv
from io import StringIO
from functools import wraps
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

DB_PATH = os.path.join('data', 'finance.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or (not session.get('is_admin') and session.get('role') != 'admin'):
            flash('دسترسی غیرمجاز!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')  
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    user_filter = request.args.get('user_id', type=int)
    type_filter = request.args.get('type', type=str)
    
    users = conn.execute('SELECT id, username, is_admin FROM users').fetchall()
    
    query = '''
        SELECT t.*, u.username 
        FROM transactions t 
        JOIN users u ON t.user_id = u.id 
        WHERE 1=1
    '''
    params = []
    
    if user_filter:
        query += ' AND t.user_id = ?'
        params.append(user_filter)
        
    if type_filter in ['income', 'expense']:
        query += ' AND t.type = ?'
        params.append(type_filter)
        
    query += ' ORDER BY t.date DESC'
    transactions = conn.execute(query, params).fetchall()
    
    # محاسبه آمار کلان سیستم
    stats = conn.execute('''
        SELECT 
            (SELECT COUNT(*) FROM users) as total_users,
            COUNT(*) as total_count,
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense,
            COALESCE(AVG(amount), 0) as avg_amount
        FROM transactions
    ''').fetchone()
    
    conn.close()
    
    return render_template(
        'admin.html', 
        users=users, 
        transactions=transactions, 
        stats=stats, 
        user_filter=user_filter, 
        type_filter=type_filter
    )

@admin_bp.route('/export/csv')
@admin_required
def admin_export_csv():
    conn = get_db_connection()
    transactions = conn.execute('SELECT t.*, u.username FROM transactions t JOIN users u ON t.user_id = u.id ORDER BY t.date DESC').fetchall()
    conn.close()
    
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Username', 'Title', 'Type', 'Amount', 'Category', 'Date'])
    
    for tx in transactions:
        title = tx['title'] if 'title' in tx.keys() and tx['title'] else '-'
        writer.writerow([tx['id'], tx['username'], title, tx['type'], tx['amount'], tx['category'], tx['date']])
        
    output = make_response(si.getvalue().encode('utf-8-sig'))
    output.headers["Content-Disposition"] = "attachment; filename=system_transactions_report.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8-sig"
    return output

@admin_bp.route('/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    conn = get_db_connection()
    if user_id != session['user_id']:
        conn.execute('UPDATE users SET is_admin = CASE WHEN is_admin = 1 THEN 0 ELSE 1 END WHERE id = ?', (user_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    if user_id != session['user_id']:
        conn.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete-transaction/<int:tx_id>', methods=['POST'])
@admin_required
def admin_delete_transaction(tx_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM transactions WHERE id = ?', (tx_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin.admin_dashboard'))
