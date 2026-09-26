"""Admin endpoints."""
import sqlite3

from fastapi import APIRouter, Depends

from app.auth import admin_required
from app.db import audit, get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/merchants")
def list_merchants(admin: str = Depends(admin_required),
                   conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    rows = conn.execute("SELECT id, name, email FROM merchants ORDER BY id").fetchall()
    audit(conn, actor=f"admin:{admin}", action="merchant.list", resource="merchants")
    return [dict(r) for r in rows]
