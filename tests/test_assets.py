from fastapi.testclient import TestClient

def asset_payload(
    *,
    asset_tag: str = "TEST-001",
) -> dict:
    return {
        "name": "Test Forklift",
        "asset_tag": asset_tag,
        "manufacturer": "Toyota",
        "model": "8FGCU25",
        "serial_number": f"SERIAL-{asset_tag}",
        "location": "Shipping",
    }

def test_create_asset(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/assets",
        headers=auth_headers,
        json=asset_payload(),
    )
    
    assert response.status_code == 201
    
    data = response.json()
    
    assert data["asset_tag"] == "TEST-001"
    assert data["status"] == "active"

def test_assets_require_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/assets"
    )
    
    assert response.status_code == 401

def test_duplicate_asset_tag_returns_409(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    client.post(
        "/assets",
        headers=auth_headers,
        json=asset_payload(),
    )
    
    response = client.post(
        "/assets",
        headers=auth_headers,
        json=asset_payload(
            asset_tag="test-001"
        ),
    )
    
    assert response.status_code == 409

def test_asset_can_be_updated(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = client.post(
        "/assets",
        headers=auth_headers,
        json=asset_payload(),
    ).json()
    
    response = client.patch(
        f"/assets/{created['id']}",
        headers=auth_headers,
        json={
            "location": "Maintenance Bay",
            "status": "out_of_service",
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["location"] == "Maintenance Bay"
    assert data["status"] == "out_of_service"

def test_delete_retires_asset(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    asset = client.post(
        "/assets",
        headers=auth_headers,
        json=asset_payload(),
    ).json()
    
    response = client.delete(
        f"/assets/{asset['id']}",
        headers=auth_headers,
    )
    
    assert response.status_code == 204
    
    retrieved = client.get(
        f"/assets/{asset['id']}",
        headers=auth_headers,
    )
    
    assert (
        retrieved.json()["status"]
        == "retired"
    )

def test_asset_filtering_and_pagination(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    client.post(
        "/assets",
        headers=auth_headers,
        json=asset_payload(
            asset_tag="FLT-001"
        ),
    )
    
    second = asset_payload(
        asset_tag="GEN-001"
    )
    second["name"] = "Backup Generator"
    second["location"] = "Utility Room"
    
    client.post(
        "/assets",
        headers=auth_headers,
        json=second,
    )
    
    response = client.get(
        "/assets?search=forklift&limit=1",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert len(data["items"]) == 1
    assert data["pagination"]["total"] == 1
