import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "users.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            email            TEXT    UNIQUE NOT NULL,
            password_hash    TEXT    NOT NULL,
            tries_remaining  INTEGER NOT NULL DEFAULT 3,
            country          TEXT    NOT NULL DEFAULT '',
            phone            TEXT    NOT NULL DEFAULT '',
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Add columns if upgrading from older schema
    for col, definition in [("country", "TEXT NOT NULL DEFAULT ''"), ("phone", "TEXT NOT NULL DEFAULT ''")]:
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
        except Exception:
            pass
    conn.commit()
    conn.close()
