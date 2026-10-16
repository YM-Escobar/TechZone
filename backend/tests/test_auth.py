from app.core.config import settings
from tests.conftest import PASSWORD, auth_headers, token_from_email


def register(client, username: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": f"{username}@Mail.com", "username": username, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_register_and_login_with_email_or_username(client):
    user = register(client, "carla")
    assert user["email"] == "carla@mail.com"
    assert user["role"] == "usuario" and user["is_verified"] is False
    auth_headers(client, "carla")
    auth_headers(client, "CARLA@mail.com")


def test_register_duplicate_and_invalid_data(client):
    register(client, "dani")
    duplicated = client.post("/api/auth/register", json={"email": "dani@mail.com", "username": "otro", "password": PASSWORD})
    assert duplicated.status_code == 409
    weak = client.post("/api/auth/register", json={"email": "x@mail.com", "username": "xx_ok", "password": "123"})
    assert weak.status_code == 422


def test_login_errors(client):
    assert client.post("/api/auth/login", data={"username": "nadie", "password": "x"}).status_code == 401
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/users/me", headers={"Authorization": "Bearer basura"}).status_code == 401


def test_refresh_rotates_tokens_and_detects_reuse(client):
    register(client, "elena")
    tokens = client.post("/api/auth/login", data={"username": "elena", "password": PASSWORD}).json()

    rotated = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert rotated.status_code == 200
    new_tokens = rotated.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # Reusar el token viejo cierra todas las sesiones, incluida la nueva
    assert client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]}).status_code == 401


def test_logout_revokes_refresh_token(client):
    register(client, "fabio")
    tokens = client.post("/api/auth/login", data={"username": "fabio", "password": PASSWORD}).json()
    assert client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_logout_all(client):
    register(client, "gina")
    first = client.post("/api/auth/login", data={"username": "gina", "password": PASSWORD}).json()
    second = client.post("/api/auth/login", data={"username": "gina", "password": PASSWORD}).json()
    headers = {"Authorization": f"Bearer {second['access_token']}"}
    assert client.post("/api/auth/logout-all", headers=headers).status_code == 200
    for tokens in (first, second):
        assert client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_email_verification(client, outbox):
    register(client, "hugo")
    token = token_from_email(outbox, "hugo@mail.com")

    verified = client.post("/api/auth/verify-email", json={"token": token})
    assert verified.status_code == 200 and verified.json()["is_verified"] is True
    # Cada enlace sirve una sola vez
    assert client.post("/api/auth/verify-email", json={"token": token}).status_code == 400

    headers = auth_headers(client, "hugo")
    assert client.post("/api/auth/resend-verification", headers=headers).status_code == 409


def test_require_email_verification(client, outbox, monkeypatch):
    register(client, "irene")
    headers = auth_headers(client, "irene")
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)

    post = {"title": "Hola comunidad", "content": "Mi primer post"}
    assert client.post("/api/posts", json=post, headers=headers).status_code == 403

    assert client.post("/api/auth/resend-verification", headers=headers).status_code == 202
    client.post("/api/auth/verify-email", json={"token": token_from_email(outbox, "irene@mail.com")})
    assert client.post("/api/posts", json=post, headers=headers).status_code == 201


def test_password_reset_flow(client, outbox):
    register(client, "juan")
    session = client.post("/api/auth/login", data={"username": "juan", "password": PASSWORD}).json()

    assert client.post("/api/auth/forgot-password", json={"email": "juan@mail.com"}).status_code == 202
    # Un correo que no existe responde igual, para no revelar qué cuentas hay
    assert client.post("/api/auth/forgot-password", json={"email": "noexiste@mail.com"}).status_code == 202

    token = token_from_email(outbox, "juan@mail.com")
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": "nueva12345"}).status_code == 200
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": "otra12345"}).status_code == 400

    auth_headers(client, "juan", "nueva12345")
    # Cambiar la contraseña cierra las sesiones anteriores
    assert client.post("/api/auth/refresh", json={"refresh_token": session["refresh_token"]}).status_code == 401
