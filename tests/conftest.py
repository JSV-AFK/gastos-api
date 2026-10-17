import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

PASSWORD = "clave-segura-123"


@pytest.fixture()
def client():
    """Cliente de pruebas con una base de datos SQLite en memoria, nueva en cada prueba."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def auth_headers(client: TestClient, email: str) -> dict:
    """Registra un usuario, inicia sesión y devuelve el encabezado Authorization."""
    client.post("/auth/register", json={"email": email, "password": PASSWORD})
    res = client.post("/auth/login", data={"username": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def create_category(client: TestClient, headers: dict, name: str) -> int:
    res = client.post("/categories", json={"name": name}, headers=headers)
    return res.json()["id"]


def create_expense(client: TestClient, headers: dict, **fields) -> dict:
    res = client.post("/expenses", json=fields, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()