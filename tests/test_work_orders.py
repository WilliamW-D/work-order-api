from fastapi.testclient import TestClient

def test_create_work_order(
    created_work_order: dict,
) -> None:
    assert created_work_order[
        "status"
    ] == "open"
    
    assert created_work_order[
        "priority"
    ] == "high"
    
    assert created_work_order[
        "completed_at"
    ] is None

def test_retired_asset_rejects_work_order(
    client: TestClient,
    auth_headers: dict[str, str],
    created_asset: dict,
) -> None:
    client.delete(
        f"/assets/{created_asset['id']}",
        headers=auth_headers,
    )
    
    response = client.post(
        "/work-orders",
        headers=auth_headers,
        json={
            "asset_id": created_asset["id"],
            "title": "Should fail",
            "description": (
                "Retired assets should "
                "reject new work."
            ),
            "priority": "medium",
        },
    )
    
    assert response.status_code == 409

def test_work_order_status_transition(
    client: TestClient,
    auth_headers: dict[str, str],
    created_work_order: dict,
) -> None:
    response = client.patch(
        (
            "/work-orders/"
            f"{created_work_order['id']}"
        ),
        headers=auth_headers,
        json={
            "status": "in_progress",
        },
    )
    
    assert response.status_code == 200
    
    assert (
        response.json()["status"]
        == "in_progress"
    )

def test_complete_work_order(
    client: TestClient,
    auth_headers: dict[str, str],
    created_work_order: dict,
) -> None:
    work_order_id = created_work_order[
        "id"
    ]
    
    response = client.post(
        f"/work-orders/{work_order_id}/complete",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["status"] == "completed"
    assert data["completed_at"] is not None

def test_completed_work_order_cannot_be_modified(
    client: TestClient,
    auth_headers: dict[str, str],
    created_work_order: dict,
) -> None:
    work_order_id = created_work_order[
        "id"
    ]
    
    client.post(
        f"/work-orders/{work_order_id}/complete",
        headers=auth_headers,
    )
    
    response = client.patch(
        f"/work-orders/{work_order_id}",
        headers=auth_headers,
        json={
            "priority": "low",
        },
    )
    
    assert response.status_code == 409

def test_work_order_filtering(
    client: TestClient,
    auth_headers: dict[str, str],
    created_work_order: dict,
) -> None:
    response = client.get(
        "/work-orders?priority=high&status=open",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["pagination"]["total"] == 1
    assert len(data["items"]) == 1
