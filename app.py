import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from data.database import Database
db = Database()
from data.database import farsi

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # کلید امنیتی سشن
DB_PATH = os.path.join('data', 'finance.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("لطفاً تمامی فیلدها را پر کنید.")
            return render_template("register.html")

        password_hash = generate_password_hash(password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (username, password_hash, now, now)
                )
                conn.commit()
            print(farsi(f"کاربر جدید ثبت شد: {username}"))
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("این نام کاربری قبلاً ثبت شده است.")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            print(farsi(f"ورود موفق: {username}"))
            return redirect(url_for("dashboard"))
        else:
            flash("نام کاربری یا رمز عبور اشتباه است.")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    username = session.get("username", "unknown")
    session.clear()
    print(farsi(f"خروج کاربر: {username}"))
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("قابلیت بازیابی رمز عبور به زودی فعال خواهد شد.")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


# ==========================================
# داشبورد و مدیریت تراکنش‌ها
# ==========================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    current_month = datetime.now().strftime('%Y-%m')
    
    # دریافت فیلترها از فرم HTML
    search = request.args.get('search', '')
    t_type_filter = request.args.get('type', '')

    conn = get_db_connection()

    # ۱. واکشی تراکنش‌ها با اعمال فیلتر
    query = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]
    
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")
    if t_type_filter:
        query += " AND type = ?"
        params.append(t_type_filter)
        
    query += " ORDER BY date DESC, id DESC"
    transactions = conn.execute(query, params).fetchall()

    # ۲. محاسبه آمار کلی (بدون فیلتر برای اینکه درست نمایش داده شوند)
    all_txns = conn.execute('SELECT * FROM transactions WHERE user_id = ?', (user_id,)).fetchall()
    total_income = sum(t['amount'] for t in all_txns if t['type'] == 'income')
    total_expense = sum(t['amount'] for t in all_txns if t['type'] == 'expense')
    balance = total_income - total_expense

    # ۳. داده‌های نمودار (فقط هزینه‌ها)
    expenses = [t for t in all_txns if t['type'] == 'expense']
    category_totals = {}
    for t in expenses:
        cat = t['category']
        category_totals[cat] = category_totals.get(cat, 0) + t['amount']
    
    chart_labels = list(category_totals.keys())
    chart_data = list(category_totals.values())

    # ۴. وضعیت بودجه
    budgets = conn.execute('SELECT * FROM budgets WHERE user_id = ? AND month = ?', (user_id, current_month)).fetchall()
    budgets_status = []
    for b in budgets:
        # محاسبه هزینه مصرف شده برای این دسته‌بندی در این ماه
        spent = conn.execute('''
            SELECT SUM(amount) FROM transactions 
            WHERE user_id = ? AND category = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?
        ''', (user_id, b['category'], current_month)).fetchone()[0] or 0
        
        percentage = (spent / b['limit_amount'] * 100) if b['limit_amount'] > 0 else 0
        
        budgets_status.append({
            'id': b['id'],
            'category': b['category'],
            'limit_amount': b['limit_amount'],
            'spent_amount': spent,
            'percentage': round(percentage, 1)
        })

    conn.close()

    return render_template(
        'dashboard.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        chart_labels=chart_labels,
        chart_data=chart_data,
        budgets_status=budgets_status,
        current_month=current_month
    )

@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    t_type = request.form.get("type", "").strip()
    date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        amount = float(request.form.get("amount", 0))
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash(farsi("مبلغ وارد شده معتبر نیست."), "danger")
        return redirect(url_for("dashboard"))

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # بررسی هوشمند بودجه در صورت ثبت هزینه
        if t_type == "expense":
            # ۱. دریافت سقف بودجه دسته
            cursor.execute(
                "SELECT limit_amount FROM budgets WHERE user_id = ? AND category = ?",
                (user_id, category)
            )
            budget_row = cursor.fetchone()

            if budget_row and budget_row[0] and budget_row[0] > 0:
                limit = float(budget_row[0])

                # ۲. مجموع هزینه‌های ثبت‌شده قبلی در این دسته
                cursor.execute(
                    "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = ? AND type = 'expense'",
                    (user_id, category)
                )
                sum_row = cursor.fetchone()
                current_spent = float(sum_row[0]) if sum_row and sum_row[0] else 0.0

                new_total = current_spent + amount

                # الف) مسدودسازی در صورت رد شدن از ۱۰۰٪ سقف بودجه
                if new_total > limit:
                    flash(farsi(f"خطا: ثبت این هزینه ({amount:,.0f}) باعث عبور از سقف بودجه دسته '{category}' ({limit:,.0f}) می‌شود!"), "danger")
                    return redirect(url_for("dashboard"))

                # ب) هشدار در صورت رسیدن به ۸۰٪ تا ۱۰۰٪ سقف بودجه
                if new_total >= (limit * 0.8):
                    flash(farsi(f"هشدار: شما با ثبت این هزینه به بیش از ۸۰٪ سقف بودجه دسته '{category}' رسیدید."), "warning")

        # ثبت تراکنش در صورت مجاز بودن
        cursor.execute(
            """INSERT INTO transactions (user_id, title, amount, type, category, date, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, amount, t_type, category, date, now)
        )
        conn.commit()

    return redirect(url_for("dashboard"))

@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    txn = conn.execute('SELECT * FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, session['user_id'])).fetchone()
    
    if txn is None:
        conn.close()
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        amount = request.form['amount']
        title = request.form['title']
        category = request.form['category']
        txn_type = request.form['type']
        
        conn.execute('''
            UPDATE transactions 
            SET amount = ?, title = ?, category = ?, type = ?
            WHERE id = ? AND user_id = ?
        ''', (amount, title, category, txn_type, transaction_id, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('edit_transaction.html', transaction=txn)

@app.route('/delete_transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/set_budget', methods=['POST'])
def set_budget():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    category = request.form.get('category', '').strip()
    month = request.form.get(
        'month',
        datetime.now().strftime('%Y-%m')
    ).strip()

    if not category:
        flash('دسته‌بندی بودجه را انتخاب کنید.', 'error')
        return redirect(url_for('dashboard'))

    try:
        limit_amount = float(request.form.get('limit_amount', ''))

        if limit_amount <= 0:
            raise ValueError

    except (ValueError, TypeError):
        flash('مبلغ بودجه باید یک عدد مثبت باشد.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()

    existing = conn.execute(
        '''
        SELECT id
        FROM budgets
        WHERE user_id = ?
          AND category = ?
          AND month = ?
        LIMIT 1
        ''',
        (user_id, category, month)
    ).fetchone()

    if existing:
        conn.execute(
            '''
            UPDATE budgets
            SET limit_amount = ?
            WHERE id = ?
            ''',
            (limit_amount, existing['id'])
        )
    else:
        conn.execute(
            '''
            INSERT INTO budgets
                (user_id, category, limit_amount, month, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                user_id,
                category,
                limit_amount,
                month,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )

    conn.commit()
    conn.close()

    flash('بودجه با موفقیت ذخیره شد.', 'success')
    return redirect(url_for('dashboard'))
@app.route('/delete_budget/<int:id>')
def delete_budget(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM budgets WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    conn.row_factory = sqlite3.Row
    flash('بودجه با موفقیت حذف شد.', 'success')
    return redirect(url_for('dashboard'))

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, created_at, updated_at FROM users WHERE id = ?", (session["user_id"],))
        user = cursor.fetchone()

    return render_template("profile.html", user=user)


@app.route("/change_username", methods=["GET", "POST"])
def change_username():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_username = request.form.get("new_username", "").strip()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not new_username:
            flash("نام کاربری نمی‌تواند خالی باشد.")
            return redirect(url_for("change_username"))

        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET username = ?, updated_at = ? WHERE id = ?",
                    (new_username, now, session["user_id"])
                )
                conn.commit()
                session["username"] = new_username
                flash("نام کاربری با موفقیت تغییر کرد.")
                return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("این نام کاربری قبلاً انتخاب شده است.")
            return redirect(url_for("change_username"))

        return redirect(url_for("profile"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],))
            user = cursor.fetchone()

            if not user or not check_password_hash(user["password_hash"], current_password):
                flash("رمز عبور فعلی نادرست است.")
                return redirect(url_for("change_password"))

            if len(new_password) < 6:
                flash("رمز عبور جدید باید حداقل ۶ کاراکتر باشد.")
                return redirect(url_for("change_password"))

            new_hash = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (new_hash, now, session["user_id"])
            )
            conn.commit()
            flash("رمز عبور با موفقیت به‌روزرسانی شد.")
            return redirect(url_for("dashboard"))

        return redirect(url_for("profile"))


# ==========================================
# اجرای برنامه
# ==========================================

if __name__ == "__main__":
    db.init_db()
    app.run(debug=True)
