import sqlite3

conn = sqlite3.connect("data/finance.db")
cursor = conn.cursor()

# 1. بررسی فعال بودن کلیدهای خارجی و خطاهای یکپارچگی
cursor.execute("PRAGMA foreign_key_check;")
fk_errors = cursor.fetchall()

# 2. بررسی ساختار جدول تراکنش‌ها
cursor.execute("PRAGMA table_info(transactions);")
columns = [col[1] for col in cursor.fetchall()]

print("FK Errors:", fk_errors)
print("Transactions Columns:", columns)

conn.close()
