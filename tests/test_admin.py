from testkit import totp_code


def test_admin_login_with_totp(client, admin_user):
    r = client.post("/admin/login", json={"username": admin_user["username"], "password": admin_user["password"]})
    assert r.json() == {"second_factor": "totp"}
    r = client.post("/admin/login/verify",
                    json={"username": admin_user["username"], "code": totp_code(admin_user["totp_secret"])})
    assert r.status_code == 200 and r.json()["session"]


def test_wrong_totp_rejected(client, admin_user):
    client.post("/admin/login", json={"username": admin_user["username"], "password": admin_user["password"]})
    r = client.post("/admin/login/verify", json={"username": admin_user["username"], "code": "000000"})
    assert r.status_code == 401


def test_wrong_password_rejected(client, admin_user):
    r = client.post("/admin/login", json={"username": admin_user["username"], "password": "wrong"})
    assert r.status_code == 401


def test_admin_can_list_merchants(client, admin_session, merchants):
    r = client.get("/admin/merchants", headers={"X-Admin-Session": admin_session})
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_admin_endpoint_requires_session(client):
    assert client.get("/admin/merchants").status_code == 401
