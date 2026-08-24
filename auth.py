import json
import os
import re
import secrets
import hashlib
from datetime import datetime
from utils import farsi

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
    users = load_users()
    user = next((u for u in users if u["username"] == current_user["username"]), None)

    if user is None:
        print(farsi("کاربر یpassword", ""))
        return

    print(farsi("رمز فعلی را وارد کنید:"))
    old_pass = input("> ")
    if not verify_password(old_pass, user.get("password", "")):
        print(farsi("رمز فعلی اشتباه است."))
        return

    while True:
        print(farsi("رمز جدید (حداقل ۸ کاراکتر؛ ترکیب حروف، عدد و علامت):"))
        new_pass = input("> ")

        if not new_pass:
            print(farsi("رمز نمی‌تواند خالی باشد."))
            continue

        score = password_strength(new_pass)
        print(farsi(f"قدرت رمز: {fa_num(score)} از {fa_num(5)} ({strength_label(score)})"))

        # قدرت کمتر از ۳ → پذیرفته نمی‌شود؛ تا قوی شدن ادامه می‌یابد
        while score < 3:
            print(farsi("رمز ضعیف است (آسان است). رمز دیگری بنویسید یا از پیشنهادها انتخاب کنید:"))
            suggestions = generate_password_suggestions(3)
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}) {s}")
            print(farsi("0) تولید پیشنهادهای جدید"))
            choice = normalize_choice(input(farsi("انتخاب: ")))

            if choice == "0":
                continue  # پیشنهادهای تازه
            elif choice in ("1", "2", "3"):
                new_pass = suggestions[int(choice) - 1]
            else:
                new_pass = choice  # رمز خودش

            score = password_strength(new_pass)
            print(farsi(f"قدرت رمز: {fa_num(score)} از {fa_num(5)} ({strength_label(score)})"))

        # قدرت ۳ یا بیشتر → فقط یک بار تایید بگیر
        print(farsi("تکرار رمز جدید:"))
        if input("> ") != new_pass:
            print(farsi("تکرار رمز مطابقت ندارد. دوباره از اول."))
            continue

        user["password"] = hash_password(new_pass)
        user["updated_at"] = datetime.now().isoformat()
        save_users(users)
        print(farsi("رمز عبور با موفقیت تغییر کرد."))
        break
