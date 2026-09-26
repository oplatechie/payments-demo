"""Merchant payments API."""
import logging
import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import merchant_auth
from app.db import audit, get_db
from app.vault import tokenize

log = logging.getLogger("payments.api")
router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentIn(BaseModel):
    card_number: str = Field(pattern=r"^\d{13,19}$")
    amount: int = Field(gt=0, le=10_000_000)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")


class PaymentOut(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    card_last4: str


def _out(row: sqlite3.Row) -> PaymentOut:
    return PaymentOut(id=row["id"], amount=row["amount"], currency=row["currency"],
                      status=row["status"], card_last4=row["card_last4"])


@router.post("", status_code=201)
def create_payment(body: PaymentIn, merchant: dict = Depends(merchant_auth),
                   conn: sqlite3.Connection = Depends(get_db)) -> PaymentOut:
    payment_id = "pay_" + secrets.token_hex(6)
    conn.execute(
        "INSERT INTO payments (id, merchant_id, card_token, card_last4, amount, currency, status) "
        "VALUES (?, ?, ?, ?, ?, ?, 'captured')",
        (payment_id, merchant["id"], tokenize(body.card_number), body.card_number[-4:],
         body.amount, body.currency))
    log.info("payment created id=%s merchant=%s", payment_id, merchant["id"])
    row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
    return _out(row)


@router.get("/{payment_id}")
def get_payment(payment_id: str, merchant: dict = Depends(merchant_auth),
                conn: sqlite3.Connection = Depends(get_db)) -> PaymentOut:
    row = conn.execute("SELECT * FROM payments WHERE id = ? AND merchant_id = ?",
                       (payment_id, merchant["id"])).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="payment not found")
    audit(conn, actor=merchant["id"], action="payment.read", resource=f"payment:{payment_id}")
    return _out(row)


@router.get("")
def list_payments(merchant: dict = Depends(merchant_auth),
                  conn: sqlite3.Connection = Depends(get_db)) -> list[PaymentOut]:
    rows = conn.execute("SELECT * FROM payments WHERE merchant_id = ? ORDER BY created_at",
                        (merchant["id"],)).fetchall()
    audit(conn, actor=merchant["id"], action="payment.list", resource="payments")
    return [_out(r) for r in rows]
