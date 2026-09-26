"""STD-AC-02.a Admin login needs TOTP or a security key. Email or SMS codes never complete admin login."""
from testkit import totp_code


def test_admin_login_requires_totp_and_sends_no_email_code(client, admin_user, captured_emails, db):
    start = client.post(
        "/admin/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert start.status_code == 200
    assert start.json().get("second_factor") in {"totp", "webauthn"}
    assert captured_emails == [], "no login code may be sent by email"

    guessed = client.post("/admin/login/verify", json={"username": admin_user["username"], "code": "123456"})
    assert guessed.status_code in {401, 403}
    assert db.rows("SELECT username FROM admin_sessions") == []

    ok = client.post(
        "/admin/login/verify",
        json={"username": admin_user["username"], "code": totp_code(admin_user["totp_secret"])},
    )
    assert ok.status_code == 200
    assert db.rows("SELECT username FROM admin_sessions") == [{"username": admin_user["username"]}]
