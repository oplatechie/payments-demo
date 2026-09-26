"""STD-AC-01.a: merchants cannot read or change another merchant's payment records."""


def test_merchant_cannot_read_another_merchants_payment(client, merchants):
    beta_payment = {
        "card_number": "4111111111111111",
        "amount": 4321,
        "currency": "INR",
    }
    create_response = client.post(
        "/payments",
        json=beta_payment,
        headers=merchants["beta"]["headers"],
    )
    assert create_response.status_code == 201
    beta_record = create_response.json()
    beta_payment_id = beta_record["id"]

    # Direct object read by a different merchant must be denied or hidden.
    get_response = client.get(
        f"/payments/{beta_payment_id}",
        headers=merchants["alpha"]["headers"],
    )
    assert get_response.status_code in (403, 404)
    assert beta_payment_id not in get_response.text
    assert "4321" not in get_response.text
    assert beta_record["card_last4"] not in get_response.text

    # Collection read by a different merchant must not leak beta's record.
    list_response = client.get("/payments", headers=merchants["alpha"]["headers"])
    assert list_response.status_code == 200
    alpha_records = list_response.json()
    assert beta_payment_id not in list_response.text
    assert all(record["id"] != beta_payment_id for record in alpha_records)
    assert all(record["amount"] != beta_payment["amount"] for record in alpha_records)
    assert all(record["card_last4"] != beta_record["card_last4"] for record in alpha_records)
