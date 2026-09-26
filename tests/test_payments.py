TEST_CARD = "4111111111111111"


def test_create_payment_returns_last4(client, merchant_token):
    r = client.post("/payments", json={"card_number": TEST_CARD, "amount": 500}, headers=merchant_token)
    assert r.status_code == 201
    body = r.json()
    assert body["card_last4"] == "1111"
    assert body["status"] == "captured"


def test_get_payment(client, merchant_token):
    pid = client.post("/payments", json={"card_number": TEST_CARD, "amount": 500},
                      headers=merchant_token).json()["id"]
    r = client.get(f"/payments/{pid}", headers=merchant_token)
    assert r.status_code == 200
    assert r.json()["amount"] == 500


def test_list_payments(client, merchant_token):
    client.post("/payments", json={"card_number": TEST_CARD, "amount": 100}, headers=merchant_token)
    client.post("/payments", json={"card_number": TEST_CARD, "amount": 200}, headers=merchant_token)
    assert len(client.get("/payments", headers=merchant_token).json()) == 2


def test_rejects_bad_card_number(client, merchant_token):
    r = client.post("/payments", json={"card_number": "12ab", "amount": 500}, headers=merchant_token)
    assert r.status_code == 422


def test_requires_merchant_token(client):
    assert client.get("/payments").status_code == 401
