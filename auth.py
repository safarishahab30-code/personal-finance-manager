import json
import os
import re
import hashlib
from datetime import datetime
import secrets
import string
from utils import farsi
import random

USERS_FILE = "data/users.json"

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

def normalize_choice(s):
    return s.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).strip()

def fa_num(s):
    return str(s).translate(FA_DIGITS)

def strength_label(score):
    if score <= 1:
        return "خیلی ضعیف"
    if score == 2:
        return "ضعیف"
    if score == 3:
        return "متوسط"
    if score == 4:
        return "قوی"
    return "خیلی قوی"

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    os.makedirs("data", exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)

def password_strength(password):
    score = 0
    if len(password) >= 8:
        score += 1
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"\d", password):
        score += 1
    if re.search(r"[@$!%*#?&]", password):
        score += 1
    return score

def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + "$" + digest.hex()

def verify_password(plain, stored):
    if "$" in stored:
        salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", plain.encode(), bytes.fromhex(salt_hex), 100_000)
        return digest.hex() == hash_hex
    return stored == plain

def update_transactions_username(old_username, new_username):
    for path in ("data/transactions.json", "transactions.json"):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for t in data:
                    if t.get("username") == old_username:
                        t["username"] = new_username
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return
        except (OSError, json.JSONDecodeError):
            continue

def register():
    users = load_users()
    username = input(farsi("نام کاربری: ")).strip()
    password = input(farsi("رمز عبور: "))

    if not username or not password:
        print(farsi("نام کاربری و رمز عبور نمی‌تواند خالی باشد."))
        return

    if any(u["username"] == username for u in users):
        print(farsi("این نام کاربری قبلاً ثبت شده است."))
        return

    role = "admin" if len(users) == 0 else "user"

    new_user = {
        "username": username,
        "password": hash_password(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
    }

    users.append(new_user)
    save_users(users)
    print(farsi("ثبت‌نام با موفقیت انجام شد."))
    print(farsi("نقش شما: ") + role)

def login():
    username = input(farsi(": نام کاربری")).strip()
    password = input(farsi(": رمز عبور"))

    users = load_users()
    for user in users:
        if user["username"] == username:
            if verify_password(password, user.get("password", "")):
                # ارتقای خودکار رمز قدیمیِ متن‌ساده به هش
                if "$" not in user.get("password", ""):
                    user["password"] = hash_password(password)
                    user["updated_at"] = datetime.now().isoformat()
                    save_users(users)
                return user
            print(farsi("نام کاربری یا رمز عبور اشتباه است."))
            return None

    print(farsi("نام کاربری یا رمز عبور اشتباه است."))
    return None

def suggest_usernames(base, users, count=3):
    taken = {u["username"] for u in users}
    styles = ["_", "", "."]
    out = []
    n = 1
    while len(out) < count:
        cand = f"{base}{styles[len(out) % len(styles)]}{n}"
        if cand not in taken:
            out.append(cand)
            taken.add(cand)
        n += 1
    return out

WORDS = ["Blue", "Tiger", "Lotus", "Falcon", "Sunset", "Cobalt", "Nova",
         "Orchid", "Silver", "Emerald", "Comet", "Dawn", "Violet",
         "Zenith", "Maple", "River", "Harbor", "Meadow", "Crystal", "Thunder"]

SYMBOLS = "!@#$%&*?"

def generate_password_suggestions(count=3):
    out = []
    for _ in range(count):
        style = secrets.randbelow(3)
        if style == 0:
            pw = f"{secrets.choice(WORDS)}{secrets.choice(SYMBOLS)}{secrets.randbelow(900) + 100}"
        elif style == 1:
            pw = f"{secrets.choice(WORDS)}_{secrets.choice(WORDS)}{secrets.choice(SYMBOLS)}{secrets.randbelow(90) + 10}"
        else:
            pw = f"{secrets.choice(WORDS)}{secrets.randbelow(90) + 10}{secrets.choice(SYMBOLS)}{secrets.choice(WORDS)}"
        out.append(pw)
    return out

def change_username(current_user):
    users = load_users()

    while True:
        print(farsi("نام کاربری جدید (فقط حروف انگلیسی، عدد و _ ؛ ۳ تا ۲۰ کاراکتر):"))
        new_username = input("> ").strip()

        if not new_username:
            print(farsi("نام کاربری نمی‌تواند خالی باشد."))
            continue

        if not USERNAME_RE.match(new_username):
            print(farsi("فرمت نامعتبر است. فقط حروف انگلیسی، عدد و _ مجاز است."))
            continue

        if any(u["username"] == new_username for u in users):
            print(farsi("این نام گرفته شده است. پیشنهادهای نزدیک:"))
            suggestions = suggest_usernames(new_username, users)
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}) {s}")
            print(farsi("0) نوشتن نام دیگر"))
            choice = normalize_choice(input(farsi("انتخاب: ")))
            if choice in ("1", "2", "3"):
                new_username = suggestions[int(choice) - 1]
                break
            continue

        break

    print(farsi("نام جدید:"))
    print(f"  {new_username}")
    if normalize_choice(input(farsi("تأیید می‌کنید؟ (1=بله، 2=خیر): "))) != "1":
        print(farsi("انصراف دادید."))
        return

    old_username = current_user["username"]
    for user in users:
        if user["username"] == old_username:
            user["username"] = new_username
            user["updated_at"] = datetime.now().isoformat()
            break

    save_users(users)
    current_user["username"] = new_username
    update_transactions_username(old_username, new_username)
    print(farsi("نام کاربری با موفقیت تغییر کرد."))
    print(f"  {old_username}  ←  {new_username}")

def change_password(current_user):
    print(farsi("\n--- تغییر رمز عبور ---"))
    old_pass = input(farsi("رمز عبور فعلی خود را وارد کنید: "))

    # بررسی صحت رمز فعلی با متد اعتبارسنجی هش
    if not verify_password(old_pass, current_user.get("password", "")):
        print(farsi("رمز عبور فعلی اشتباه است."))
        return False

    while True:
        new_pass = input(
            farsi("رمز عبور جدید را وارد کنید (یا 'p' برای رمز پیشنهادی): ")
        )
        if new_pass.lower() == "p":
            suggested = generate_strong_password()
            print(farsi(f"رمز پیشنهادی: {suggested}"))
            confirm = input(
                farsi("آیا از این رمز استفاده شود؟ (y/n): ")
            ).lower()
            if confirm == "y":
                new_pass = suggested
            else:
                continue

        is_strong, reason = check_password_strength(new_pass)
        if not is_strong:
            print(
                farsi(
                    "رمز ضعیف است. باید حداقل ۶ کاراکتر و شامل حروف و ارقام باشد."
                )
            )
            continue

        confirm_pass = input(farsi("تکرار رمز عبور جدید: "))
        if new_pass != confirm_pass:
            print(farsi("تکرار رمز مطابقت ندارد."))
            continue

        # هش کردن رمز جدید و ثبت زمان
        current_user["password"] = hash_password(new_pass)
        current_user["updated_at"] = datetime.now().isoformat()
        print(farsi("رمز عبور با موفقیت تغییر یافت."))
        return True
def check_password_strength(password):
    if len(password) < 6:
        return False, "weak_length"
    has_digit = any(c.isdigit() for c in password)
    has_alpha = any(c.isalpha() for c in password)
    if not (has_digit and has_alpha):
        return False, "weak_complexity"
    return True, "strong"
def generate_strong_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(chars) for _ in range(length))

def change_password(current_user):
    print(farsi("\n--- تغییر رمز عبور ---"))
    old_pass = input(farsi("رمز عبور فعلی خود را وارد کنید: "))
    
    # اعتبارسنجی صحیح رمز عبور فعلی با استفاده از verify_password
    if not verify_password(old_pass, current_user.get("password", "")):
        print(farsi("رمز عبور فعلی اشتباه است."))
        return False

    while True:
        new_pass = input(
            farsi("رمز عبور جدید را وارد کنید (یا 'p' برای رمز پیشنهادی): ")
        )
        if new_pass.lower() == "p":
            suggested = generate_strong_password()
            print(farsi(f"رمز پیشنهادی: {suggested}"))
            confirm = input(
                farsi("آیا از این رمز استفاده شود؟ (y/n): ")
            ).lower()
            if confirm == "y":
                new_pass = suggested
            else:
                continue

        is_strong, reason = check_password_strength(new_pass)
        if not is_strong:
            print(
                farsi(
                    "رمز ضعیف است. باید حداقل ۶ کاراکتر و شامل حروف و ارقام باشد."
                )
            )
            continue

        confirm_pass = input(farsi("تکرار رمز عبور جدید: "))
        if new_pass != confirm_pass:
            print(farsi("تکرار رمز مطابقت ندارد."))
            continue

        # ذخیره رمز جدید به صورت هش‌شده و ثبت تاریخ به‌روزرسانی
        current_user["password"] = hash_password(new_pass)
        current_user["updated_at"] = datetime.now().isoformat()
        print(farsi("رمز عبور با موفقیت تغییر یافت."))
        return True


def suggest_username(base_name, existing_users):
    existing_names = {u["username"] for u in existing_users}
    while True:
        candidate = f"{base_name}_{random.randint(100, 999)}"
        if candidate not in existing_names:
            return candidate


def change_username(current_user, all_users, all_transactions):
    print(farsi("\n--- تغییر نام کاربری ---"))
    new_username = input(farsi("نام کاربری جدید را وارد کنید: ")).strip()

    if not new_username:
        print(farsi("نام کاربری نمی‌تواند خالی باشد."))
        return False

    if new_username == current_user["username"]:
        print(farsi("این نام کاربری با نام فعلی شما یکسان است."))
        return False

    existing_names = {
        u["username"] for u in all_users if u["username"] != current_user["username"]
    }
    if new_username in existing_names:
        suggested = suggest_username(new_username, all_users)
        print(farsi(f"این نام کاربری قبلاً ثبت شده است. نام پیشنهادی: {suggested}"))
        choice = input(farsi("آیا مایل به استفاده از نام پیشنهادی هستید؟ (y/n): ")).strip().lower()
        if choice == "y":
            new_username = suggested
        else:
            return False

    confirm = input(farsi(f"آیا از تغییر نام کاربری به '{new_username}' اطمینان دارید؟ (y/n): ")).strip().lower()
    if confirm != "y":
        print(farsi("عملیات لغو شد."))
        return False

    old_username = current_user["username"]
    current_user["username"] = new_username
    current_user["updated_at"] = datetime.now().isoformat()
    # به‌روزرسانی نام کاربری در تراکنش‌های قبلی
    for tx in all_transactions:
        if tx.get("username") == old_username:
            tx["username"] = new_username

    print(farsi("نام کاربری و تراکنش‌های مرتبط با موفقیت به‌روزرسانی شدند."))
    return True
def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password

def hash_password(password):
    return password