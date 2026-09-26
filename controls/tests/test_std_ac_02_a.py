import pytest

from testkit import extract_code


@pytest.mark.parametrize("email_index", [0])
@pytest.mark.xfail(strict=True, reason="https://github.com/oplatechie/payments-demo/issues/1 STD-AC-02.a")
def test_email_code_cannot_complete_admin_login(client, admin_user, captured_emails, db, email_index):
    """Email-delivered codes are offered by this app but must not create admin sessions."""
    start = client.post(
        "/admin/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )

    assert start.status_code == 200
    assert start.json().get("second_factor") == "email_code"
    assert captured_emails, "admin login should send an email code when that factor is offered"

    email_code = extract_code(captured_emails[email_index])
    verify = client.post(
        "/admin/login/verify",
        json={"username": admin_user["username"], "code": email_code},
    )

    assert verify.status_code in {401, 403}
    assert "session" not in verify.json()
    assert db.rows("SELECT username FROM admin_sessions") == []
