import arabic_reshaper
from bidi.algorithm import get_display

def farsi(text):
    try:
        # معکوس‌سازی مناسب برای نمایش چسبیده در ترمینال ویندوز
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text
