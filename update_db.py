import sqlite3

# مسیر فایل دیتابیس خودت را اینجا بنویس (معمولاً در پوشه instance یا ریشه پروژه است)
conn = sqlite3.connect('finance.db') 
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE budgets ADD COLUMN alert_threshold REAL;")
    conn.commit()
    print("ستون alert_threshold با موفقیت به جدول budgets اضافه شد.")
except Exception as e:
    print(f"خطا یا تکرار ستون: {e}")

conn.close()
