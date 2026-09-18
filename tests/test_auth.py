from fastapi.testclient import TestClient

def test_register_user(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "full_name": "Test User",
            "password": "TestPassword123!",
        },
    )
    
    assert response.status_code == 201
    
    data = response.json()
    
    assert data["email"] == "user@example.com"
    assert data["role"] == "technician"
    
    assert "password" not in data
    assert "password_hash" not in data

def test_duplicate_user_returns_conflict(
    client: TestClient,
) -> None:
    payload = {
        "email": "user@example.com",
        "full_name": "Test User",
        "password": "TestPassword123!",
    }
    
    first = client.post(
        "/auth/register",
        json=payload,
    )
    
    second = client.post(
        "/auth/register",
        json=payload,
    )
    
    assert first.status_code == 201
    assert second.status_code == 409

def test_login_returns_access_token(
    client: TestClient,
    register_user,
) -> None:
    register_user()
    
    response = client.post(
        "/auth/token",
        data={
            "username": "tech@example.com",
            "password": "TestPassword123!",
        },
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["token_type"] == "bearer"
    assert data["access_token"]

def test_invalid_password_is_rejected(
    client: TestClient,
    register_user,
) -> None:
    register_user()
    
    response = client.post(
        "/auth/token",
        data={
            "username": "tech@example.com",
            "password": "wrong-password",
        },
    )
    
    assert response.status_code == 401

def test_users_me_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/users/me"
    )
    
    assert response.status_code == 401

def test_users_me_returns_current_user(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/users/me",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    
    assert (
        response.json()["email"]
        == "tech@example.com"
    )
