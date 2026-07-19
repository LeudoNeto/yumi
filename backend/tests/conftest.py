"""Shared fixtures for Yumi backend unit tests.

Uses an in-memory SQLite database so tests run without Docker / MySQL.
"""
import os

# Override DATABASE_URL *before* any app module is imported so that
# config.settings picks up SQLite instead of the default MySQL DSN.
os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def engine():
    """Create a single in-memory SQLite engine shared across the whole test session."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Enable foreign-key enforcement (off by default in SQLite)
    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture()
def db(engine):
    """Yield a session wrapped in a transaction that is rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """TestClient whose requests use the per-test database session."""
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------
_counter = 0


def _unique_id() -> int:
    global _counter
    _counter += 1
    return _counter


@pytest.fixture()
def auth_headers(client) -> dict[str, str]:
    """Register a company + admin and return Authorization headers."""
    uid = _unique_id()
    resp = client.post("/api/auth/register", json={
        "company_name": f"Test Store {uid}",
        "empresa_url": f"test-store-{uid}",
        "admin_name": "Admin Test",
        "admin_email": f"admin-{uid}@test.com",
        "password": "password123",
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def second_auth_headers(client) -> dict[str, str]:
    """Register a *second* company + admin for cross-company tests."""
    uid = _unique_id()
    resp = client.post("/api/auth/register", json={
        "company_name": f"Other Store {uid}",
        "empresa_url": f"other-store-{uid}",
        "admin_name": "Other Admin",
        "admin_email": f"other-{uid}@test.com",
        "password": "password123",
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def customer_headers(client) -> dict[str, str]:
    """Register a customer account and return Authorization headers."""
    uid = _unique_id()
    resp = client.post("/api/customer/auth/register", json={
        "name": f"Customer {uid}",
        "email": f"customer-{uid}@test.com",
        "phone": "11999990000",
        "password": "custpass123",
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def empresa_url(auth_headers, client) -> str:
    """Return the empresa_url slug of the company created by auth_headers."""
    resp = client.get("/api/company", headers=auth_headers)
    assert resp.status_code == 200
    return resp.json()["empresa_url"]


@pytest.fixture()
def seed_menu(auth_headers, client) -> dict:
    """Create a category with one item (+ option group) and return ids.

    Returns dict with keys: category_id, item_id, option_group_id, option_id, empresa_url
    """
    # Get empresa_url
    company = client.get("/api/company", headers=auth_headers).json()

    # Create category
    cat = client.post("/api/menu/categories", json={
        "name": "Bebidas",
        "description": "Drinks",
    }, headers=auth_headers)
    assert cat.status_code == 201, cat.text
    cat_data = cat.json()

    # Create item with option group
    item = client.post(f"/api/menu/categories/{cat_data['id']}/items", json={
        "name": "Guaraná Antarctica",
        "description": "Lata 350ml",
        "base_price": 7.00,
        "option_groups": [
            {
                "name": "Tamanho",
                "min_select": 0,
                "max_select": 1,
                "allow_repeat": False,
                "options": [
                    {"name": "Lata 350ml", "price_delta": 0.0},
                    {"name": "Garrafa 600ml", "price_delta": 3.0},
                ],
            }
        ],
    }, headers=auth_headers)
    assert item.status_code == 201, item.text
    item_data = item.json()

    og = item_data["option_groups"][0]
    return {
        "category_id": cat_data["id"],
        "item_id": item_data["id"],
        "option_group_id": og["id"],
        "option_ids": [o["id"] for o in og["options"]],
        "empresa_url": company["empresa_url"],
    }
