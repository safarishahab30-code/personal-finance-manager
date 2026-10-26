DEFAULT_ACCOUNTS = [
    "نقدی",
    "بانک",
    "پس‌انداز"
]
def check_password_strength(password):
    if len(password) < 6:
        return False, "رمز عبور کوتاه است"
    if not any(char.isdigit() for char in password):
        return False, "رمز عبور باید شامل عدد باشد"
    if not any(char.isalpha() for char in password):
        return False, "رمز عبور باید شامل حروف باشد"
    return True, "رمز عبور معتبر است"

def farsi(text):
    return text

def format_money(amount):
    return f"{amount:,}"

def parse_farsi_number(text):
    # تبدیل ارقام فارسی/عربی به انگلیسی و تبدیل به عدد صحیح
    if not text:
        return 0
    persian_nums = '۰۱۲۳۴۵۶۷۸۹'
    english_nums = '0123456789'
    trans = str.maketrans(persian_nums, english_nums)
    cleaned = str(text).translate(trans).replace(',', '').strip()
    return int(cleaned) if cleaned.isdigit() else 0

