import sqlite3
from pathlib import Path

def farsi(text):
    return str(text)

class Database:
    def __init__(self, db_path="data/finance.db"):
        self.db_path = db_path
        self._ensure_database_directory()
        self.init_db()

    def _ensure_database_directory(self):
        """اطمینان از وجود پوشه دیتابیس"""
        database_path = Path(self.db_path)
        database_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        """ایجاد اتصال جدید به دیتابیس"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """ایجاد جدول‌های اصلی در صورت نبودن آن‌ها"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # جدول کاربران
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    security_question TEXT,
                    security_answer_hash TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # جدول تراکنش‌ها
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    note TEXT,
                    account TEXT,
                    date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id)
                        REFERENCES users (id)
                        ON DELETE CASCADE
                )
                """
            )

            # جدول مدیریت بودجه
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    limit_amount REAL NOT NULL,
                    month TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id)
                        REFERENCES users (id)
                        ON DELETE CASCADE,
                    UNIQUE(user_id, category, month)
                )
                """
            )

            conn.commit()

    def get_user_by_username(self, username):
        """دریافت کاربر بر اساس نام کاربری"""
        with self.get_connection() as conn:
            return conn.execute(
                """
                SELECT *
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()

    def get_user_by_id(self, user_id):
        """دریافت کاربر بر اساس شناسه"""
        with self.get_connection() as conn:
            return conn.execute(
                """
                SELECT *
                FROM users
                WHERE id = ?
                """,
                (user_id,)
            ).fetchone()

    def create_user(self, username, password_hash, role="user"):
        """ایجاد کاربر جدید"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users (
                        username,
                        password_hash,
                        role
                    )
                    VALUES (?, ?, ?)
                    """,
                    (username, password_hash, role)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_username(self, user_id, new_username, updated_at):
        """تغییر نام کاربری"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    UPDATE users
                    SET username = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (new_username, updated_at, user_id)
                )
                conn.commit()
            return cursor.rowcount == 1
        except sqlite3.IntegrityError:
            return False

    def update_password(self, user_id, new_password_hash, updated_at):
        """تغییر رمز عبور"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE users
                SET password_hash = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (new_password_hash, updated_at, user_id)
            )
            conn.commit()
        return cursor.rowcount == 1

    def add_transaction(
        self,
        user_id,
        title,
        amount,
        category,
        transaction_type,
        date
    ):
        """ثبت تراکنش جدید"""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    type,
                    amount,
                    category,
                    note,
                    date
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    transaction_type,
                    amount,
                    category,
                    title,
                    date
                )
            )
            conn.commit()

    def get_transactions_by_user(self, user_id):
        """دریافت تراکنش‌های متعلق به یک کاربر"""
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    user_id,
                    type,
                    amount,
                    category,
                    note,
                    account,
                    date
                FROM transactions
                WHERE user_id = ?
                ORDER BY date DESC, id DESC
                """,
                (user_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_transaction(self, transaction_id, user_id):
        """حذف تراکنش فقط توسط مالک آن"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM transactions
                WHERE id = ?
                  AND user_id = ?
                """,
                (transaction_id, user_id)
            )
            conn.commit()
        return cursor.rowcount == 1

    def set_budget(self, user_id, category, limit_amount, month):
        """ثبت یا ویرایش بودجه برای یک دسته‌بندی در یک ماه"""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO budgets (user_id, category, limit_amount, month)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, category, month)
                DO UPDATE SET limit_amount = excluded.limit_amount
                """,
                (user_id, category, limit_amount, month)
            )
            conn.commit()

    def get_budgets_by_user(self, user_id, month):
        """دریافت تمام بودجه‌های کاربر برای ماه مشخص"""
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM budgets
                WHERE user_id = ? AND month = ?
                """,
                (user_id, month)
            ).fetchall()
        return [dict(row) for row in rows]

db = Database()