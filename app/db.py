"""SQLite storage. Path comes from PAYMENTS_DB (tests use a temp file)."""
import hashlib
import os
import secrets
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS merchants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    api_token_hash TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants(id),
    card_token TEXT NOT NULL,
    card_last4 TEXT NOT NULL,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    email TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS login_codes (
    username TEXT PRIMARY KEY,
    code_hash TEXT NOT NULL,
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_sessions (
    token_hash TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def db_path() -> str:
    return os.environ.get("PAYMENTS_DB", "payments.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def get_db():
    """FastAPI dependency: one connection per request, committed at the end."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, _ = stored.split("$", 1)
    return secrets.compare_digest(hash_password(password, salt), stored)


def create_merchant(conn: sqlite3.Connection, name: str, email: str) -> tuple[str, str]:
    """Returns (merchant_id, api_token). Only the token hash is stored."""
    merchant_id = "m_" + secrets.token_hex(4)
    token = secrets.token_urlsafe(24)
    conn.execute("INSERT INTO merchants (id, name, email, api_token_hash) VALUES (?, ?, ?, ?)",
                 (merchant_id, name, email, sha256(token)))
    return merchant_id, token


def create_admin(conn: sqlite3.Connection, username: str, password: str, email: str) -> None:
    conn.execute("INSERT INTO admins (username, password_hash, email) VALUES (?, ?, ?)",
                 (username, hash_password(password), email))


def audit(conn: sqlite3.Connection, actor: str, action: str, resource: str) -> None:
    conn.execute("INSERT INTO audit_log (actor, action, resource) VALUES (?, ?, ?)",
                 (actor, action, resource))
