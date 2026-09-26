import json

from testkit import find_pans


TEST_CARD = "4111111111111111"
LAST4 = TEST_CARD[-4:]


def assert_response_masks_card_number(response):
    assert response.status_code < 400
    body_text = response.text
    assert TEST_CARD not in body_text
    assert find_pans(body_text) == []
    assert LAST4 in body_text


def test_payment_api_responses_expose_only_card_last4(client, merchant_token):
    create_response = client.post(
        "/payments",
        json={"card_number": TEST_CARD, "amount": 500, "currency": "INR"},
        headers=merchant_token,
    )
    assert create_response.status_code == 201
    assert_response_masks_card_number(create_response)

    payment_id = create_response.json()["id"]

    get_response = client.get(f"/payments/{payment_id}", headers=merchant_token)
    assert_response_masks_card_number(get_response)

    list_response = client.get("/payments", headers=merchant_token)
    assert_response_masks_card_number(list_response)

    for body in (create_response.json(), get_response.json(), list_response.json()[0]):
        assert body["card_last4"] == LAST4
        serialized = json.dumps(body)
        assert TEST_CARD not in serialized
        assert find_pans(serialized) == []
