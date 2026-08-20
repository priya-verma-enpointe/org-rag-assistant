import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_required():
    from app.main import app
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/organizations/")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_organization_crud(client: AsyncClient):
    # 1. Create Organization
    create_payload = {"name": "Test Organization"}
    response = await client.post("/api/v1/organizations/", json=create_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Organization"
    org_id = data["id"]

    # 2. Get Organization
    response = await client.get(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Organization"

    # 3. List Organizations (Paginated)
    response = await client.get("/api/v1/organizations/?skip=0&limit=100")
    assert response.status_code == 200
    orgs = response.json()
    assert len(orgs) >= 1
    assert any(o["id"] == org_id for o in orgs)

    # 4. Update Organization
    update_payload = {"name": "Updated Org"}
    response = await client.put(f"/api/v1/organizations/{org_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Org"

    # 5. Delete Organization
    response = await client.delete(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 200
    assert "successfully deleted" in response.json()["message"]

    # 6. Verify 404 for deleted organization
    response = await client.get(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 404
