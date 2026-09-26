"""STD-AC-02.b: protected admin endpoints require a valid admin session."""


def test_admin_merchants_rejects_missing_and_unknown_admin_session(client, conn, admin_user):
    # A valid-session call proves this is the protected admin endpoint under test
    # and exercises the endpoint body, not only FastAPI route registration.
    from app.db import sha256

    valid_session = "valid-admin-session-token"
    conn.execute(
        "INSERT INTO admin_sessions (token_hash, username) VALUES (?, ?)",
        (sha256(valid_session), admin_user["username"]),
    )
    conn.commit()

    valid_response = client.get("/admin/merchants", headers={"X-Admin-Session": valid_session})
    assert valid_response.status_code == 200

    unauthenticated_response = client.get("/admin/merchants")
    assert unauthenticated_response.status_code in {401, 403}

    forged_response = client.get(
        "/admin/merchants",
        headers={"X-Admin-Session": "not-a-real-admin-session"},
    )
    assert forged_response.status_code in {401, 403}
