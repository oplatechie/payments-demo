"""Shared pytest fixtures for unit tests (tests/) and control tests (controls/tests/)."""
import secrets
import sqlite3

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PAYMENTS_DB", str(tmp_path / "test.db"))
    return tmp_path


@pytest.fixture
def client(app_env):
    from app.main import create_app
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def conn(client):
    from app.db import connect
    c = connect()
    yield c
    c.commit()
    c.close()


@pytest.fixture
def merchants(conn):
    """Two merchants. Each entry: {"id", "headers"}."""
    from app.db import create_merchant
    out = {}
    for name in ("alpha", "beta"):
        merchant_id, token = create_merchant(conn, name, f"{name}@example.com")
        out[name] = {"id": merchant_id, "headers": {"Authorization": f"Bearer {token}"}}
    conn.commit()
    return out


@pytest.fixture
def merchant_token(merchants):
    """Auth headers for merchant 'alpha'."""
    return merchants["alpha"]["headers"]


@pytest.fixture
def admin_user(conn):
    """An admin account. Returns {"username", "password", "email"}."""
    from app.db import create_admin
    user = {"username": "admin", "password": secrets.token_urlsafe(12), "email": "admin@example.com"}
    create_admin(conn, user["username"], user["password"], user["email"])
    conn.commit()
    return user


@pytest.fixture
def captured_emails():
    """Emails sent during the test, as a list of {"to", "body"}."""
    from app import notify
    notify.OUTBOX.clear()
    yield notify.OUTBOX
    notify.OUTBOX.clear()


class DbView:
    def __init__(self, path):
        self.path = path

    def all_values(self):
        """Yield (table, column, value) for every stored value in every table."""
        c = sqlite3.connect(self.path)
        try:
            tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            for table in tables:
                cur = c.execute(f'SELECT * FROM "{table}"')
                cols = [d[0] for d in cur.description]
                for row in cur.fetchall():
                    for col, val in zip(cols, row):
                        yield table, col, val
        finally:
            c.close()

    def rows(self, sql, params=()):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in c.execute(sql, params).fetchall()]
        finally:
            c.close()


@pytest.fixture
def db(client):
    from app.db import db_path
    return DbView(db_path())
