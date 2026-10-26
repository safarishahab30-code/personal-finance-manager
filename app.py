import os
import sqlite3
import os
import io
import csv
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from data import database as db


# مسیر واقعی دیتابیس
DB_PATH = os.path.join('data', 'finance.db')

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "a_long_random_secret_key_for_dev_only_change_me")


# ---------------------------------------------------------------
#  دسترسی به دیتابیس
# ---------------------------------------------------------------
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
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                category TEXT,
                date TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
        ''')
        conn.commit()
        print("Database initialized.")
    except sqlite3.Error as e:
        print(f"DB init error: {e}")
        conn.rollback()
    finally:
        conn.close()


# ---------------------------------------------------------------
#  مسیرهای عمومی
# ---------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


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
            print(f"Register DB error: {e}")
            flash('خطایی در ثبت نام رخ داد.', 'danger')
            return render_template('register.html')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        try:
            user = conn.execute(
                'SELECT id, username, password_hash FROM users WHERE username = ?', (username,)
            ).fetchone()

            if user and check_password_hash(user['password_hash'], password):
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('ورود شما موفقیت‌آمیز بود.', 'success')
                return redirect(url_for('dashboard'))

            flash('نام کاربری یا رمز عبور اشتباه است.', 'danger')
            return render_template('login.html')
        except sqlite3.Error as e:
            print(f"Login DB error: {e}")
            flash('خطایی در ورود رخ داد.', 'danger')
            return render_template('login.html')
        finally:
            conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('با موفقیت از حساب خارج شدید.', 'info')
    return redirect(url_for('login'))
import jdatetime


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
# ---------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('لطفاً برای مشاهده داشبورد وارد شوید.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    current_month = datetime.now().strftime('%Y-%m')

    search_query = request.args.get('search', '').strip()
    t_type_filter = request.args.get('type', '').strip()
    category_filter = request.args.get('category', '').strip()

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

        # ساخت پرس‌وجوی فیلترشده
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

        query += ' ORDER BY date DESC, id DESC'
        transactions = conn.execute(query, params).fetchall()

        # داده چارت هزینه‌ها بر اساس دسته‌بندی
        category_totals = {}
        for t in all_txns:
            if t['type'] == 'expense':
                cat = t['category'] or 'سایر'
                category_totals[cat] = category_totals.get(cat, 0) + t['amount']

        chart_labels = list(category_totals.keys())
        chart_data = list(category_totals.values())

        # بودجه‌های ماه جاری
        budgets = conn.execute(
            'SELECT * FROM budgets WHERE user_id = ? AND month = ?',
            (user_id, current_month)
        ).fetchall()

        budgets_status = []
        for b in budgets:
            spent_row = conn.execute(
                "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?",
                (user_id, b['category'], current_month)
            ).fetchone()
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

        return render_template(
            'dashboard.html',
            username=session.get('username'),
            transactions=transactions,
            all_transactions=all_txns,
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            categories=categories,
            chart_labels=chart_labels,
            chart_data=chart_data,
            budgets=budgets,
            budgets_status=budgets_status,
            search_query=search_query,
            type_filter=t_type_filter,
            category_filter=category_filter
        )

    except sqlite3.Error as e:
        print(f"Dashboard DB error: {e}")
        flash('خطایی در بارگذاری داشبورد رخ داد.', 'danger')
        return redirect(url_for('login'))
    finally:
        conn.close()


# ---------------------------------------------------------------
#  مدیریت تراکنش‌ها
# ---------------------------------------------------------------
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', '').strip()
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
    except sqlite3.Error as e:
        print(f"Add txn DB error: {e}")
        flash('خطایی در ثبت تراکنش رخ داد.', 'danger')
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('dashboard'))


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
    limit_amount = request.form.get('limit_amount', '').strip()
    month = request.form.get('month', '').strip() or datetime.now().strftime('%Y-%m')

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
        conn.execute(
            '''INSERT INTO budgets (user_id, category, limit_amount, month, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, category, month)
               DO UPDATE SET limit_amount = excluded.limit_amount, updated_at = excluded.updated_at''',
            (session['user_id'], category, limit_amount, month, now, now)
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


@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
    if 'user_id' not in session:
        flash('لطفاً وارد شوید.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        result = conn.execute(
            'DELETE FROM budgets WHERE id = ? AND user_id = ?',
            (budget_id, session['user_id'])
        )
        conn.commit()
        if result.rowcount > 0:
            flash('بودجه حذف شد.', 'success')
        else:
            flash('بودجه یافت نشد.', 'warning')
    except sqlite3.Error as e:
        print(f"Delete budget DB error: {e}")
        flash('خطایی در حذف بودجه رخ داد.', 'danger')
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

    new_username = request.form.get('username', '').strip()

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
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (new_hash, now, session["user_id"])
        )
        conn.commit()
        flash("رمز عبور با موفقیت به‌روزرسانی شد.", "success")
        return redirect(url_for("dashboard"))
    except Exception as e:
        conn.rollback()
        flash("خطایی در تغییر رمز عبور رخ داد.", "danger")
        return redirect(url_for("profile"))
    finally:
        conn.close()


if __name__ == "__main__":
    db_instance = db.Database()
    db_instance.init_db()
    init_db()
    app.run(debug=True)
