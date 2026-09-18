import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

def load_test_environment() -> None:
    """Load local .env.test values before application imports."""
    
    env_file = Path(".env.test")
    
    if not env_file.exists():
        return
        
    for line in env_file.read_text().splitlines():
        line = line.strip()
        
        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue
            
        key, value = line.split(
            "=",
            maxsplit=1,
        )
        
        os.environ.setdefault(
            key.strip(),
            value.strip(),
        )

load_test_environment()

from work_order_api.database import engine  # noqa: E402
from work_order_api.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_database():
    """Remove application data before and after each test."""
    
    clean_sql = text(
        """
        TRUNCATE TABLE
            work_order_notes,
            work_orders,
            assets,
            users
        RESTART IDENTITY CASCADE
        """
    )
    
    with engine.begin() as connection:
        connection.execute(clean_sql)
        
    yield
    
    with engine.begin() as connection:
        connection.execute(clean_sql)


@pytest.fixture
def register_user(client: TestClient):
    def _register(
        *,
        email: str = "tech@example.com",
        password: str = "TestPassword123!",
        full_name: str = "Test Technician",
    ):
        return client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
            }
        )
        
    return _register


@pytest.fixture
def auth_headers(
    client: TestClient,
    register_user,
):
    register_response = register_user()
    
    assert register_response.status_code == 201
    
    login_response = client.post(
        "/auth/token",
        data={
            "username": "tech@example.com",
            "password": "TestPassword123!",
        },
    )
    
    assert login_response.status_code == 200
    
    token = login_response.json()[
        "access_token"
    ]
    
    return {
        "Authorization": f"Bearer {token}",
    }

@pytest.fixture
def created_asset(
    client: TestClient,
    auth_headers: dict[str, str],
):
    response = client.post(
        "/assets",
        headers=auth_headers,
        json={
            "name": "Test Forklift",
            "asset_tag": "FLT-001",
            "manufacturer": "Toyota",
            "model": "8FGCU25",
            "serial_number": "TEST-FLT-001",
            "location": "Shipping",
        },
    )
    
    assert response.status_code == 201
    
    return response.json()


@pytest.fixture
def created_work_order(
    client: TestClient,
    auth_headers: dict[str, str],
    created_asset: dict,
):
    response = client.post(
        "/work-orders",
        headers=auth_headers,
        json={
            "asset_id": created_asset["id"],
            "title": "Hydraulic leak",
            "description": (
                "Hydraulic fluid visible "
                "near lift cylinder."
            ),
            "priority": "high",
        },
    )
    
    assert response.status_code == 201
    
    return response.json()
