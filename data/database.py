import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="data/finance.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """ایجاد یک اتصال جدید به دیتابیس"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # اجازه می‌دهد نتایج مثل دیکشنری دسترسی داشته باشند
        return conn

    def init_db(self):
        """ایجاد جداول اصلی در صورت عدم وجود"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # ۱. جدول کاربران
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ۲. جدول تراکنش‌ها (با ارتباط با جدول کاربران)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    note TEXT,
                    account TEXT,
                    date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()

# ایجاد یک نمونه واحد از دیتابیس برای استفاده در کل پروژه
db = Database()