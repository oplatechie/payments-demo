"""Merchant refunds API: refund all or part of a captured payment."""
import logging
import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import merchant_auth
from app.db import get_db

log = logging.getLogger("payments.refunds")
router = APIRouter(prefix="/refunds", tags=["refunds"])


class RefundIn(BaseModel):
    payment_id: str = Field(pattern=r"^pay_[0-9a-f]{12}$")
    amount: int = Field(gt=0, le=10_000_000)


class RefundOut(BaseModel):
    id: str
    payment_id: str
    amount: int
    status: str
    card_last4: str


def _out(row: sqlite3.Row) -> RefundOut:
    return RefundOut(id=row["id"], payment_id=row["payment_id"], amount=row["amount"],
                     status=row["status"], card_last4=row["card_last4"])


@router.post("", status_code=201)
def create_refund(body: RefundIn, merchant: dict = Depends(merchant_auth),
                  conn: sqlite3.Connection = Depends(get_db)) -> RefundOut:
    payment = conn.execute("SELECT * FROM payments WHERE id = ? AND merchant_id = ?",
                           (body.payment_id, merchant["id"])).fetchone()
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    refunded = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM refunds WHERE payment_id = ?",
                            (body.payment_id,)).fetchone()[0]
    if refunded + body.amount > payment["amount"]:
        raise HTTPException(status_code=422, detail="refund exceeds captured amount")
    refund_id = "ref_" + secrets.token_hex(6)
    conn.execute(
        "INSERT INTO refunds (id, payment_id, merchant_id, amount, card_last4, status) "
        "VALUES (?, ?, ?, ?, ?, 'refunded')",
        (refund_id, body.payment_id, merchant["id"], body.amount, payment["card_last4"]))
    log.info("refund created id=%s payment=%s merchant=%s", refund_id, body.payment_id, merchant["id"])
    row = conn.execute("SELECT * FROM refunds WHERE id = ?", (refund_id,)).fetchone()
    return _out(row)


@router.get("/{refund_id}")
def get_refund(refund_id: str, merchant: dict = Depends(merchant_auth),
               conn: sqlite3.Connection = Depends(get_db)) -> RefundOut:
    row = conn.execute("SELECT * FROM refunds WHERE id = ? AND merchant_id = ?",
                       (refund_id, merchant["id"])).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="refund not found")
    return _out(row)
