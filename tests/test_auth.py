from tests.conftest import PASSWORD, auth_headers


def test_register_and_login(client):
    res = client.post("/auth/register", json={"email": "ana@gmail.com", "password": PASSWORD})
    assert res.status_code == 201
    assert res.json()["email"] == "ana@gmail.com"
    assert "password" not in res.json()
    assert "hashed_password" not in res.json()

    res = client.post("/auth/login", data={"username": "ana@gmail.com", "password": PASSWORD})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"


def test_duplicate_email_is_rejected(client):
    body = {"email": "ana@gmail.com", "password": PASSWORD}
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409


def test_short_password_is_rejected(client):
    res = client.post("/auth/register", json={"email": "ana@gmail.com", "password": "corta"})
    assert res.status_code == 422


def test_wrong_password_is_rejected(client):
    auth_headers(client, "ana@gmail.com")
    res = client.post("/auth/login", data={"username": "ana@gmail.com", "password": "otra-clave-123"})
    assert res.status_code == 401


def test_me_returns_current_user(client):
    headers = auth_headers(client, "ana@gmail.com")
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "ana@gmail.com"


def test_protected_routes_require_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/expenses").status_code == 401
    assert client.get("/categories").status_code == 401
    assert client.get("/reports/summary").status_code == 401


def test_invalid_token_is_rejected(client):
    res = client.get("/auth/me", headers={"Authorization": "Bearer token-falso"})
    assert res.status_code == 401