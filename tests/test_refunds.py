TEST_CARD = "4111111111111111"


def _payment(client, headers, amount=1000):
    return client.post("/payments", json={"card_number": TEST_CARD, "amount": amount}, headers=headers).json()["id"]


def test_partial_refund(client, merchant_token):
    pid = _payment(client, merchant_token)
    r = client.post("/refunds", json={"payment_id": pid, "amount": 400}, headers=merchant_token)
    assert r.status_code == 201
    assert r.json()["amount"] == 400 and r.json()["card_last4"] == "1111"


def test_refund_cannot_exceed_payment(client, merchant_token):
    pid = _payment(client, merchant_token, amount=500)
    client.post("/refunds", json={"payment_id": pid, "amount": 300}, headers=merchant_token)
    r = client.post("/refunds", json={"payment_id": pid, "amount": 300}, headers=merchant_token)
    assert r.status_code == 422


def test_get_refund(client, merchant_token):
    pid = _payment(client, merchant_token)
    rid = client.post("/refunds", json={"payment_id": pid, "amount": 100}, headers=merchant_token).json()["id"]
    r = client.get(f"/refunds/{rid}", headers=merchant_token)
    assert r.status_code == 200 and r.json()["payment_id"] == pid
