"""Request authentication: merchants use API tokens, admins use a session token."""
import sqlite3

from fastapi import Depends, Header, HTTPException

from app.db import get_db, sha256


def merchant_auth(authorization: str = Header(default=""),
                  conn: sqlite3.Connection = Depends(get_db)) -> dict:
    token = authorization.removeprefix("Bearer ").strip()
    row = conn.execute("SELECT id, name FROM merchants WHERE api_token_hash = ?",
                       (sha256(token),)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="invalid merchant token")
    return dict(row)


def admin_required(x_admin_session: str = Header(default=""),
                   conn: sqlite3.Connection = Depends(get_db)) -> str:
    row = conn.execute("SELECT username FROM admin_sessions WHERE token_hash = ?",
                       (sha256(x_admin_session),)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="admin session required")
    return row["username"]
