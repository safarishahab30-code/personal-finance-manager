import json
import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret_finance_key"

USERS_FILE = "users.json"
TRANSACTIONS_FILE = "transactions.json"

def normalize_username(username):
    """حذف فاصله‌های اضافی و یکسان‌سازی حروف انگلیسی"""
    return str(username or "").strip().lower()

def load_data(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_username_suggestions(base_username, existing_usernames, count=3):
    """تولید پیشنهادات تصادفی در صورت تکراری بودن نام کاربری"""
    suggestions = []
    attempts = 0
    while len(suggestions) < count and attempts < 25:
        attempts += 1
        suffix = random.randint(10, 999)
        candidate = f"{base_username}_{suffix}"
        if candidate not in existing_usernames and candidate not in suggestions:
            suggestions.append(candidate)
    return suggestions

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        norm_user = normalize_username(username)
        
        users = load_data(USERS_FILE)
        user_match = next((u for u in users if normalize_username(u.get("username")) == norm_user), None)
        
        if user_match and user_match.get("password") == password:
            session["user"] = norm_user
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="نام کاربری یا رمز عبور اشتباه است.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        norm_user = normalize_username(username)
        
        if not norm_user or not password:
            return render_template("register.html", error="لطفاً تمام فیلدها را پر کنید.")
            
        users = load_data(USERS_FILE)
        if any(normalize_username(u.get("username")) == norm_user for u in users):
            return render_template("register.html", error="این نام کاربری قبلاً ثبت شده است.")
            
        users.append({"username": norm_user, "password": password})
        save_data(USERS_FILE, users)
        session["user"] = norm_user
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = normalize_username(request.form.get("username", ""))
        users = load_data(USERS_FILE)
        user_match = next((u for u in users if normalize_username(u.get("username")) == username), None)
        
        if user_match:
            return render_template("forgot_password.html", message="درخواست بازیابی ثبت شد.")
        return render_template("forgot_password.html", error="کاربری با این مشخصات یافت نشد.")
        
    return render_template("forgot_password.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
        
    current_user = session["user"]
    all_transactions = load_data(TRANSACTIONS_FILE)
    
    # فیلتر تراکنش‌های مربوط به کاربر لاگین‌شده
    user_txs = [
        tx for tx in all_transactions 
        if normalize_username(tx.get("username")) == current_user
    ]
    
    total_income = sum(float(tx.get("amount", 0)) for tx in user_txs if tx.get("type") == "income")
    total_expense = sum(float(tx.get("amount", 0)) for tx in user_txs if tx.get("type") == "expense")
    balance = total_income - total_expense
    
    return render_template(
        "dashboard.html",
        user=current_user,
        transactions=user_txs,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )

@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    if "user" not in session:
        return redirect(url_for("login"))
        
    current_user = session["user"]
    description = request.form.get("description", "").strip()
    amount = float(request.form.get("amount", 0))
    tx_type = request.form.get("type", "expense")
    category = request.form.get("category", "عمومی").strip()
    
    all_transactions = load_data(TRANSACTIONS_FILE)
    new_tx = {
        "id": len(all_transactions) + 1,
        "username": current_user,
        "description": description,
        "amount": amount,
        "type": tx_type,
        "category": category
    }
    all_transactions.append(new_tx)
    save_data(TRANSACTIONS_FILE, all_transactions)
    
    return redirect(url_for("dashboard"))

@app.route("/edit_transaction/<int:id>", methods=["GET", "POST"])
def edit_transaction(id):
    if "user" not in session:
        return redirect(url_for("login"))
        
    current_user = session["user"]
    all_transactions = load_data(TRANSACTIONS_FILE)
    tx = next((t for t in all_transactions if t.get("id") == id and normalize_username(t.get("username")) == current_user), None)
    
    if not tx:
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        tx["description"] = request.form.get("description", "").strip()
        tx["amount"] = float(request.form.get("amount", 0))
        tx["type"] = request.form.get("type", "expense")
        tx["category"] = request.form.get("category", "عمومی").strip()
        save_data(TRANSACTIONS_FILE, all_transactions)
        return redirect(url_for("dashboard"))
        
    return render_template("edit_transaction.html", transaction=tx)

@app.route("/delete_transaction/<int:id>", methods=["POST", "GET"])
def delete_transaction(id):
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = session["user"]
    all_transactions = load_data(TRANSACTIONS_FILE)

    # حذف تراکنش فقط در صورتی که متعلق به کاربر جاری باشد
    all_transactions = [
        tx for tx in all_transactions
        if not (tx.get("id") == id and normalize_username(tx.get("username")) == current_user)
    ]

    save_data(TRANSACTIONS_FILE, all_transactions)
    return redirect(url_for("dashboard"))

def generate_username_suggestions(base_username):
    base = normalize_username(base_username)
    all_users = load_data(USERS_FILE)
    existing_users = {normalize_username(u.get("username", "")) for u in all_users}
    suggestions = []
    
    while len(suggestions) < 3:
        candidate = f"{base}{random.randint(10, 999)}"
        if candidate not in existing_users and candidate not in suggestions:
            suggestions.append(candidate)
    return suggestions

@app.route("/profile/change-username", methods=["GET", "POST"])
def change_username():
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = session["user"]
    users = load_data(USERS_FILE)
    error = None
    suggestions = []

    if request.method == "POST":
        new_username = request.form.get("new_username", "").strip()
        normalized_new = normalize_username(new_username)

        if not new_username:
            error = "نام کاربری نمی‌تواند خالی باشد."
        elif normalized_new == current_user:
            error = "نام کاربری جدید با نام قبلی یکسان است."
        elif any(normalize_username(u.get("username", "")) == normalized_new for u in users):
            error = "این نام کاربری قبلاً ثبت شده است. پیشنهادهای ما:"
            suggestions = generate_username_suggestions(new_username)
        else:
            # ۱. به‌روزرسانی کاربران + ثبت تاریخ ویرایش
            for u in users:
                if normalize_username(u.get("username", "")) == current_user:
                    u["username"] = new_username
                    u["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            save_data(USERS_FILE, users)

            # ۲. همگام‌سازی تراکنش‌های کاربر قبلی
            transactions = load_data(TRANSACTIONS_FILE)
            for tx in transactions:
                if normalize_username(tx.get("username", "")) == current_user:
                    tx["username"] = new_username
            save_data(TRANSACTIONS_FILE, transactions)

            # ۳. به‌روزرسانی سشن
            session["user"] = normalized_new
            return redirect(url_for("dashboard"))

    return render_template("change_username.html", current_username=current_user, error=error, suggestions=suggestions)


def check_password_strength(password):
    """
    بررسی قدرت رمز عبور:
    - حداقل ۸ کاراکتر
    - شامل حروف بزرگ و کوچک
    - شامل عدد
    - شامل کاراکتر خاص (مانند @, #, $, etc.)
    """
    score = 0
    if len(password) >= 8: score += 1
    if re.search(r"[a-z]", password): score += 1
    if re.search(r"[A-Z]", password): score += 1
    if re.search(r"\d", password): score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): score += 1
    
    # برگرداندن سطح قدرت
    if score <= 2: return "ضعیف", "red"
    if score <= 4: return "متوسط", "orange"
    return "قوی", "green"

@app.route("/profile/change-password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("login"))

    error = None
    success = False

    if request.method == "POST":
        # فعلاً برای اینکه خطا ندهد، فرض می‌کنیم عملیات موفق است
        # بعداً منطق اصلی را اینجا می‌نویسیم
        success = True 

    return render_template("change_password.html", error=error, success=success)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)