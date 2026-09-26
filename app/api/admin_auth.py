"""Admin login: password, then a one-time code as the second factor."""
import secrets
import sqlite3
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_db, sha256, verify_password
from app.notify import send_email

router = APIRouter(prefix="/admin/login", tags=["admin-auth"])
CODE_TTL_SECONDS = 300


class LoginIn(BaseModel):
    username: str
    password: str


class VerifyIn(BaseModel):
    username: str
    code: str


@router.post("")
def start_login(body: LoginIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    admin = conn.execute("SELECT * FROM admins WHERE username = ?", (body.username,)).fetchone()
    if admin is None or not verify_password(body.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")
    code = f"{secrets.randbelow(10**6):06d}"
    conn.execute("INSERT OR REPLACE INTO login_codes (username, code_hash, expires_at) VALUES (?, ?, ?)",
                 (body.username, sha256(code), time.time() + CODE_TTL_SECONDS))
    send_email(admin["email"], f"Your admin login code is {code}")
    return {"second_factor": "email_code"}


@router.post("/verify")
def verify_login(body: VerifyIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    row = conn.execute("SELECT * FROM login_codes WHERE username = ?", (body.username,)).fetchone()
    if row is None or row["expires_at"] < time.time() or row["code_hash"] != sha256(body.code):
        raise HTTPException(status_code=401, detail="invalid code")
    conn.execute("DELETE FROM login_codes WHERE username = ?", (body.username,))
    session = secrets.token_urlsafe(24)
    conn.execute("INSERT INTO admin_sessions (token_hash, username) VALUES (?, ?)",
                 (sha256(session), body.username))
    return {"session": session}
