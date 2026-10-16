"""Configuración de pruebas.

Por defecto usan una base SQLite temporal. Para probar contra PostgreSQL:
    $env:TEST_DATABASE_URL = "postgresql://usuario:clave@host/base_de_pruebas"
¡Nunca apuntes TEST_DATABASE_URL a una base con datos reales: las pruebas la vacían!
"""
import itertools
import os
import re
import tempfile
from pathlib import Path

import pytest

_tmp = Path(tempfile.mkdtemp(prefix="techzone-tests-"))
os.environ.update({
    "DATABASE_URL": os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp / 'test.db'}"),
    "SECRET_KEY": "clave-solo-para-pruebas-no-usar-en-produccion",
    "FIRST_ADMIN_EMAIL": "admin@techzone.com",
    "FIRST_ADMIN_USERNAME": "admin",
    "FIRST_ADMIN_PASSWORD": "Admin12345",
    "UPLOAD_DIR": str(_tmp / "uploads"),
    "SMTP_HOST": "",
    "REQUIRE_EMAIL_VERIFICATION": "false",
})

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import Models  # noqa: E402,F401
from app.db.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.Services import mailer  # noqa: E402

PASSWORD = "secret123"
_counter = itertools.count(1)


@pytest.fixture(scope="session")
def outbox():
    """Correos enviados durante las pruebas, en lugar de mandarlos por SMTP."""
    sent: list[dict] = []
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(mailer, "send_email", lambda to, subject, body: sent.append(
            {"to": to, "subject": subject, "body": body}
        ))
        yield sent


@pytest.fixture(scope="session")
def client(outbox):
    # Base limpia en cada ejecución; las migraciones se aplican al arrancar la app
    Base.metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(client: TestClient, login: str, password: str = PASSWORD) -> dict[str, str]:
    response = client.post("/api/auth/login", data={"username": login, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client) -> dict[str, str]:
    return auth_headers(client, "admin@techzone.com", "Admin12345")


@pytest.fixture
def make_user(client, admin):
    """Crea un usuario (verificado) con el rol indicado y devuelve (datos, headers)."""
    def _make(role: str = "usuario") -> tuple[dict, dict[str, str]]:
        n = next(_counter)
        data = {"email": f"user{n}@mail.com", "username": f"user{n}", "password": PASSWORD, "role": role}
        response = client.post("/api/admin/users", json=data, headers=admin)
        assert response.status_code == 201, response.text
        return response.json(), auth_headers(client, data["username"])
    return _make


@pytest.fixture
def make_product(client, admin):
    def _make(**overrides) -> dict:
        n = next(_counter)
        data = {"name": f"Producto {n}", "brand": "Marca", "category": "gpu", "price": 100, "stock": 5} | overrides
        response = client.post("/api/products", json=data, headers=admin)
        assert response.status_code == 201, response.text
        return response.json()
    return _make


def token_from_email(outbox: list[dict], to: str) -> str:
    """Extrae el token del último enlace enviado a ese correo."""
    body = next(mail["body"] for mail in reversed(outbox) if mail["to"] == to)
    return re.search(r"token=([\w-]+)", body).group(1)
