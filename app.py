import os
import re
import random
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from data.database import get_connection, init_db

def farsi(text):
    return text

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    encoding='utf-8'
)

app = Flask(__name__)
app.secret_key = "finance_secret_key_shahab"

# راه‌اندازی اولیه جداول در صورت عدم وجود
init_db()

def normalize_username(username):
    """حذف فاصله‌های اضافی و استانداردسازی حروف"""
    return str(username or "").strip().lower()

def check_password_strength(password):
    """بررسی الزامات امنیتی رمز عبور"""
    if len(password) < 8:
        return False, "طول رمز باید حداقل ۸ کاراکتر باشد."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return False, "رمز باید ترکیبی از حروف و اعداد باشد."
    return True, "رمز عبور تایید شد."

def generate_username_suggestions(base_username, count=3):
    """تولید نام‌های کاربری پیشنهادی در صورت تکراری بودن"""
    base = normalize_username(base_username)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    existing_users = {row["username"] for row in cursor.fetchall()}
    conn.close()

    suggestions = []
    attempts = 0
    while len(suggestions) < count and attempts < 30:
        attempts += 1
        candidate = f"{base}_{random.randint(100, 999)}"
        if candidate not in existing_users and candidate not in suggestions:
            suggestions.append(candidate)
    return suggestions

# --- مسیرهای اصلی و احراز هویت ---

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    suggestions = []
    if request.method == "POST":
        username = normalize_username(request.form.get("username", ""))
        password = request.form.get("password", "")

        if not username or not password:
            flash("لطفاً تمام فیلدها را پر کنید.", "warning")
            return render_template("register.html", suggestions=suggestions)

        is_strong, msg = check_password_strength(password)
        if not is_strong:
            flash(f"رمز عبور ضعیف است: {msg}", "danger")
            return render_template("register.html", suggestions=suggestions)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            suggestions = generate_username_suggestions(username)
            flash("این نام کاربری قبلاً ثبت شده است. می‌توانید از نام‌های پیشنهادی استفاده کنید.", "warning")
            return render_template("register.html", suggestions=suggestions)

        hashed_password = generate_password_hash(password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO users (username, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_password, now, now))
        conn.commit()

        cursor.execute("SELECT id, username FROM users WHERE username = ?", (username,))
        new_user = cursor.fetchone()
        conn.close()

        session["user_id"] = new_user["id"]
        session["username"] = new_user["username"]
        logging.info(f"کاربر جدید ثبت نام کرد: {username}")
        print(farsi(f"ثبت‌نام موفق: {username}"))
        return redirect(url_for("dashboard"))

    return render_template("register.html", suggestions=suggestions)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = normalize_username(request.form.get("username", ""))
        password = request.form.get("password", "")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            logging.info(f"ورود موفق کاربر: {username}")
            print(farsi(f"ورود موفق: {username}"))
            return redirect(url_for("dashboard"))
        else:
            flash("نام کاربری یا رمز عبور اشتباه است.", "danger")

    return render_template("login.html")

@app.route("/logout")
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from data.database import Database
from auth import verify_password

def farsi(text):
    return str(text)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'shahab_finance_secure_key_2026')

db = Database()

def verify_user_password(password, stored_hash):
    """
    بررسی رمز عبور با پشتیبانی از هر دو استاندارد:
    1. استاندارد جدید Werkzeug (scrypt/pbkdf2)
    2. استاندارد قدیمی (Custom/scrypt قدیمی)
    """
    if not password or not stored_hash:
        return False
    
    # تلاش اول: استاندارد مدرن Werkzeug
    try:
        if check_password_hash(stored_hash, password):
            return True
    except Exception:
        pass

    # تلاش دوم: استاندارد قدیمی موجود در auth.py
    try:
        return verify_password(password, stored_hash)
    except Exception:
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash(farsi('لطفاً ابتدا وارد حساب کاربری خود شوید.'), 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_username_suggestion(base_username):
    random_digits = ''.join(random.choices(string.digits, k=3))
    return f"{base_username}_{random_digits}"

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        print(farsi('تلاش برای ثبت‌نام کاربر:'), username)

        if not username or not password:
            flash(farsi('لطفاً نام کاربری و رمز عبور را وارد کنید.'), 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash(farsi('رمز عبور با تکرار آن مطابقت ندارد.'), 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash(farsi('رمز عبور باید حداقل ۶ کاراکتر باشد.'), 'danger')
            return render_template('register.html')

        existing_user = db.get_user_by_username(username)
        if existing_user:
            suggestion = generate_username_suggestion(username)
            flash(farsi(f'نام کاربری تکراری است. پیشنهاد: {suggestion}'), 'warning')
            return render_template('register.html', suggested_username=suggestion)

        hashed_password = generate_password_hash(password)
        created = db.create_user(username=username, password_hash=hashed_password, role='user')

        if created:
            flash(farsi('ثبت‌نام با موفقیت انجام شد. اکنون وارد شوید.'), 'success')
            return redirect(url_for('login'))
        else:
            flash(farsi('خطا در ثبت‌نام. دوباره تلاش کنید.'), 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = db.get_user_by_username(username)
        
        print(farsi('تلاش برای ورود با نام کاربری:'), username)
        print(farsi('کاربر در دیتابیس یافت شد:'), bool(user))

        if user and verify_user_password(password, user['password_hash']):
            stored_hash = user['password_hash']

            # ارتقای خودکار هش قدیمی پس از ورود موفق
            if not stored_hash.startswith(('scrypt:', 'pbkdf2:')):
                upgraded_hash = generate_password_hash(password)
                db.update_password(
                    user_id=user['id'],
                    new_password_hash=upgraded_hash,
                    updated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                print(farsi('هش رمز عبور کاربر'), username, f'{farsi("با موفقیت ارتقا یافت.")}')

            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role'] if 'role' in user.keys() else 'user'
            flash(farsi(f'خوش آمدید، {user["username"]}!'), 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(farsi('نام کاربری یا رمز عبور اشتباه است.'), 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get("username", "ناشناس")
    session.clear()
<<<<<<< HEAD
    logging.info(f"کاربر خارج شد: {username}")
    print(farsi(f"خروج کاربر: {username}"))
    return redirect(url_for("login"))

# --- مدیریت حساب کاربری ---

@app.route("/change-username", methods=["GET", "POST"])
def change_username():
    if "user_id" not in session:
        return redirect(url_for("login"))

    suggestions = []
    if request.method == "POST":
        new_username = normalize_username(request.form.get("new_username", ""))

        if not new_username:
            flash("نام کاربری نمی‌تواند خالی باشد.", "warning")
            return render_template("change_username.html", suggestions=suggestions)

        if new_username == session["username"]:
            flash("نام کاربری جدید با نام فعلی یکسان است.", "info")
            return redirect(url_for("dashboard"))

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (new_username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            suggestions = generate_username_suggestions(new_username)
            flash("این نام کاربری قبلاً رزرو شده است. از پیشنهادات زیر انتخاب کنید:", "warning")
            return render_template("change_username.html", suggestions=suggestions)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE users SET username = ?, updated_at = ? WHERE id = ?
        """, (new_username, now, session["user_id"]))
        conn.commit()
        conn.close()

        old_name = session["username"]
        session["username"] = new_username
        logging.info(f"نام کاربری از {old_name} به {new_username} تغییر کرد.")
        print(farsi(f"تغییر نام کاربری موفق: {old_name} -> {new_username}"))
        flash("نام کاربری با موفقیت بروزرسانی شد.", "success")
        return redirect(url_for("dashboard"))

    return render_template("change_username.html", suggestions=suggestions)

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],))
        user = cursor.fetchone()

        if not user or not check_password_hash(user["password_hash"], current_password):
            conn.close()
            flash("رمز عبور فعلی نادرست است.", "danger")
            return render_template("change_password.html")

        is_strong, msg = check_password_strength(new_password)
        if not is_strong:
            conn.close()
            flash(f"رمز عبور جدید ضعیف است: {msg}", "danger")
            return render_template("change_password.html")

        new_hash = generate_password_hash(new_password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?
        """, (new_hash, now, session["user_id"]))
        conn.commit()
        conn.close()

        logging.info(f"رمز عبور کاربر {session['username']} تغییر یافت.")
        print(farsi(f"تغییر رمز موفق برای: {session['username']}"))
        flash("رمز عبور با موفقیت تغییر کرد.", "success")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html")

# --- داشبورد و مدیریت تراکنش‌ها ---

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    current_month = datetime.now().strftime("%Y-%m")
    
    # دریافت فیلترها از URL
    search_query = request.args.get("search", "").strip()
    type_filter = request.args.get("type", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    # ۱. لیست تراکنش‌ها با فیلتر داینامیک
    sql = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]

    if search_query:
        sql += " AND title LIKE ?"
        params.append(f"%{search_query}%")
    
    if type_filter:
        sql += " AND type = ?"
        params.append(type_filter)
    
    sql += " ORDER BY date DESC, id DESC"
    
    cursor.execute(sql, params)
    transactions = [dict(row) for row in cursor.fetchall()]

    # ۲. خلاصه درآمد، هزینه و مانده کل (ثابت)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense
        FROM transactions
        WHERE user_id = ?
    """, (user_id,))
    summary = cursor.fetchone()

    total_income = summary["total_income"]
    total_expense = summary["total_expense"]
    balance = total_income - total_expense

    # ۳. وضعیت بودجه‌بندی و ۴. نمودار (بخش‌های دیگر تغییری نکردند)
    # ... [کد بودجه و نمودار را از فایل قبلی خودت کپی کن] ...

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        budgets_status=budgets_status, # اطمینان حاصل کن این متغیرها تعریف شده باشند
        current_month=current_month,
        chart_labels=chart_labels,
        chart_data=chart_data
    )
@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()
    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0.0

    tx_type = request.form.get("type", "expense")
    category = request.form.get("category", "").strip()
    date = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if title and amount > 0 and category:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (user_id, title, amount, type, category, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session["user_id"], title, amount, tx_type, category, date, created_at))
        conn.commit()
        conn.close()
        flash("تراکنش جدید با موفقیت ثبت شد.", "success")
    else:
        flash("عنوان، دسته‌بندی و مبلغ معتبر الزامی است.", "warning")

    return redirect(url_for("dashboard"))

@app.route('/transaction/edit/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form.get('title')
        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            amount = 0.0
        category = request.form.get('category')
        t_type = request.form.get('type')
        
        cursor.execute('''
            UPDATE transactions 
            SET title = ?, amount = ?, category = ?, type = ? 
            WHERE id = ? AND user_id = ?
        ''', (title, amount, category, t_type, id, session['user_id']))
        conn.commit()
        conn.close()
        flash('تراکنش با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('dashboard'))
    
    cursor.execute('SELECT * FROM transactions WHERE id = ? AND user_id = ?', (id, session['user_id']))
    transaction = cursor.fetchone()
    conn.close()
    
    if not transaction:
        flash('تراکنش مورد نظر یافت نشد.', 'danger')
        return redirect(url_for('dashboard'))
        
    return render_template('edit_transaction.html', transaction=transaction)

@app.route("/delete_transaction/<int:id>", methods=["POST", "GET"])
def delete_transaction(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (id, session["user_id"]))
    conn.commit()
    conn.close()

    flash("تراکنش با موفقیت حذف شد.", "info")
    return redirect(url_for("dashboard"))

# --- مسیرهای مدیریت بودجه ---

@app.route("/set_budget", methods=["POST"])
def set_budget():
    if "user_id" not in session:
        return redirect(url_for("login"))

    category = request.form.get("category", "").strip()
    try:
        limit_amount = float(request.form.get("limit_amount", 0))
    except ValueError:
        limit_amount = 0.0

    month = request.form.get("month") or datetime.now().strftime("%Y-%m")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not category or limit_amount <= 0:
        flash("دسته‌بندی و سقف بودجه معتبر الزامی است.", "warning")
        return redirect(url_for("dashboard"))

    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO budgets (user_id, category, limit_amount, month, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, category, month) 
        DO UPDATE SET limit_amount = excluded.limit_amount
    """, (session["user_id"], category, limit_amount, month, created_at))
    
    conn.commit()
    conn.close()
    
    flash(f"بودجه دسته‌بندی «{category}» با موفقیت ثبت شد.", "success")
    return redirect(url_for("dashboard"))

@app.route("/delete_budget/<int:id>", methods=["POST", "GET"])
def delete_budget(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM budgets WHERE id = ? AND user_id = ?", (id, session["user_id"]))
    conn.commit()
    conn.close()

    flash("بودجه مورد نظر حذف شد.", "info")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
=======
    flash(farsi('با موفقیت خارج شدید.'), 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    transactions = db.get_transactions_by_user(user_id) or []

    total_income = sum(t['amount'] for t in transactions if t.get('type') == 'income')
    total_expense = sum(t['amount'] for t in transactions if t.get('type') == 'expense')
    balance = total_income - total_expense

    return render_template(
        'dashboard.html',
        username=session.get('username'),
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )

@app.route('/transaction/add', methods=['POST'])
@login_required
def add_transaction():
    user_id = session['user_id']
    title = request.form.get('title', '').strip()
    amount_str = request.form.get('amount', '').strip()
    category = request.form.get('category', '').strip()
    trans_type = request.form.get('type', '').strip()
    date_str = request.form.get('date', '').strip()

    if not title or not amount_str or not category or trans_type not in ['income', 'expense']:
        flash(farsi('اطلاعات تراکنش ناقص است.'), 'danger')
        return redirect(url_for('dashboard'))

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError()
    except ValueError:
        flash(farsi('مبلغ باید یک عدد مثبت باشد.'), 'danger')
        return redirect(url_for('dashboard'))

    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')

    db.add_transaction(
        user_id=user_id,
        title=title,
        amount=amount,
        category=category,
        transaction_type=trans_type,
        date=date_str
    )
    flash(farsi('تراکنش با موفقیت ثبت شد.'), 'success')
    return redirect(url_for('dashboard'))

@app.route('/transaction/delete/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    user_id = session['user_id']
    success = db.delete_transaction(transaction_id=transaction_id, user_id=user_id)
    if success:
        flash(farsi('تراکنش با موفقیت حذف شد.'), 'info')
    else:
        flash(farsi('خطا در حذف تراکنش یا دسترسی غیرمجاز.'), 'danger')
    return redirect(url_for('dashboard'))

@app.route('/profile')
@login_required
def profile():
    user = db.get_user_by_id(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/profile/change-username', methods=['POST'])
@login_required
def change_username():
    new_username = request.form.get('new_username', '').strip()
    user_id = session['user_id']

    if not new_username:
        flash(farsi('نام کاربری جدید نمی‌تواند خالی باشد.'), 'danger')
        return redirect(url_for('profile'))

    if new_username == session.get('username'):
        flash(farsi('نام کاربری جدید نمی‌تواند با نام قبلی یکسان باشد.'), 'warning')
        return redirect(url_for('profile'))

    existing = db.get_user_by_username(new_username)
    if existing:
        suggestion = generate_username_suggestion(new_username)
        flash(farsi(f'این نام کاربری از قبل وجود دارد. پیشنهاد ما: {suggestion}'), 'warning')
        return redirect(url_for('profile'))

    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    success = db.update_username(user_id=user_id, new_username=new_username, updated_at=updated_at)

    if success:
        session['username'] = new_username
        flash(farsi('نام کاربری با موفقیت تغییر کرد.'), 'success')
    else:
        flash(farsi('خطا در تغییر نام کاربری.'), 'danger')

    return redirect(url_for('profile'))

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_new_password = request.form.get('confirm_new_password', '').strip()
    user_id = session['user_id']

    user = db.get_user_by_id(user_id)
    if not user or not verify_user_password(current_password, user['password_hash']):
        flash(farsi('رمز عبور فعلی نادرست است.'), 'danger')
        return redirect(url_for('profile'))

    if len(new_password) < 6:
        flash(farsi('رمز عبور جدید آسان است! حداقل باید ۶ کاراکتر باشد.'), 'warning')
        return redirect(url_for('profile'))

    if new_password != confirm_new_password:
        flash(farsi('تکرار رمز عبور جدید یکسان نیست.'), 'danger')
        return redirect(url_for('profile'))

    new_hash = generate_password_hash(new_password)
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    success = db.update_password(user_id=user_id, new_password_hash=new_hash, updated_at=updated_at)

    if success:
        flash(farsi('رمز عبور با موفقیت بروزرسانی شد.'), 'success')
    else:
        flash(farsi('خطا در بروزرسانی رمز عبور.'), 'danger')

    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
