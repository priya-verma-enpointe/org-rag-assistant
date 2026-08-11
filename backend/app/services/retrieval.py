from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from google import genai 
from app.config import settings

from google.genai import types

import asyncio
import re
from google.genai.errors import APIError, ClientError

client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def embed_with_retry(contents, model: str = "gemini-embedding-2", config: dict = None, max_retries: int = 5):
    if config is None:
        config = {"output_dimensionality": 768}
        
    for attempt in range(max_retries):
        try:
            # Call synchronous SDK method in executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.embed_content(
                    model=model,
                    contents=contents,
                    config=config
                )
            )
            return response
        except (APIError, ClientError) as e:
            is_429 = getattr(e, 'code', None) == 429 or "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if is_429 and attempt < max_retries - 1:
                # Default sleep time in seconds
                retry_seconds = 10.0
                try:
                    # Parse "Please retry in X.Y seconds" from the message
                    match = re.search(r"Please retry in ([\d\.]+)s", str(e), re.IGNORECASE)
                    if match:
                        retry_seconds = float(match.group(1)) + 1.0  # add 1s buffer
                    else:
                        # Fallback parsing for "retryDelay: 'Xs'" or similar format
                        match_seconds = re.search(r"retryDelay': '(\d+)s'", str(e))
                        if match_seconds:
                            retry_seconds = float(match_seconds.group(1)) + 1.0
                except Exception:
                    pass
                
                print(f"Rate limit hit. Retrying in {retry_seconds:.2f} seconds (attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(retry_seconds)
            else:
                raise e

async def get_embedding(text_input: str) -> list[float]:
    """Generates vector embedding for input text using Gemini"""
    response = await embed_with_retry(text_input)
    return response.embeddings[0].values

async def get_embeddings_batch(texts: list[str], batch_size: int = 50) -> list[list[float]]:
    """Generates vector embeddings for a list of input texts in batches using Gemini"""
    if not texts:
        return []
    
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        contents = [
            types.Content(parts=[types.Part.from_text(text=txt)])
            for txt in batch_texts
        ]
        response = await embed_with_retry(contents)
        for emb in response.embeddings:
            all_embeddings.append(emb.values)
            
    return all_embeddings


async def search_relevant_chunks(
    db: AsyncSession,
    query: str,
    organization_id: int,
    document_ids: list[int] = None,
    top_k: int = 4
):
    """
    Searches PostgreSQL pgvector with strict organization_id isolation and optional document filtering
    """
    query_vector = await get_embedding(query)

    query_str = """
        SELECT d.file_name, c.page_number, c.chunk_content,
               1 - (c.embedding <=> CAST(:vector AS vector)) AS similarity
        FROM document_chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.organization_id = :org_id 
          AND 1 - (c.embedding <=> CAST(:vector AS vector)) >= 0.5
    """
    
    params = {
        "vector": str(query_vector),
        "org_id": organization_id,
        "top_k": top_k
    }

    if document_ids:
        query_str += " AND c.document_id = ANY(:doc_ids)"
        params["doc_ids"] = list(document_ids)

    query_str += """
        ORDER BY similarity DESC
        LIMIT :top_k
    """

    sql_query = text(query_str)
    result = await db.execute(sql_query, params)
    return result.fetchall()