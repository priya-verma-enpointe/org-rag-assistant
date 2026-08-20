import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_chat_and_history(client: AsyncClient):
    # 1. Create Organization
    org_res = await client.post("/api/v1/organizations/", json={"name": "Chat Org"})
    org_id = org_res.json()["id"]

    # 2. Chat with Mocked Retrieval and LLM
    question = "What is the policy?"
    
    # Create mock chunk objects
    class MockChunk:
        def __init__(self, file_name, page_number, chunk_content):
            self.file_name = file_name
            self.page_number = page_number
            self.chunk_content = chunk_content

    mock_chunks = [MockChunk("policy.pdf", 3, "This is the organization policy.")]
    mock_answer = "According to the provided document, this is the organization policy."

    with patch("app.api.v1.endpoints.chat.search_relevant_chunks", new_callable=AsyncMock) as mock_search, \
         patch("app.api.v1.endpoints.chat.generate_rag_answer", new_callable=AsyncMock) as mock_llm:
         
        mock_search.return_value = mock_chunks
        mock_llm.return_value = mock_answer

        chat_payload = {
            "organizationId": org_id,
            "question": question,
            "selectedDocumentIds": []
        }

        response = await client.post("/api/v1/chat", json=chat_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == mock_answer
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document"] == "policy.pdf"
        assert data["sources"][0]["page"] == 3

    # 3. Get Chat History
    history_res = await client.get(f"/api/v1/chat/history/{org_id}?skip=0&limit=5")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    assert history[0]["question"] == question
    assert history[0]["answer"] == mock_answer

    # 4. Clean up organization
    del_org = await client.delete(f"/api/v1/organizations/{org_id}")
    assert del_org.status_code == 200


@pytest.mark.asyncio
async def test_chat_stream(client: AsyncClient):
    # 1. Create Organization
    org_res = await client.post("/api/v1/organizations/", json={"name": "Chat Stream Org"})
    org_id = org_res.json()["id"]

    # Mock chunk objects
    class MockChunk:
        def __init__(self, file_name, page_number, chunk_content):
            self.file_name = file_name
            self.page_number = page_number
            self.chunk_content = chunk_content

    mock_chunks = [MockChunk("policy.pdf", 3, "This is the organization policy.")]

    # Create mock generator for generate_rag_response_stream
    async def mock_generator(query, context_chunks):
        yield 'data: {"sources": [{"file_name": "policy.pdf", "page": 3}]}\n\n'
        yield 'data: {"text": "According"}\n\n'
        yield 'data: {"text": " to the policy"}\n\n'
        yield 'data: [DONE]\n\n'

    with patch("app.api.v1.endpoints.chat.search_relevant_chunks", new_callable=AsyncMock) as mock_search, \
         patch("app.api.v1.endpoints.chat.generate_rag_response_stream", side_effect=mock_generator) as mock_stream:
         
        mock_search.return_value = mock_chunks

        chat_payload = {
            "organizationId": org_id,
            "question": "What is the policy?",
            "selectedDocumentIds": []
        }

        async with client.stream("POST", "/api/v1/chat/stream", json=chat_payload) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            
            lines = []
            async for line in response.aiter_lines():
                if line:
                    lines.append(line)
            
            assert len(lines) >= 3
            assert lines[0].startswith("data: ")
            assert "sources" in lines[0]
            assert "According" in lines[1]
            assert lines[-1] == "data: [DONE]"

    # Clean up organization
    del_org = await client.delete(f"/api/v1/organizations/{org_id}")
    assert del_org.status_code == 200
