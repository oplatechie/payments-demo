"""Admin login: password, then a TOTP code from an authenticator app as the second factor."""
import secrets
import sqlite3

import pyotp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_db, sha256, verify_password

router = APIRouter(prefix="/admin/login", tags=["admin-auth"])


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
    return {"second_factor": "totp"}


@router.post("/verify")
def verify_login(body: VerifyIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    admin = conn.execute("SELECT * FROM admins WHERE username = ?", (body.username,)).fetchone()
    if admin is None or not pyotp.TOTP(admin["totp_secret"]).verify(body.code, valid_window=1):
        raise HTTPException(status_code=401, detail="invalid code")
    session = secrets.token_urlsafe(24)
    conn.execute("INSERT INTO admin_sessions (token_hash, username) VALUES (?, ?)",
                 (sha256(session), body.username))
    return {"session": session}
