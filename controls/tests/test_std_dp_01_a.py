import pytest
"""STD-DP-01.a: read APIs return only needed personal data fields."""

from testkit import totp_code


TEST_CARD = "4111111111111111"
PERSONAL_FIELDS = {"email", "phone", "full_name", "fullname", "name_full"}
PAYMENT_READ_FIELDS = {"id", "amount", "currency", "status", "card_last4"}
MERCHANT_LIST_FIELDS = {"id", "name"}


def _admin_session(client, admin_user, captured_emails):
    response = client.post(
        "/admin/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert response.status_code == 200
    code = totp_code(admin_user["totp_secret"])
    response = client.post(
        "/admin/login/verify",
        json={"username": admin_user["username"], "code": code},
    )
    assert response.status_code == 200
    return response.json()["session"]


def _assert_records_have_only_needed_fields(records, allowed_fields):
    for record in records:
        keys = set(record)
        assert keys <= allowed_fields, f"unexpected response fields: {sorted(keys - allowed_fields)} in {record!r}"
        unnecessary_personal = keys & PERSONAL_FIELDS - allowed_fields
        assert not unnecessary_personal, f"unnecessary personal fields returned: {sorted(unnecessary_personal)}"


@pytest.mark.xfail(strict=True, reason="https://github.com/oplatechie/payments-demo/issues/2 STD-DP-01.a")
def test_read_endpoints_do_not_return_unnecessary_personal_fields(
    client, merchant_token, admin_user, captured_emails, merchants
):
    payment_id = client.post(
        "/payments",
        json={"card_number": TEST_CARD, "amount": 500},
        headers=merchant_token,
    ).json()["id"]

    payment = client.get(f"/payments/{payment_id}", headers=merchant_token)
    assert payment.status_code == 200
    _assert_records_have_only_needed_fields([payment.json()], PAYMENT_READ_FIELDS)

    payments = client.get("/payments", headers=merchant_token)
    assert payments.status_code == 200
    _assert_records_have_only_needed_fields(payments.json(), PAYMENT_READ_FIELDS)

    session = _admin_session(client, admin_user, captured_emails)
    merchant_list = client.get("/admin/merchants", headers={"X-Admin-Session": session})
    assert merchant_list.status_code == 200
    _assert_records_have_only_needed_fields(merchant_list.json(), MERCHANT_LIST_FIELDS)
