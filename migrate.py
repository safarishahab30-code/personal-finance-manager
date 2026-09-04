import json
import os
from datetime import datetime
from data.database import get_connection

def farsi(text):
    return text

def migrate():
    conn = get_connection()
    cursor = conn.cursor()

    # ۱. انتقال کاربران
    users_file = os.path.join("data", "users.json")
    if os.path.exists(users_file):
        with open(users_file, "r", encoding="utf-8") as f:
            try:
                users = json.load(f)
                for u in users:
                    now = datetime.now().isoformat(timespec="seconds")
                    cursor.execute("""
                        INSERT OR IGNORE INTO users (username, password_hash, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (u["username"], u["password"], u.get("created_at", now), u.get("updated_at", now)))
                print(farsi("انتقال کاربران انجام شد."))
            except Exception as e:
                print(farsi(f"خطا در خواندن کاربران: {e}"))

    # ۲. انتقال تراکنش‌ها
    tx_file = os.path.join("data", "transactions.json")
    if os.path.exists(tx_file):
        with open(tx_file, "r", encoding="utf-8") as f:
            try:
                transactions = json.load(f)
                for t in transactions:
                    # پیدا کردن id کاربر بر اساس نام کاربری
                    cursor.execute("SELECT id FROM users WHERE username = ?", (t.get("username", ""),))
                    user_row = cursor.fetchone()
                    if user_row:
                        user_id = user_row["id"]
                        now = datetime.now().strftime("%Y-%m-%d")
                        cursor.execute("""
                            INSERT INTO transactions (user_id, title, amount, type, category, date, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user_id,
                            t.get("title", t.get("description", "بدون عنوان")),
                            float(t.get("amount", 0)),
                            t.get("type", "expense"),
                            t.get("category", "عمومی"),
                            t.get("date", now),
                            t.get("created_at", datetime.now().isoformat(timespec="seconds"))
                        ))
                print(farsi("انتقال تراکنش‌ها انجام شد."))
            except Exception as e:
                print(farsi(f"خطا در خواندن تراکنش‌ها: {e}"))

    conn.commit()
    conn.close()
    print(farsi("عملیات مهاجرت داده‌ها کامل شد."))

if __name__ == "__main__":
    migrate()