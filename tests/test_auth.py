def test_register_user(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "new@test.com", "password": "Strong123!"}
    )
    assert res.status_code == 201


def test_register_duplicate_user(client):
    client.post(
        "/api/auth/register",
        json={"email": "dup@test.com", "password": "123"}
    )

    res = client.post(
        "/api/auth/register",
        json={"email": "dup@test.com", "password": "123"}
    )

    assert res.status_code == 400


def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={"email": "login@test.com", "password": "pass"}
    )

    res = client.post(
        "/api/auth/login",
        json={"email": "login@test.com", "password": "pass"}
    )

    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_bad_credentials(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "nope@test.com", "password": "wrong"}
    )

    assert res.status_code == 401
