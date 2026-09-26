"""STD-SDLC-01.a: write endpoints reject malformed input and persist nothing."""

import pytest

from testkit import totp_code


@pytest.mark.parametrize(
    "payload",
    [
        {"card_number": "not-a-card-number", "amount": 100, "currency": "INR"},
        {"card_number": "4111111111111111", "amount": 0, "currency": "INR"},
        {"card_number": "4111111111111111", "amount": 10_000_001, "currency": "INR"},
        {"card_number": ["4111111111111111"], "amount": 100, "currency": "INR"},
        {"card_number": "4111111111111111", "amount": "not-an-int", "currency": "INR"},
        {"card_number": "4111111111111111", "amount": 100, "currency": "usd"},
    ],
)
def test_create_payment_rejects_malformed_input_and_stores_no_payment(
    client, merchant_token, db, payload
):
    # Valid write proves the endpoint works and executes the PaymentIn/create path;
    # malformed writes below must not add any more rows.
    valid = {"card_number": "4111111111111111", "amount": 100, "currency": "INR"}
    assert client.post("/payments", json=valid, headers=merchant_token).status_code == 201
    before = len(db.rows("SELECT * FROM payments"))

    response = client.post("/payments", json=payload, headers=merchant_token)

    assert response.status_code == 422
    assert len(db.rows("SELECT * FROM payments")) == before


@pytest.mark.parametrize(
    "payload",
    [
        {"username": ["admin"], "password": "pw"},
        {"username": "admin", "password": {"raw": "pw"}},
        {"username": "admin"},
    ],
)
def test_admin_login_rejects_malformed_input_and_stores_no_login_code(
    client, admin_user, captured_emails, db, payload
):
    before_codes = len(db.rows("SELECT * FROM login_codes"))

    response = client.post("/admin/login", json=payload)

    assert response.status_code == 422
    assert len(db.rows("SELECT * FROM login_codes")) == before_codes
    assert captured_emails == []


@pytest.mark.parametrize(
    "payload",
    [
        {"username": ["admin"], "code": "000000"},
        {"username": "admin", "code": {"value": "000000"}},
        {"username": "admin"},
    ],
)
def test_admin_verify_rejects_malformed_input_and_stores_no_session(
    client, admin_user, captured_emails, db, payload
):
    login = client.post(
        "/admin/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert login.status_code == 200
    before_codes = db.rows("SELECT * FROM login_codes")
    before_sessions = len(db.rows("SELECT * FROM admin_sessions"))

    response = client.post("/admin/login/verify", json=payload)

    assert response.status_code == 422
    assert len(db.rows("SELECT * FROM admin_sessions")) == before_sessions
    assert db.rows("SELECT * FROM login_codes") == before_codes

    # The rejected request did not lock out a valid TOTP login.
    valid_verify = client.post(
        "/admin/login/verify",
        json={"username": admin_user["username"], "code": totp_code(admin_user["totp_secret"])},
    )
    assert valid_verify.status_code == 200
