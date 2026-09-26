from testkit import extract_code


def login(client, admin_user, captured_emails):
    r = client.post("/admin/login", json={"username": admin_user["username"], "password": admin_user["password"]})
    assert r.status_code == 200
    code = extract_code(captured_emails[-1])
    r = client.post("/admin/login/verify", json={"username": admin_user["username"], "code": code})
    assert r.status_code == 200
    return r.json()["session"]


def test_admin_login_with_code(client, admin_user, captured_emails):
    assert login(client, admin_user, captured_emails)


def test_wrong_password_rejected(client, admin_user):
    r = client.post("/admin/login", json={"username": admin_user["username"], "password": "wrong"})
    assert r.status_code == 401


def test_admin_can_list_merchants(client, admin_user, captured_emails, merchants):
    session = login(client, admin_user, captured_emails)
    r = client.get("/admin/merchants", headers={"X-Admin-Session": session})
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_admin_endpoint_requires_session(client):
    assert client.get("/admin/merchants").status_code == 401
