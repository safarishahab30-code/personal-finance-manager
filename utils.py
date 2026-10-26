import arabic_reshaper
from bidi.algorithm import get_display
def farsi(text):
    return text

def format_money(amount):
    """فرمت ۳ رقم ۳ رقم مبالغ به همراه تومان"""
    try:
        return f"{int(amount):,} تومان"
    except (ValueError, TypeError):
        return f"{amount} تومان"


def parse_farsi_number(text):
    """تبدیل تمام ارقام فارسی به انگلیسی"""
    if not isinstance(text, str):
        text = str(text)
    return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).strip()
def format_money(amount):
    try:
        return f"{int(amount):,} تومان"
    except (ValueError, TypeError):
        return f"{amount} تومان"
def parse_farsi_number(text):
    if not isinstance(text, str):
        text = str(text)
    return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).strip()
DEFAULT_ACCOUNTS = ["کارت اصلی", "کارت پس‌انداز", "کیف پول نقدی"]

def format_money(amount):
    try:
        return f"{int(amount):,} تومان"
    except (ValueError, TypeError):
        return f"{amount} تومان"
def parse_farsi_number(text):
    if not isinstance(text, str):
        text = str(text)
    return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).strip()
