import hashlib
import hmac
import json
import os
import random
import re
import secrets
import string
from datetime import datetime
from utils import farsi


USERS_FILE = "data/users.json"
TRANSACTIONS_FILES = (
    "data/transactions.json",
    "transactions.json",
)

PBKDF2_ITERATIONS = 100_000

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")

FA_DIGITS = str.maketrans(
    "0123456789",
    "۰۱۲۳۴۵۶۷۸۹",
)

EN_DIGITS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)

WORDS = [
    "Blue",
    "Tiger",
    "Lotus",
    "Falcon",
    "Sunset",
    "Cobalt",
    "Nova",
    "Orchid",
    "Silver",
    "Emerald",
    "Comet",
    "Dawn",
    "Violet",
    "Zenith",
    "Maple",
    "River",
    "Harbor",
    "Meadow",
    "Crystal",
    "Thunder",
]

SYMBOLS = "!@#$%&*?"

from werkzeug.security import generate_password_hash

def admin_reset_password(username, new_password):
    # فرض بر این است که لیستی از کاربران را از users.json می‌خوانی
    users = load_users() 
    if username in users:
        # رمز جدید هش شده و جایگزین می‌شود
        users[username]['password'] = generate_password_hash(new_password)
        save_users(users)
        return True
    return False

def normalize_choice(value):
    return str(value).translate(EN_DIGITS).strip()


def fa_num(value):
    return str(value).translate(FA_DIGITS)


def load_users():
    if not os.path.exists(USERS_FILE):
        return []

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            users = json.load(file)

        if isinstance(users, list):
            return users

        return []
    except (OSError, json.JSONDecodeError):
        return []


def save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


def hash_password(password):
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    salt = os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return f"{salt.hex()}${digest.hex()}"


def verify_password(plain_password, stored_password):
    if not isinstance(plain_password, str):
        return False

    if not isinstance(stored_password, str):
        return False

    if "$" not in stored_password:
        return hmac.compare_digest(plain_password, stored_password)

    try:
        salt_hex, stored_hash = stored_password.split("$", 1)

        if not salt_hex or not stored_hash:
            return False

        salt = bytes.fromhex(salt_hex)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
        ).hex()

        return hmac.compare_digest(calculated_hash, stored_hash)
    except (ValueError, TypeError):
        return False


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

    if re.search(r"[@$!%*#?&^]", password):
        score += 1

    return score


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


def check_password_strength(password):
    if len(password) < 8:
        return "حداقل طول رمز باید ۸ کاراکتر باشد."
    if not any(c.isupper() for c in password):
        return "باید حداقل یک حرف بزرگ انگلیسی داشته باشد."
    if not any(c.islower() for c in password):
        return "باید حداقل یک حرف کوچک انگلیسی داشته باشد."
    if not any(c.isdigit() for c in password):
        return "باید حداقل یک عدد داشته باشد."
    return None

def generate_strong_password(length=12):
    if length < 8:
        length = 8

    required_characters = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(SYMBOLS),
    ]

    all_characters = string.ascii_letters + string.digits + SYMBOLS

    remaining_characters = [
        secrets.choice(all_characters)
        for _ in range(length - len(required_characters))
    ]

    password_characters = required_characters + remaining_characters
    secrets.SystemRandom().shuffle(password_characters)

    return "".join(password_characters)


def generate_password_suggestions(count=3):
    return [generate_strong_password() for _ in range(count)]


def register():
    users = load_users()

    username = input(farsi("نام کاربری: ")).strip()
    password = input(farsi("رمز عبور: "))

    if not username or not password:
        print(farsi("نام کاربری و رمز عبور نمی‌توانند خالی باشند."))
        return None

    if not USERNAME_RE.fullmatch(username):
        print(
            farsi(
                "نام کاربری باید بین ۳ تا ۲۰ کاراکتر و شامل حروف انگلیسی، عدد یا _ باشد."
            )
        )
        return None

    if any(user.get("username") == username for user in users):
        print(farsi("این نام کاربری قبلاً ثبت شده است."))
        return None

    is_strong, reason = check_password_strength(password)

    if not is_strong:
        print(farsi(f"رمز عبور آسان است: {reason}"))
        return None

    role = "admin" if not users else "user"
    now = datetime.now().isoformat()

    new_user = {
        "username": username,
        "password": hash_password(password),
        "role": role,
        "created_at": now,
        "updated_at": now,
    }

    users.append(new_user)
    save_users(users)

    print(farsi("ثبت‌نام با موفقیت انجام شد."))
    print(farsi(f"نقش شما: {role}"))

    return new_user


def login():
    username = input(farsi("نام کاربری: ")).strip()
    password = input(farsi("رمز عبور: "))

    users = load_users()

    for user in users:
        if user.get("username") != username:
            continue

        stored_password = user.get("password", "")

        if not verify_password(password, stored_password):
            print(farsi("نام کاربری یا رمز عبور اشتباه است."))
            return None

        if "$" not in stored_password:
            user["password"] = hash_password(password)
            user["updated_at"] = datetime.now().isoformat()
            save_users(users)

        print(farsi("ورود با موفقیت انجام شد."))
        return user

    print(farsi("نام کاربری یا رمز عبور اشتباه است."))
    return None


def suggest_username(base_name, existing_users):
    existing_names = {
        user.get("username")
        for user in existing_users
        if user.get("username")
    }

    while True:
        candidate = f"{base_name}_{random.randint(100, 999)}"

        if candidate not in existing_names:
            return candidate


def suggest_usernames(base_name, existing_users, count=3):
    existing_names = {
        user.get("username")
        for user in existing_users
        if user.get("username")
    }

    suggestions = []

    while len(suggestions) < count:
        candidate = f"{base_name}_{random.randint(100, 999)}"

        if candidate not in existing_names and candidate not in suggestions:
            suggestions.append(candidate)

    return suggestions


def update_transactions_username(old_username, new_username):
    for path in TRANSACTIONS_FILES:
        if not os.path.exists(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as file:
                transactions = json.load(file)

            if not isinstance(transactions, list):
                continue

            changed = False

            for transaction in transactions:
                if transaction.get("username") == old_username:
                    transaction["username"] = new_username
                    changed = True

            if changed:
                with open(path, "w", encoding="utf-8") as file:
                    json.dump(
                        transactions,
                        file,
                        ensure_ascii=False,
                        indent=4,
                    )

        except (OSError, json.JSONDecodeError):
            continue


def change_username(
    current_user,
    all_users=None,
    all_transactions=None,
):
    users = all_users if isinstance(all_users, list) else load_users()

    print(farsi("\n--- تغییر نام کاربری ---"))

    old_username = current_user.get("username", "")

    while True:
        new_username = input(
            farsi(
                "نام کاربری جدید را وارد کنید "
                "(۳ تا ۲۰ کاراکتر، حروف انگلیسی، عدد یا _): "
            )
        ).strip()

        if not new_username:
            print(farsi("نام کاربری نمی‌تواند خالی باشد."))
            continue

        if new_username == old_username:
            print(farsi("نام جدید با نام کاربری فعلی یکسان است."))
            continue

        if not USERNAME_RE.fullmatch(new_username):
            print(
                farsi(
                    "فرمت نام کاربری نامعتبر است. "
                    "فقط حروف انگلیسی، عدد و _ مجاز است."
                )
            )
            continue

        username_exists = any(
            user.get("username") == new_username
            and user.get("username") != old_username
            for user in users
        )

        if username_exists:
            suggestions = suggest_usernames(
                new_username,
                users,
                count=3,
            )

            print(farsi("این نام کاربری قبلاً ثبت شده است."))
            print(farsi("نام‌های پیشنهادی:"))

            for index, suggestion in enumerate(suggestions, start=1):
                print(farsi(f"{index}) {suggestion}"))

            print(farsi("۰) وارد کردن نام دیگر"))

            choice = normalize_choice(
                input(farsi("انتخاب: "))
            )

            if choice in ("1", "2", "3"):
                new_username = suggestions[int(choice) - 1]
            else:
                continue

        confirmation = normalize_choice(
            input(
                farsi(
                    f"تغییر نام کاربری از «{old_username}» "
                    f"به «{new_username}» تأیید شود؟ "
                    "(۱=بله، ۲=خیر): "
                )
            )
        )

        if confirmation != "1":
            print(farsi("عملیات لغو شد."))
            return False

        break

    user_found = False

    for user in users:
        if user.get("username") == old_username:
            user["username"] = new_username
            user["updated_at"] = datetime.now().isoformat()
            user_found = True
            break

    if not user_found:
        print(farsi("کاربر در فایل کاربران پیدا نشد."))
        return False

    current_user["username"] = new_username
    current_user["updated_at"] = datetime.now().isoformat()

    if isinstance(all_transactions, list):
        for transaction in all_transactions:
            if transaction.get("username") == old_username:
                transaction["username"] = new_username

    save_users(users)
    update_transactions_username(old_username, new_username)

    print(farsi("نام کاربری با موفقیت تغییر کرد."))

    return True

def generate_temporary_password(length=10):
    # ترکیب حروف بزرگ، کوچک، اعداد و علامت‌ها
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))

def change_password(current_user):
    print(farsi("\n--- تغییر رمز عبور ---"))

    old_password = input(
        farsi("رمز عبور فعلی را وارد کنید: ")
    )

    stored_password = current_user.get("password", "")

    if not verify_password(old_password, stored_password):
        print(farsi("رمز عبور فعلی اشتباه است."))
        return False

    while True:
        new_password = input(
            farsi(
                "رمز عبور جدید را وارد کنید "
                "یا برای دریافت پیشنهاد، حرف p را وارد کنید: "
            )
        )

        if new_password.lower() == "p":
            suggestions = generate_password_suggestions(3)

            print(farsi("رمزهای پیشنهادی:"))

            for index, suggestion in enumerate(suggestions, start=1):
                print(farsi(f"{index}) {suggestion}"))

            choice = normalize_choice(
                input(
                    farsi(
                        "شماره رمز را انتخاب کنید "
                        "یا ۰ را برای بازگشت وارد کنید: "
                    )
                )
            )

            if choice in ("1", "2", "3"):
                new_password = suggestions[int(choice) - 1]
                print(farsi(f"رمز انتخاب‌شده: {new_password}"))
            else:
                continue

        if new_password == old_password:
            print(
                farsi(
                    "رمز عبور جدید نباید با رمز فعلی یکسان باشد."
                )
            )
            continue

        is_strong, reason = check_password_strength(new_password)

        if not is_strong:
            print(farsi(f"این رمز آسان است: {reason}"))
            print(
                farsi(
                    "رمز را اصلاح کنید یا برای دریافت پیشنهاد، "
                    "حرف p را وارد کنید."
                )
            )
            continue

        repeated_password = input(
            farsi("رمز عبور جدید را دوباره وارد کنید: ")
        )

        if new_password != repeated_password:
            print(farsi("تکرار رمز عبور مطابقت ندارد."))
            continue

        confirmation = normalize_choice(
            input(
                farsi(
                    "تغییر رمز عبور تأیید شود؟ "
                    "(۱=بله، ۲=خیر): "
                )
            )
        )

        if confirmation != "1":
            print(farsi("عملیات لغو شد."))
            return False

        break

    users = load_users()
    username = current_user.get("username")
    new_password_hash = hash_password(new_password)
    updated_at = datetime.now().isoformat()
    user_found = False

    for user in users:
        if user.get("username") == username:
            user["password"] = new_password_hash
            user["updated_at"] = updated_at
            user_found = True
            break

    if not user_found:
        print(farsi("کاربر در فایل کاربران پیدا نشد."))
        return False

    current_user["password"] = new_password_hash
    current_user["updated_at"] = updated_at

    save_users(users)

    print(farsi("رمز عبور با موفقیت تغییر کرد."))

    return True
