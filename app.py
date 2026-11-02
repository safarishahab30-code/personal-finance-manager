import os
import sqlite3
import io
import csv
import secrets
import string
from datetime import datetime, timezone, date, timedelta
import jdatetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, send_file, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from data import database as db
from reports import export_transactions_excel, export_transactions_csv, export_transactions_pdf
from admin_routes import admin_bp

app = Flask(__name__)  
app.register_blueprint(admin_bp)

app.secret_key = "secret-9c8f2b3a1e4d7f6c"


# ---------------------------------------------------------------
#  دسترسی به دیتابیس
# ---------------------------------------------------------------
DB_PATH = os.path.join('data', 'finance.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                limit_amount REAL NOT NULL,
                month TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, category, month)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                category TEXT,
                date TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        ''')

        # بررسی و اضافه کردن ستون‌های مفقود در جدول کاربران (برای دیتابیس‌های قدیمی)
        cursor.execute("PRAGMA table_info(users)")
        u_columns = [row[1] for row in cursor.fetchall()]
        if 'is_admin' not in u_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        if 'is_active' not in u_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")

        # بررسی و اضافه کردن ستون‌های مفقود در جدول تراکنش‌ها
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'title' not in columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN title TEXT")
        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN created_at TEXT")
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN updated_at TEXT")

        # بررسی و اضافه کردن ستون‌های مفقود در جدول budgets
        cursor.execute("PRAGMA table_info(budgets)")
        b_columns = [row[1] for row in cursor.fetchall()]
        if 'created_at' not in b_columns:
            cursor.execute("ALTER TABLE budgets ADD COLUMN created_at TEXT")
        if 'updated_at' not in b_columns:
            cursor.execute("ALTER TABLE budgets ADD COLUMN updated_at TEXT")

        conn.commit()
        print("Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"DB init error: {e}")
        conn.rollback()
    finally:
        conn.close()

# ---------------------------------------------------------------
#  مسیرهای عمومی
# ---------------------------------------------------------------
@app.route('/')
def home():
    return render_template('intro.html')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('intro.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('نام کاربری و رمز عبور الزامی است.', 'warning')
            return render_template('register.html')

        conn = get_db_connection()
        try:
            exists = conn.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
            ).fetchone()
            if exists:
                flash('این نام کاربری قبلاً ثبت شده است.', 'warning')
                return render_template('register.html')

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute(
                'INSERT INTO users (username, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?)',
                (username, generate_password_hash(password), now, now)
            )
            conn.commit()
            flash('ثبت نام با موفقیت انجام شد. لطفاً وارد شوید.', 'success')
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            print(f"Set budget DB error: {e}")  # این خط خطا را در ترمینال چاپ می‌کند
            flash(f'خطا در ذخیره بودجه: {e}', 'danger')
            conn.rollback()

        finally:
            conn.close()

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            
            if user['is_admin'] == 1:
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('dashboard'))
            
        flash('نام کاربری یا رمز عبور اشتباه است.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('با موفقیت از حساب خارج شدید.', 'info')
    return redirect(url_for('login'))
import jdatetime
import sqlite3
from flask import g

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()

def query_db(query, args=(), one=False):
  cur = get_db().execute(query, args)
  rv = cur.fetchall()
  cur.close()
  return (rv[0] if rv else None) if one else rv


# تعریف فیلتر جلالی
@app.template_filter('jalali')
def jalali_filter(date_value):
  if not date_value:
    return ''
  # اگر تاریخ به صورت استرینگ یا شیء datetime باشد، تبدیل به جلالی می‌کنیم
  # فرض بر این است که تاریخ میلادی به دست می‌آید:
  try:
    if isinstance(date_value, str):
      # بسته به فرمت ذخیره در دیتابیس (مثلا YYYY-MM-DD)
      dt = jdatetime.datetime.strptime(date_value[:10], '%Y-%m-%d')
    else:
      dt = jdatetime.datetime.fromgregorian(datetime=date_value)
    return dt.strftime('%Y/%m/%d')
  except Exception:
    return date_value


# ---------------------------------------------------------------
#  داشبورد
from datetime import datetime, date, timedelta
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('لطفاً برای مشاهده داشبورد وارد شوید.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    current_month = datetime.now().strftime('%Y-%m')
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')

    # ۱. دریافت ورودی‌های فیلتر
    search_query = request.args.get('search', '').strip()
    t_type_filter = request.args.get('type', '').strip()
    category_filter = request.args.get('category', '').strip()
    quick_range = request.args.get('quick_range', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    today = date.today()
    if quick_range == 'week':
        start_date = (today - timedelta(days=7)).isoformat()
    elif quick_range == 'month':
        start_date = (today - timedelta(days=30)).isoformat()
    elif quick_range == '3months':
        start_date = (today - timedelta(days=90)).isoformat()

    conn = get_db_connection()
    try:
        all_txns = conn.execute(
            'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC',
            (user_id,)
        ).fetchall()

        total_income = sum(t['amount'] for t in all_txns if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in all_txns if t['type'] == 'expense')
        balance = total_income - total_expense

        categories = sorted(set(t['category'] for t in all_txns if t['category']))

        # ساخت پرس‌وجوی پویا
        query = 'SELECT * FROM transactions WHERE user_id = ?'
        params = [user_id]
        if search_query:
            query += " AND (title LIKE ? OR category LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        if t_type_filter:
            query += ' AND type = ?'
            params.append(t_type_filter)
        if category_filter:
            query += ' AND category = ?'
            params.append(category_filter)
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)

        query += ' ORDER BY date DESC, id DESC'
        transactions = conn.execute(query, params).fetchall()

        # داده چارت
        category_totals = {}
        for t in all_txns:
            if t['type'] == 'expense':
                cat = t['category'] or 'سایر'
                category_totals[cat] = category_totals.get(cat, 0) + t['amount']

        chart_labels = list(category_totals.keys())
        chart_data = list(category_totals.values())

        # بودجه‌ها
        budgets = conn.execute(
            'SELECT * FROM budgets WHERE user_id = ? AND month = ?',
            (user_id, current_month)
        ).fetchall()

        budgets_status = []
        for b in budgets:
            spent_row = conn.execute(
                """SELECT SUM(amount) FROM transactions 
                WHERE user_id = ? AND category = ? AND type = 'expense' 
                AND date LIKE ?""",
            (user_id, b['category'], f"{current_month}%")).fetchone()

            spent = spent_row[0] if spent_row and spent_row[0] else 0.0
            limit = b['limit_amount']
            percentage = (spent / limit * 100) if limit > 0 else 0

            budgets_status.append({
                'id': b['id'],
                'category': b['category'],
                'limit_amount': limit,
                'spent_amount': spent,
                'percentage': round(percentage, 1)
            })

        # --- محاسبات قلک و اهداف مالی ---
        raw_goals = conn.execute(
            'SELECT * FROM savings_goals WHERE user_id = ? ORDER BY id DESC',
            (user_id,)
        ).fetchall()

        savings_goals = []
        for g in raw_goals:
            goal_dict = dict(g)
            progress = (goal_dict['current_amount'] / goal_dict['target_amount'] * 100) if goal_dict['target_amount'] > 0 else 0
            goal_dict['progress'] = min(round(progress, 1), 100)
            savings_goals.append(goal_dict)

        # --- متغیرهای بودجه برای استفاده در قالب ---
        total_budget_limit = sum(b['limit_amount'] for b in budgets_status) if budgets_status else 0
        total_budget_spent = sum(b['spent_amount'] for b in budgets_status) if budgets_status else 0
        remaining_budget = max(0, total_budget_limit - total_budget_spent)

        # --- محاسبات خرج امن روزانه (مبتنی بر موجودی کل) ---
        today_shamsi = jdatetime.date.today()
        days_in_month = 31 if today_shamsi.month <= 6 else (30 if today_shamsi.month <= 11 else (30 if today_shamsi.isleap() else 29))
        days_left = max((days_in_month - today_shamsi.day) + 1, 1)

        safe_daily_spend = int(max(0, balance) / days_left) if balance > 0 else 0

        # -----------------------------------------------------------

        user_expense_cats = [r[0] for r in conn.execute("SELECT DISTINCT category FROM transactions WHERE user_id = ? AND type = 'expense'", (user_id,)).fetchall() if r[0]]
        user_income_cats = [r[0] for r in conn.execute("SELECT DISTINCT category FROM transactions WHERE user_id = ? AND type = 'income'", (user_id,)).fetchall() if r[0]]
        
        default_expenses = ['خوراکی و سوپرمارکت', 'اجاره و قبوض', 'حمل و نقل', 'پوشاک', 'تفریح و سرگرمی', 'درمان و سلامت']
        default_incomes = ['حقوق', 'پاداش', 'فروش کتاب', 'سرمایه‌گذاری', 'یارانه']

        return render_template(
            'dashboard.html',
            username=session.get('username'),
            current_month=current_month, 
            transactions=transactions,
            today=today_jalali,
            all_transactions=all_txns,
            safe_daily_spend=safe_daily_spend,
            days_left=days_left,
            total_budget_limit=total_budget_limit,
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            categories=categories,
            expense_categories=list(dict.fromkeys(default_expenses + user_expense_cats)),
            income_categories=list(dict.fromkeys(default_incomes + user_income_cats)),
            chart_labels=chart_labels,
            chart_data=chart_data,
            budgets=budgets,
            budgets_status=budgets_status,
            savings_goals=savings_goals,
            search_query=search_query,
            selected_type=t_type_filter,
            selected_category=category_filter,
            quick_range=quick_range,
            start_date=start_date,
            end_date=end_date,
        )

    except sqlite3.Error as e:
        print(f"Dashboard DB error: {e}")
        flash('خطایی در بارگذاری داشبورد رخ داد.', 'danger')
        return redirect(url_for('login'))
    finally:
        conn.close()

# ---------------------------------------------------------------
#  مدیریت تراکنش‌ها
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', '').replace(',', '').strip()
    t_type = request.form.get('type', '').strip()
    category = request.form.get('category', '').strip()
    date = request.form.get('date', '').strip() or datetime.now().strftime('%Y-%m-%d')

    if not title or not amount or not t_type:
        flash('عنوان، مبلغ و نوع تراکنش الزامی است.', 'warning')
        return redirect(url_for('dashboard'))

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash('مبلغ وارد شده معتبر نیست.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            '''INSERT INTO transactions
               (user_id, title, amount, type, category, date, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (session['user_id'], title, amount, t_type, category or None, date, now, now)
        )
        conn.commit()
        flash('تراکنش با موفقیت ثبت شد.', 'success')

        # بررسی و اتصال به بودجه در صورت ثبت هزینه
        # بررسی و اتصال به بودجه در صورت ثبت هزینه
        if t_type == 'expense' and category:
            current_month = date[:7] if len(date) >= 7 else datetime.now().strftime('%Y-%m')

            budget = conn.execute("""
                SELECT id, limit_amount FROM budgets
                WHERE user_id = ? AND category = ? AND month = ?
            """, (session['user_id'], category, current_month)).fetchone()

            if not budget:
                conn.execute("""
                    INSERT INTO budgets (user_id, category, limit_amount, month, created_at, updated_at)
                    VALUES (?, ?, 0.0, ?, ?, ?)
                """, (session['user_id'], category, current_month, now, now))
                conn.commit()
                limit_amount = 0.0
            else:
                limit_amount = float(budget['limit_amount'])

            # بررسی تجاوز از سقف بودجه
            if limit_amount > 0:
                total_spent_row = conn.execute("""
                    SELECT SUM(amount) FROM transactions
                    WHERE user_id = ? AND category = ? AND type = 'expense' AND date LIKE ?
                    """, (session['user_id'], category, f"{current_month}%")).fetchone()

                total_spent = total_spent_row[0] or 0.0
                if total_spent > limit_amount:
                    flash(f'هشدار: مجموع هزینه‌های دسته «{category}» از سقف بودجه تعیین‌شده ({limit_amount:,.0f} تومان) عبور کرد!', 'warning')

    except sqlite3.Error as e:
        print(f"Add txn DB error: {e}")
        flash('خطایی در ثبت تراکنش رخ داد.', 'danger')
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('dashboard'))
from flask import jsonify

@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'لطفاً وارد شوید.'}), 401

    conn = get_db_connection()
    try:
        result = conn.execute(
            'DELETE FROM budgets WHERE id = ? AND user_id = ?',
            (budget_id, session['user_id'])
        )
        conn.commit()
        if result.rowcount > 0:
            return jsonify({'success': True, 'message': 'بودجه حذف شد.'})
        else:
            return jsonify({'success': False, 'message': 'بودجه یافت نشد.'}), 404
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/edit_transaction/<int:txn_id>', methods=['GET', 'POST'])
def edit_transaction(txn_id):
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        txn = conn.execute(
            'SELECT * FROM transactions WHERE id = ? AND user_id = ?',
            (txn_id, session['user_id'])
        ).fetchone()

        if not txn:
            flash('تراکنش یافت نشد.', 'danger')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            amount = request.form.get('amount', '').strip()
            t_type = request.form.get('type', '').strip()
            category = request.form.get('category', '').strip()
            date = request.form.get('date', '').strip()

            if not title or not amount or not t_type or not date:
                flash('همه فیلدهای اجباری را پر کنید.', 'warning')
                return render_template('edit_transaction.html', txn=txn)

            try:
                amount = float(amount)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                flash('مبلغ وارد شده معتبر نیست.', 'danger')
                return render_template('edit_transaction.html', txn=txn)

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute(
                '''UPDATE transactions SET
                   title = ?, amount = ?, type = ?, category = ?, date = ?, updated_at = ?
                   WHERE id = ? AND user_id = ?''',
                (title, amount, t_type, category or None, date, now, txn_id, session['user_id'])
            )
            conn.commit()
            flash('تراکنش با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('edit_transaction.html', txn=txn)

    except sqlite3.Error as e:
        print(f"Edit txn DB error: {e}")
        flash('خطایی در ویرایش تراکنش رخ داد.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()
@app.route("/savings/add", methods=["POST"])
def add_savings_goal():
    """ثبت هدف مالی جدید"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()
    raw_amount = request.form.get("target_amount", "").replace(",", "").strip()
    deadline = request.form.get("deadline", "").strip() or None

    try:
        target_amount = float(raw_amount)
    except (ValueError, TypeError):
        target_amount = 0

    if not title or target_amount <= 0:
        flash("عنوان و مبلغ هدف را به درستی وارد کنید.", "error")
        return redirect(url_for("dashboard"))

    db.add_savings_goal(
        user_id=session["user_id"],
        title=title,
        target_amount=target_amount,
        deadline=deadline,
        current_amount=0
    )
    flash("هدف مالی جدید با موفقیت ایجاد شد.", "success")
    return redirect(url_for("dashboard"))


@app.route('/savings/withdraw/<int:goal_id>', methods=['POST'])
def withdraw_savings(goal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    raw_amount = request.form.get('amount', '0').replace(',', '').strip()
    try:
        amount = float(raw_amount)
    except (ValueError, TypeError):
        amount = 0

    if amount > 0:
        conn = get_db_connection()
        goal = conn.execute('SELECT current_amount FROM savings_goals WHERE id = ? AND user_id = ?', 
                            (goal_id, session['user_id'])).fetchone()
        if goal:
            new_amount = max(0.0, goal['current_amount'] - amount)
            conn.execute('UPDATE savings_goals SET current_amount = ? WHERE id = ?', (new_amount, goal_id))
            conn.commit()
            flash('مبلغ با موفقیت از قلک برداشت شد.', 'info')
        conn.close()
    return redirect(url_for('dashboard'))


@app.route("/savings/deposit/<int:goal_id>", methods=["POST"])
def deposit_savings(goal_id):
    """واریز وجه به قلک"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    raw_amount = request.form.get("amount", "0").replace(",", "").strip()
    try:
        amount = float(raw_amount)
    except (ValueError, TypeError):
        amount = 0

    if amount <= 0:
        flash("مبلغ واریزی معتبر نیست.", "error")
        return redirect(url_for("dashboard"))

    success = db.update_savings_goal_amount(goal_id, session["user_id"], amount)
    if success:
        flash("واریز به قلک انجام شد.", "success")
    else:
        flash("خطا در انجام واریز.", "error")

    return redirect(url_for("dashboard"))

@app.route("/savings/delete/<int:goal_id>", methods=["POST"])
def delete_savings_goal(goal_id):
    """حذف هدف مالی"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    db.delete_savings_goal(goal_id, session["user_id"])
    flash("هدف مالی حذف شد.", "info")
    return redirect(url_for("dashboard"))
@app.route('/delete_transaction/<int:txn_id>', methods=['POST'])
def delete_transaction(txn_id):
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        result = conn.execute(
            'DELETE FROM transactions WHERE id = ? AND user_id = ?',
            (txn_id, session['user_id'])
        )
        conn.commit()
        if result.rowcount > 0:
            flash('تراکنش حذف شد.', 'success')
        else:
            flash('تراکنش یافت نشد.', 'warning')
    except sqlite3.Error as e:
        print(f"Delete txn DB error: {e}")
        flash('خطایی در حذف تراکنش رخ داد.', 'danger')
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('dashboard'))


# ---------------------------------------------------------------
#  مدیریت بودجه
# ---------------------------------------------------------------
@app.route('/set_budget', methods=['POST'])
def set_budget():
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    category = request.form.get('category', '').strip() or 'سایر'
    limit_amount = request.form.get('limit_amount', '').replace(',', '').strip()
    month = request.form.get('month', '').strip()
    if not month:
        month = datetime.now().strftime('%Y-%m')

    try:
        limit_amount = float(limit_amount)
        if limit_amount <= 0:
            raise ValueError
    except ValueError:
        flash('مبلغ بودجه معتبر نیست.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # استفاده از INSERT OR REPLACE برای جایگزینی بودجه در صورت وجود
        conn.execute(
            '''INSERT INTO budgets (user_id, category, limit_amount, month, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, category, month) 
               DO UPDATE SET limit_amount = excluded.limit_amount, updated_at = ?''',
            (session['user_id'], category, limit_amount, month, now, now, now)
        )
        conn.commit()
        flash('بودجه با موفقیت ذخیره شد.', 'success')
    except sqlite3.Error as e:
        print(f"Set budget DB error: {e}")
        flash('خطایی در ذخیره بودجه رخ داد.', 'danger')
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('dashboard'))


@app.route('/edit_budget/<int:budget_id>', methods=['POST'])
def edit_budget(budget_id):
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))
    
    new_limit = request.form.get('limit_amount', '').replace(',', '').strip()
    new_threshold = request.form.get('alert_threshold', '80').strip()

    if not new_limit:
        flash('سقف بودجه الزامی است.', 'warning')
        return redirect(url_for('dashboard'))

    try:
        limit_val = float(new_limit)
        threshold_val = int(new_threshold)
        if limit_val <= 0 or not (10 <= threshold_val <= 100):
            raise ValueError
    except ValueError:
        flash('مقادیر وارد شده برای بودجه یا آستانه هشدار معتبر نیستند.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # اگر ستون alert_threshold را در جدول داری، آن را هم آپدیت کن (یا اگر نداری فقط limit_amount)
        conn.execute(
            '''UPDATE budgets 
               SET limit_amount = ?, updated_at = ? 
               WHERE id = ? AND user_id = ?''',
            (limit_val, now, budget_id, session['user_id'])
        )
        conn.commit()
        flash('بودجه با موفقیت ویرایش شد.', 'success')
    except sqlite3.Error as e:
        print(f"Edit budget DB error: {e}")
        flash('خطایی در ویرایش بودجه رخ داد.', 'danger')
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('dashboard'))

# ---------------------------------------------------------------
#  خروجی گزارش
# ---------------------------------------------------------------
@app.route('/export_transactions')
def export_transactions():
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        transactions = conn.execute(
            'SELECT title, category, type, amount, date FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC',
            (session['user_id'],)
        ).fetchall()

        if not transactions:
            flash('هیچ تراکنشی برای خروجی وجود ندارد.', 'warning')
            return redirect(url_for('dashboard'))

        output = io.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(['عنوان', 'دسته‌بندی', 'نوع', 'مبلغ', 'تاریخ'])

        type_map = {'income': 'درآمد', 'expense': 'هزینه'}
        for t in transactions:
            csv_writer.writerow([
                t['title'],
                t['category'] or 'سایر',
                type_map.get(t['type'], t['type']),
                t['amount'],
                t['date']
            ])

        csv_data = '\ufeff' + output.getvalue()

        filename = f"transactions_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response = make_response(csv_data)
        response.headers['Content-Disposition'] = f"attachment; filename={filename}"
        response.headers['Content-type'] = 'text/csv; charset=utf-8'
        return response

    except sqlite3.Error as e:
        print(f"Export DB error: {e}")
        flash('خطایی در تهیه خروجی رخ داد.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()


# ---------------------------------------------------------------
#  پروفایل کاربر
# ---------------------------------------------------------------
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        user = conn.execute(
            'SELECT id, username, created_at, updated_at FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()

        if not user:
            flash('کاربر یافت نشد. لطفاً دوباره وارد شوید.', 'danger')
            session.clear()
            return redirect(url_for('login'))

        return render_template('profile.html', user=user)

    except sqlite3.Error as e:
        print(f"Profile DB error: {e}")
        flash('خطایی در بارگذاری پروفایل رخ داد.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()


@app.route('/change_username', methods=['POST'])
def change_username():
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    new_username = request.form.get('new_username', '').strip()

    if not new_username:
        flash('نام کاربری جدید الزامی است.', 'warning')
        return redirect(url_for('profile'))

    conn = get_db_connection()
    try:
        exists = conn.execute(
            'SELECT id FROM users WHERE username = ? AND id != ?',
            (new_username, session['user_id'])
        ).fetchone()

        if exists:
            flash('این نام کاربری قبلاً استفاده شده است.', 'warning')
            return redirect(url_for('profile'))

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            'UPDATE users SET username = ?, updated_at = ? WHERE id = ?',
            (new_username, now, session['user_id'])
        )
        conn.commit()
        session['username'] = new_username
        flash('نام کاربری با موفقیت تغییر کرد.', 'success')
    except sqlite3.Error as e:
        print(f"Change username DB error: {e}")
        flash('خطایی در تغییر نام کاربری رخ داد.', 'danger')
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('profile'))


@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        flash('همه فیلدها را پر کنید.', 'warning')
        return redirect(url_for('profile'))

    if new_password != confirm_password:
        flash('رمز جدید و تکرار آن یکسان نیستند.', 'warning')
        return redirect(url_for('profile'))

    if len(new_password) < 8:
        flash('رمز جدید باید حداقل ۸ کاراکتر باشد.', 'warning')
        return redirect(url_for('profile'))
    conn = get_db_connection()
    try:
        user = conn.execute(
            'SELECT password_hash FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()

        if not user or not check_password_hash(user["password_hash"], current_password):
            flash("رمز عبور فعلی نادرست است.", "danger")
            return redirect(url_for("profile"))

        new_hash = generate_password_hash(new_password)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (new_hash, now, session["user_id"])
        )

        conn.commit()
        flash("رمز عبور با موفقیت به‌روزرسانی شد.", "success")
        return redirect(url_for("profile"))
    except Exception as e:
        conn.rollback()
        flash("خطایی در تغییر رمز عبور رخ داد.", "danger")
        return redirect(url_for("profile"))
    finally:
        conn.close()
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io

@app.route('/export_pdf')
def export_pdf():
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        transactions = conn.execute(
            'SELECT title, category, type, amount, date FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC',
            (session['user_id'],)
        ).fetchall()

        if not transactions:
            flash('هیچ تراکنشی برای خروجی PDF وجود ندارد.', 'warning')
            return redirect(url_for('dashboard'))

        # ایجاد فایل PDF در حافظه با استفاده از io.BytesIO
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # هدر صفحه
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Financial Transactions Report")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 70, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # رسم جدول ساده تراکنش‌ها
        y = height - 100
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "Title")
        p.drawString(200, y, "Category")
        p.drawString(320, y, "Type")
        p.drawString(400, y, "Amount")
        p.drawString(480, y, "Date")
        
        y -= 15
        p.line(50, y, width - 50, y)
        y -= 20

        p.setFont("Helvetica", 9)
        for t in transactions:
            if y < 50:  # اگر صفحه پر شد، صفحه جدید ایجاد کن
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 9)

            p.drawString(50, y, str(t['title'] or ''))
            p.drawString(200, y, str(t['category'] or 'سایر'))
            p.drawString(320, y, str(t['type']))
            p.drawString(400, y, f"{t['amount']:,.0f}")
            p.drawString(480, y, str(t['date']))
            y -= 20

        p.save()
        buffer.seek(0)

        filename = f"transactions_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response = make_response(buffer.getvalue())
        response.headers['Content-Disposition'] = f"attachment; filename={filename}"
        response.headers['Content-type'] = 'application/pdf'
        return response

    except Exception as e:
        print(f"PDF Export error: {e}")
        flash('خطایی در تولید فایل PDF رخ داد.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        conn = get_db_connection()
        try:
            user = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()

            if user:
                temp_pw = generate_temporary_password()
                hashed_pw = generate_password_hash(temp_pw)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn.execute(
                    "UPDATE users SET password_hash = ?, updated_at = ? WHERE username = ?",
                    (hashed_pw, now, username)
                )
                conn.commit()

                print(f"رمز موقت برای {username}: {temp_pw}")
                flash(f"رمز موقت شما: {temp_pw}", "success")
                return redirect(url_for("login"))
            else:
                flash("کاربری با این نام کاربری یافت نشد.", "danger")

        except sqlite3.Error as e:
            print(f"Forgot password DB error: {e}")
            flash("خطایی در بازیابی رمز رخ داد.", "danger")
            conn.rollback()
        finally:
            conn.close()

    return render_template("forgot_password.html")

def generate_temporary_password(length=10):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))
from datetime import datetime
from flask import send_file, request, flash, redirect, url_for
from data.database import db

@app.route('/backup/download')
def download_backup():
    # ساخت نام یکتا همراه با تاریخ روز
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/backup_{timestamp}.db"
    db.backup_database(backup_file)
    return send_file(backup_file, as_attachment=True, download_name=f"finance_backup_{timestamp}.db")

@app.route('/backup/restore', methods=['POST'])
def restore_backup():
    file = request.files.get('backup_file')
    if not file or file.filename == '':
        flash('هیچ فایلی انتخاب نشده است.', 'error')
        return redirect(url_for('profile'))
    
    temp_path = "backups/temp_restore.db"
    file.save(temp_path)
    if db.restore_database(temp_path):
        flash('پایگاه داده با موفقیت بازیابی شد.', 'success')
    else:
        flash('خطا در بازیابی نسخه پشتیبان.', 'error')
    return redirect(url_for('profile'))
@app.route("/reports/transactions/excel")
def download_transactions_excel():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    transactions = db.get_transactions_by_user(user_id)
    file_data = export_transactions_excel(transactions)

    return send_file(
        file_data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="transactions.xlsx"
    )


@app.route("/reports/transactions/csv")
def download_transactions_csv():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    transactions = db.get_transactions_by_user(user_id)
    file_data = export_transactions_csv(transactions)

    return send_file(
        file_data,
        mimetype="text/csv",
        as_attachment=True,
        download_name="transactions.csv"
    )


@app.route("/reports/transactions/pdf")
def download_transactions_pdf():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    username = session.get("username", "User")
    transactions = db.get_transactions_by_user(user_id)
    file_data = export_transactions_pdf(transactions, username)

    return send_file(
        file_data,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="transactions.pdf"
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
