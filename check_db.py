import sqlite3

for db_name in ["database.db", "finance.db"]:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?,"
        " ?, 1)",
        ("shahab", "dummy_hash"),
    )
    cursor.execute(
        "UPDATE users SET is_admin = 1 WHERE username = ?", ("shahab",)
    )
    conn.commit()
    cursor.execute("SELECT id, username, is_admin FROM users")
    print(f"کاربران در {db_name}:", cursor.fetchall())
    conn.close()
