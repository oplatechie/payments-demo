"""STD-CRYPTO-02.a: no full PAN is stored in any database table."""

from testkit import is_luhn_pan


TEST_PAN = "4000000000000002"


def test_payment_creation_does_not_store_full_pan_in_database(client, merchant_token, db):
    response = client.post(
        "/payments",
        json={"card_number": TEST_PAN, "amount": 1234, "currency": "INR"},
        headers=merchant_token,
    )
    assert response.status_code == 201

    stored_pans = [
        (table, column, value)
        for table, column, value in db.all_values()
        if is_luhn_pan(value)
    ]

    assert stored_pans == []
