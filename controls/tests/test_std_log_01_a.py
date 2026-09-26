from testkit import extract_code


TEST_CARD = "4111111111111111"


def _admin_session(client, admin_user, captured_emails):
    login = client.post(
        "/admin/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert login.status_code == 200
    code = extract_code(captured_emails[-1])
    verified = client.post(
        "/admin/login/verify",
        json={"username": admin_user["username"], "code": code},
    )
    assert verified.status_code == 200
    return verified.json()["session"]


def _audit_rows(db, *, actor, action, resource):
    return db.rows(
        """
        SELECT actor, action, resource, at
        FROM audit_log
        WHERE actor = ? AND action = ? AND resource = ?
        """,
        (actor, action, resource),
    )


def test_sensitive_read_endpoints_write_actor_resource_and_time_audit_records(
    client, merchants, db, admin_user, captured_emails
):
    merchant = merchants["alpha"]
    payment = client.post(
        "/payments",
        json={"card_number": TEST_CARD, "amount": 500},
        headers=merchant["headers"],
    )
    assert payment.status_code == 201
    payment_id = payment.json()["id"]

    payment_read = client.get(f"/payments/{payment_id}", headers=merchant["headers"])
    assert payment_read.status_code == 200
    assert payment_read.json()["card_last4"] == "1111"

    payment_list = client.get("/payments", headers=merchant["headers"])
    assert payment_list.status_code == 200
    assert any(row["id"] == payment_id and row["card_last4"] == "1111" for row in payment_list.json())

    admin_session = _admin_session(client, admin_user, captured_emails)
    merchant_list = client.get("/admin/merchants", headers={"X-Admin-Session": admin_session})
    assert merchant_list.status_code == 200
    assert any(row["id"] == merchant["id"] and row["email"] for row in merchant_list.json())

    expected_audits = [
        (merchant["id"], "payment.read", f"payment:{payment_id}"),
        (merchant["id"], "payment.list", "payments"),
        (f"admin:{admin_user['username']}", "merchant.list", "merchants"),
    ]
    for actor, action, resource in expected_audits:
        rows = _audit_rows(db, actor=actor, action=action, resource=resource)
        assert rows, f"missing audit row for actor={actor} action={action} resource={resource}"
        assert all(row["at"] for row in rows)
