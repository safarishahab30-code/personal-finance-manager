import os
import re
import uuid
import random
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from auth import (
    hash_password,
    verify_password,
    check_password_strength,
    generate_strong_password
)
from storage import load_data, save_data

# ---------- تنظیمات ----------

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = str(BASE_DIR / "data" / "users.json")
TRANSACTIONS_FILE = str(BASE_DIR / "data" / "transactions.json")

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "finance_secret_key_change_later"
)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


# ---------- توابع کمکی ----------

def farsi(text):
    """تبدیل مقدار به رشته برای چاپ در ترمینال."""
    return str(text)


def normalize_username(username):
    """حذف فاصله‌های اضافی و یکسان‌سازی حروف انگلیسی."""
    return str(username or "").strip().lower()


def generate_username_suggestion(base_name):
    """تولید یک نام کاربری پیشنهادی مشابه و تصادفی."""
    clean_base = re.sub(r"[^a-zA-Z0-9_]", "", base_name)[:15] or "user"
    suffix = random.randint(100, 999)
    return f"{clean_base}_{suffix}"


def get_current_user_record():
    """پیداکردن رکورد کامل کاربر واردشده."""
    current_username = normalize_username(session.get("user"))

    if not current_username:
        return None

    users = load_data(USERS_FILE)
    if not isinstance(users, list):
        return None

    return next(
        (
            user
            for user in users
            if normalize_username(user.get("username")) == current_username
        ),
        None
    )


# ---------- صفحه اصلی ----------

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ---------- ورود ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = normalize_username(request.form.get("username"))
    password = request.form.get("password", "")

    if not username or not password:
        return render_template(
            "login.html",
            error="نام کاربری و رمز عبور را وارد کنید."
        )

    users = load_data(USERS_FILE)

    if not isinstance(users, list):
        print(farsi("خطا: محتوای users.json باید یک لیست باشد."))
        return render_template(
            "login.html",
            error="خطا در خواندن اطلاعات کاربران."
        )

    user_record = next(
        (
            user
            for user in users
            if normalize_username(user.get("username")) == username
        ),
        None
    )

    print(farsi("----- بررسی ورود -----"))
    print(farsi(f"مسیر فایل کاربران: {USERS_FILE}"))
    print(farsi(f"تعداد کاربران خوانده‌شده: {len(users)}"))
    print(farsi(f"نام کاربری واردشده: {username}"))
    print(farsi(f"کاربر پیدا شد: {user_record is not None}"))

    password_is_valid = False

    if user_record:
        stored_password = str(user_record.get("password", ""))

        try:
            password_is_valid = verify_password(password, stored_password)
        except (TypeError, ValueError) as error:
            print(farsi(f"خطا هنگام بررسی رمز عبور: {error}"))

        print(farsi(f"رمز عبور صحیح است: {password_is_valid}"))

    if user_record and password_is_valid:
        session.clear()
        session["user"] = user_record["username"]

        print(farsi("ورود موفق بود؛ انتقال به داشبورد."))
        return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        error="نام کاربری یا رمز عبور اشتباه است."
    )


# ---------- ثبت‌نام ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = normalize_username(request.form.get("username"))
        password = request.form.get("password", "")
        sec_question = request.form.get("security_question", "").strip()
        sec_answer = request.form.get("security_answer", "").strip().lower()

        if not username or not password:
            return render_template("register.html", error="نام کاربری و رمز عبور الزامی است.")

        if not sec_answer:
            return render_template("register.html", error="پاسخ سوال امنیتی الزامی است.")

        if not USERNAME_RE.fullmatch(username):
            return render_template("register.html", error="نام کاربری باید ۳ تا ۲۰ کاراکتر انگلیسی یا عدد باشد.")

        strength_error = check_password_strength(password)
        if strength_error:
            return render_template("register.html", error=f"رمز عبور آسان است: {strength_error}")

        users = load_data(USERS_FILE)
        if not isinstance(users, list):
            users = []

        if any(normalize_username(u.get("username")) == username for u in users):
            suggestion = generate_username_suggestion(username)
            return render_template("register.html", error=f"این نام کاربری قبلاً ثبت شده است. پیشنهاد: {suggestion}")

        role = "admin" if not users else "user"
        now = datetime.now().isoformat()

        new_user = {
            "username": username,
            "password": hash_password(password),
            "role": role,
            "security_question": sec_question,
            "security_answer": hash_password(sec_answer),
            "created_at": now,
            "updated_at": now
        }
        users.append(new_user)
        save_data(USERS_FILE, users)

        print(farsi(f"کاربر جدید با موفقیت ثبت شد: {username}"))
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------- بازیابی رمز عبور ----------

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = normalize_username(request.form.get("username"))
        answer = request.form.get("security_answer", "").strip().lower()
        new_password = request.form.get("new_password", "")

        if not username or not answer or not new_password:
            return render_template("forgot_password.html", error="تمامی فیلدها الزامی هستند.")

        users = load_data(USERS_FILE)
        user = next((u for u in users if normalize_username(u.get("username")) == username), None)

        if not user or not user.get("security_answer"):
            return render_template("forgot_password.html", error="کاربر یا سوال امنیتی یافت نشد.")

        if not verify_password(answer, user["security_answer"]):
            return render_template("forgot_password.html", error="پاسخ سوال امنیتی نادرست است.")

        strength_error = check_password_strength(new_password)
        if strength_error:
            return render_template("forgot_password.html", error=f"رمز عبور آسان است: {strength_error}")

        user["password"] = hash_password(new_password)
        user["updated_at"] = datetime.now().isoformat()
        save_data(USERS_FILE, users)

        print(farsi(f"رمز عبور کاربر {username} با موفقیت بازنشانی شد."))
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


# ---------- داشبورد ----------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    current_username = normalize_username(session["user"])
    all_transactions = load_data(TRANSACTIONS_FILE)

    if not isinstance(all_transactions, list):
        all_transactions = []

    user_transactions = [
        transaction
        for transaction in all_transactions
        if normalize_username(transaction.get("username")) == current_username
    ]

    return render_template(
        "dashboard.html",
        user=session["user"],
        transactions=user_transactions
    )


# ---------- افزودن تراکنش ----------

@app.route("/add", methods=["POST"])
def add_transaction():
    if "user" not in session:
        return redirect(url_for("login"))

    amount_text = request.form.get("amount", "").strip()

    try:
        amount = float(amount_text)
    except ValueError:
        flash("مبلغ واردشده معتبر نیست.")
        return redirect(url_for("dashboard"))

    if amount <= 0:
        flash("مبلغ باید بیشتر از صفر باشد.")
        return redirect(url_for("dashboard"))

    transaction_type = request.form.get("type", "").strip()
    category = request.form.get("category", "").strip()
    account = request.form.get("account", "").strip() or "کارت اصلی"
    note = request.form.get("note", "").strip()

    transaction = {
        "id": str(uuid.uuid4())[:8],
        "username": session["user"],
        "type": transaction_type,
        "amount": amount,
        "category": category,
        "account": account,
        "note": note,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    transactions = load_data(TRANSACTIONS_FILE)

    if not isinstance(transactions, list):
        transactions = []

    transactions.append(transaction)
    save_data(TRANSACTIONS_FILE, transactions)

    flash("تراکنش با موفقیت ثبت شد.")
    return redirect(url_for("dashboard"))


# ---------- حذف تراکنش ----------

@app.route("/delete/<tx_id>", methods=["POST"])
def delete_transaction(tx_id):
    if "user" not in session:
        return redirect(url_for("login"))

    current_username = normalize_username(session["user"])
    transactions = load_data(TRANSACTIONS_FILE)

    if not isinstance(transactions, list):
        transactions = []

    updated_transactions = [
        transaction
        for transaction in transactions
        if not (
            str(transaction.get("id", "")) == str(tx_id)
            and normalize_username(transaction.get("username"))
            == current_username
        )
    ]

    save_data(TRANSACTIONS_FILE, updated_transactions)
    flash("تراکنش حذف شد.")

    return redirect(url_for("dashboard"))


# ---------- API پیشنهاد رمز عبور قوی ----------

@app.route("/suggest-password", methods=["GET"])
def suggest_password():
    """ارائه پیشنهاد رمز عبور قوی و ایمن."""
    suggested = generate_strong_password()
    return jsonify({"suggested_password": suggested})


# ---------- پروفایل کاربر ----------

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    user_record = get_current_user_record()

    if not user_record:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("profile.html", user=user_record)

    action = request.form.get("action", "").strip()
    users = load_data(USERS_FILE)

    if not isinstance(users, list):
        flash("خطا در خواندن اطلاعات کاربران.")
        return redirect(url_for("profile"))

    current_username = normalize_username(session["user"])

    current_user = next(
        (
            user
            for user in users
            if normalize_username(user.get("username")) == current_username
        ),
        None
    )

    if not current_user:
        session.clear()
        return redirect(url_for("login"))

    if action == "change_username":
        new_username = request.form.get("new_username", "").strip()
        normalized_new_username = normalize_username(new_username)

        if not normalized_new_username:
            flash("نام کاربری نمی‌تواند خالی باشد.")
            return redirect(url_for("profile"))

        if not USERNAME_RE.fullmatch(new_username):
            flash("نام کاربری باید ۳ تا ۲۰ کاراکتر انگلیسی یا عدد باشد.")
            return redirect(url_for("profile"))

        username_exists = any(
            normalize_username(user.get("username"))
            == normalized_new_username
            and user is not current_user
            for user in users
        )

        if username_exists:
            suggestion = generate_username_suggestion(new_username)
            flash(f"این نام کاربری قبلاً انتخاب شده است. پیشنهاد: {suggestion}")
            return redirect(url_for("profile"))

        old_username = current_user["username"]
        current_user["username"] = new_username
        current_user["updated_at"] = datetime.now().isoformat()

        save_data(USERS_FILE, users)

        transactions = load_data(TRANSACTIONS_FILE)
        if isinstance(transactions, list):
            for transaction in transactions:
                if (
                    normalize_username(transaction.get("username"))
                    == normalize_username(old_username)
                ):
                    transaction["username"] = new_username

            save_data(TRANSACTIONS_FILE, transactions)

        session["user"] = new_username
        flash("نام کاربری با موفقیت تغییر کرد.")
        return redirect(url_for("profile"))

    if action == "change_password":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not old_password or not new_password:
            flash("رمز فعلی و رمز جدید را وارد کنید.")
            return redirect(url_for("profile"))

        if not verify_password(old_password, current_user.get("password", "")):
            flash("رمز عبور فعلی اشتباه است.")
            return redirect(url_for("profile"))

        if new_password != confirm_password:
            flash("تکرار رمز عبور جدید مطابقت ندارد.")
            return redirect(url_for("profile"))

        strength_error = check_password_strength(new_password)
        if strength_error:
            flash(f"رمز عبور جدید آسان است: {strength_error}")
            return redirect(url_for("profile"))

        current_user["password"] = hash_password(new_password)
        current_user["updated_at"] = datetime.now().isoformat()

        save_data(USERS_FILE, users)
        flash("رمز عبور با موفقیت تغییر کرد.")
        return redirect(url_for("profile"))

    flash("عملیات درخواستی معتبر نیست.")
    return redirect(url_for("profile"))


# ---------- پنل ادمین: تغییر رمز کاربر توسط ادمین ----------

@app.route("/admin/reset-password", methods=["POST"])
def admin_reset_password():
    if "user" not in session:
        return redirect(url_for("login"))

    current_user = get_current_user_record()
    if not current_user or current_user.get("role") != "admin":
        flash("دسترسی غیرمجاز: فقط ادمین مجاز است.")
        return redirect(url_for("dashboard"))

    target_username = normalize_username(request.form.get("target_username"))
    new_password = request.form.get("new_password", "")

    if not target_username or not new_password:
        flash("نام کاربری و رمز جدید الزامی است.")
        return redirect(url_for("profile"))

    strength_error = check_password_strength(new_password)
    if strength_error:
        flash(f"رمز عبور جدید آسان است: {strength_error}")
        return redirect(url_for("profile"))

    users = load_data(USERS_FILE)
    target_user = next((u for u in users if normalize_username(u.get("username")) == target_username), None)

    if not target_user:
        flash("کاربر مورد نظر یافت نشد.")
        return redirect(url_for("profile"))

    target_user["password"] = hash_password(new_password)
    target_user["updated_at"] = datetime.now().isoformat()
    save_data(USERS_FILE, users)

    print(farsi(f"رمز عبور کاربر {target_username} توسط ادمین تغییر داده شد."))
    flash(f"رمز عبور کاربر {target_username} با موفقیت به‌روزرسانی شد.")
    return redirect(url_for("profile"))


# ---------- خروج ----------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- اجرای سرور ----------

if __name__ == "__main__":
    app.run(debug=True, port=5000)