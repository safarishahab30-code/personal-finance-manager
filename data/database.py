import sqlite3
from datetime import datetime

def farsi(text):
    return text

DB_NAME = "finance.db"

def get_connection():
    """ایجاد اتصال به دیتابیس با خروجی به شکل دیکشنری و فعال‌سازی کلید خارجی"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """ایجاد خودکار جداول کاربران، تراکنش‌ها و بودجه‌ها در صورت عدم وجود"""
    conn = get_connection()
    cursor = conn.cursor()

    # جدول کاربران
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)

    # جدول تراکنش‌ها
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # جدول بودجه‌بندی (Budget Management)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            limit_amount REAL NOT NULL,
            month TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id, category, month)
        );
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(farsi("دیتابیس و جداول با موفقیت ساخته شدند."))