import sqlite3
import glob

db_files = glob.glob("**/*.db", recursive=True)
print("Found databases:", db_files)

for db_path in db_files:
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='budgets'"
        )

        if cur.fetchone() is None:
            print(f"\n{db_path}: جدول budgets وجود ندارد؛ رد شد.")
            continue

        cur.execute("PRAGMA table_info(budgets)")
        columns = {row[1] for row in cur.fetchall()}

        for column in ("created_at", "updated_at"):
            if column not in columns:
                conn.execute(
                    f"ALTER TABLE budgets ADD COLUMN {column} DATETIME"
                )
                print(f"{db_path}: ستون {column} اضافه شد.")
            else:
                print(f"{db_path}: ستون {column} از قبل وجود دارد.")

        conn.commit()
