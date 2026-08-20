import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import asyncio

@pytest.mark.asyncio
async def test_document_upload_and_status(client: AsyncClient):
    # 1. Create Organization
    org_res = await client.post("/api/v1/organizations/", json={"name": "Doc Org"})
    org_id = org_res.json()["id"]

    # Mock get_embeddings_batch to avoid calling actual Gemini
    mock_embeddings = [[0.1] * 768]
    
    with patch("app.api.v1.endpoints.documents.get_embeddings_batch", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_embeddings
        
        # 2. Upload Document
        file_content = b"This is some test content for the knowledge assistant document."
        files = {"file": ("test_doc.txt", file_content, "text/plain")}
        
        response = await client.post(f"/api/v1/organizations/{org_id}/documents", files=files)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "PENDING"
        doc_id = data["id"]
        
        # Allow background tasks to run
        await asyncio.sleep(0.5)
        
        # 3. Check status
        status_res = await client.get(f"/api/v1/organizations/{org_id}/documents/{doc_id}/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["id"] == doc_id
        assert status_data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]

    # 4. List documents (paginated)
    list_res = await client.get(f"/api/v1/organizations/{org_id}/documents?skip=0&limit=5")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 1
    assert docs[0]["id"] == doc_id

    # 5. Delete document
    del_res = await client.delete(f"/api/v1/organizations/{org_id}/documents/{doc_id}")
    assert del_res.status_code == 200

    # 6. Clean up organization
    del_org = await client.delete(f"/api/v1/organizations/{org_id}")
    assert del_org.status_code == 200
