from fastapi.testclient import TestClient

def test_add_work_order_note(
    client: TestClient,
    auth_headers: dict[str, str],
    created_work_order: dict,
) -> None:
    work_order_id = created_work_order[
        "id"
    ]
    
    response = client.post(
        f"/work-orders/{work_order_id}/notes",
        headers=auth_headers,
        json={
            "content": (
                "Inspected hydraulic lines."
            )
        },
    )
    
    assert response.status_code == 201
    
    data = response.json()
    
    assert (
        data["work_order_id"]
        == work_order_id
    )
    
    assert (
        data["content"]
        == "Inspected hydraulic lines."
    )

def test_asset_history_includes_notes(
    client: TestClient,
    auth_headers: dict[str, str],
    created_asset: dict,
    created_work_order: dict,
) -> None:
    work_order_id = created_work_order["id"]
    
    # Add a note
    client.post(
        f"/work-orders/{work_order_id}/notes",
        headers=auth_headers,
        json={
            "content": "Inspected hydraulic lines."
        },
    )
    
    # Complete work order to add to history
    client.post(
        f"/work-orders/{work_order_id}/complete",
        headers=auth_headers,
    )
    
    response = client.get(
        f"/assets/{created_asset['id']}/history",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    
    history_item = data[0]
    assert history_item["id"] == work_order_id
    assert len(history_item["notes"]) == 1
    assert history_item["notes"][0]["content"] == "Inspected hydraulic lines."
