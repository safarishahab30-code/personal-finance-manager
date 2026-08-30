import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from storage import load_data, save_data  # فرض بر این است که save_data را در storage داری
from auth import verify_password, hash_password # فرض بر این است که hash_password را داری

USERS_FILE = "data/users.json"
TRANSACTIONS_FILE = "data/transactions.json"

app = Flask(__name__)
app.secret_key = "finance_secret_key_change_later"

# --- Helper Functions ---
def get_current_user_record():
    """یافتن رکورد کامل کاربر فعلی از فایل کاربران"""
    if 'user' in session:
        users = load_data(USERS_FILE)
        return next((u for u in users if u.get("username") == session["user"]), None)
    return None

# --- Routes ---

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        users = load_data(USERS_FILE)
        user_record = next(
            (u for u in users if str(u.get("username", "")).strip().lower() == username), 
            None
        )

        if user_record and verify_password(password, user_record.get("password", "")):
            session["user"] = user_record.get("username")
            return redirect(url_for("dashboard"))
        
        return render_template("login.html", error="نام کاربری یا رمز عبور اشتباه است.")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    
    current_user = str(session["user"]).strip().lower()
    transactions = [
        t for t in load_data(TRANSACTIONS_FILE)
        if str(t.get("username", "")).strip().lower() == current_user
    ]

    return render_template("dashboard.html", user=session["user"], transactions=transactions)

@app.route('/add', methods=['POST'])
def add_transaction():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    tx = {
        'id': str(uuid.uuid4())[:8],
        'username': session['user'],
        'type': request.form.get('type'),
        'amount': float(request.form.get('amount', 0)),
        'category': request.form.get('category'),
        'account': request.form.get('account') or 'کارت اصلی',
        'note': request.form.get('note'),
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    transactions = load_data(TRANSACTIONS_FILE)
    transactions.append(tx)
    save_data(TRANSACTIONS_FILE, transactions) # استفاده از تابع استاندارد storage
    return redirect(url_for('dashboard'))

@app.route('/delete/<tx_id>', methods=['POST'])
def delete_transaction(tx_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    current_user = str(session['user']).strip().lower()
    transactions = load_data(TRANSACTIONS_FILE)
    
    updated_transactions = [
        t for t in transactions
        if not (str(t.get('id', '')) == str(tx_id) and str(t.get('username', '')).strip().lower() == current_user)
    ]
    
    save_data(TRANSACTIONS_FILE, updated_transactions)
    return redirect(url_for('dashboard'))

# --- بخش جدید: مدیریت پروفایل (MVP) ---

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user_record = get_current_user_record()
    if not user_record:
        return redirect(url_for("logout"))

    if request.method == "POST":
        action = request.form.get("action")
        users = load_data(USERS_FILE)

        if action == "change_username":
            new_username = request.form.get("new_username", "").strip()
            # بررسی خالی نبودن و یکتا بودن
            if not new_username:
                flash("نام کاربری نمی‌تواند خالی باشد.")
            elif any(u['username'].lower() == new_username.lower() for u in users):
                flash("این نام کاربری قبلاً توسط شخص دیگری انتخاب شده است.")
            else:
                for u in users:
                    if u['username'] == session['user']:
                        u['username'] = new_username
                        u['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        break
                save_data(USERS_FILE, users)
                session['user'] = new_username  # آپدیت کردن سشن
                flash("نام کاربری با موفقیت تغییر یافت.")
                return redirect(url_for("profile"))

        elif action == "change_password":
            old_password = request.form.get("old_password")
            new_password = request.form.get("new_password")

            if verify_password(old_password, user_record['password']):
                # در اینجا فرض می‌کنیم تابع hash_password را در auth داری
                user_record['password'] = hash_password(new_password)
                save_data(USERS_FILE, users)
                flash("رمز عبور با موفقیت تغییر کرد.")
            else:
                flash("رمز عبور فعلی اشتباه است.")

        return redirect(url_for("profile"))

    return render_template("profile.html", user=user_record)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
