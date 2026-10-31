import sqlite3

conn = sqlite3.connect("database.db")  # مسیر فایل دیتابیس پروژه‌ات
cursor = conn.cursor()

# اضافه کردن ستون ایمیل بدون پاک شدن کاربران قبلی
try:
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT;")
    conn.commit()
    print("ستون ایمیل با موفقیت اضافه شد.")
except sqlite3.OperationalError:
    print("ستون ایمیل از قبل وجود دارد.")
finally:
    conn.close()
