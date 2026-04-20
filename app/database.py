import os

DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    import psycopg2.extras
    IntegrityError = psycopg2.IntegrityError
else:
    import sqlite3
    IntegrityError = sqlite3.IntegrityError


class _Cursor:
    def __init__(self, cur, pg):
        self._cur = cur
        self._pg  = pg

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return dict(row) if self._pg else dict(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [dict(r) for r in rows]


class DB:
    def __init__(self):
        if USE_PG:
            url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            self._conn = psycopg2.connect(url)
            self._conn.autocommit = False
        else:
            self._conn = sqlite3.connect(os.environ.get("DB_PATH", "users.db"))
            self._conn.row_factory = sqlite3.Row

    def execute(self, sql, params=()):
        if USE_PG:
            sql = sql.replace("?", "%s")
            cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = self._conn.cursor()
        cur.execute(sql, params)
        return _Cursor(cur, USE_PG)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def get_db() -> DB:
    return DB()


_CREATE_PG = """
    CREATE TABLE IF NOT EXISTS users (
        id               SERIAL PRIMARY KEY,
        email            TEXT    UNIQUE NOT NULL,
        password_hash    TEXT    NOT NULL,
        tries_remaining  INTEGER NOT NULL DEFAULT 3,
        country          TEXT    NOT NULL DEFAULT '',
        phone            TEXT    NOT NULL DEFAULT '',
        gdpr_consent     BOOLEAN NOT NULL DEFAULT FALSE,
        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

_CREATE_SQ = """
    CREATE TABLE IF NOT EXISTS users (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        email            TEXT    UNIQUE NOT NULL,
        password_hash    TEXT    NOT NULL,
        tries_remaining  INTEGER NOT NULL DEFAULT 3,
        country          TEXT    NOT NULL DEFAULT '',
        phone            TEXT    NOT NULL DEFAULT '',
        gdpr_consent     INTEGER NOT NULL DEFAULT 0,
        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

_EXTRA_COLS = [
    ("country",      "TEXT NOT NULL DEFAULT ''"),
    ("phone",        "TEXT NOT NULL DEFAULT ''"),
    ("gdpr_consent", "INTEGER NOT NULL DEFAULT 0"),
]


def init_db() -> None:
    db = get_db()
    db.execute(_CREATE_PG if USE_PG else _CREATE_SQ)
    for col, defn in _EXTRA_COLS:
        try:
            db.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
        except Exception:
            db.rollback()
    db.commit()
    db.close()
