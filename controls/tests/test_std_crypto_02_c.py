import logging

from testkit import find_pans


def test_payment_creation_does_not_log_full_card_number(client, merchant_token, caplog):
    card_number = "4111111111111111"

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/payments",
            headers=merchant_token,
            json={"card_number": card_number, "amount": 1234, "currency": "INR"},
        )

    assert response.status_code == 201
    assert response.json()["card_last4"] == card_number[-4:]
    assert find_pans(caplog.text) == []
