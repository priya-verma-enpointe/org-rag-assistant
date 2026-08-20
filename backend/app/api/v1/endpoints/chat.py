import json
import asyncio
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db, AsyncSessionLocal
from app.schemas.chat import ChatRequest, ChatResponse, SourceCitation, ChatHistoryResponse
from app.services.retrieval import search_relevant_chunks
from app.services.llm import generate_rag_answer, generate_rag_response_stream
from app.core.security import verify_api_key
from app.core.exceptions import EntityNotFoundException
import app.crud as crud

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/chat", response_model=ChatResponse)
async def chat_with_docs(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=payload.organizationId)
    if not org:
        raise EntityNotFoundException("Organization not found")

    # Sanitize selectedDocumentIds (Ignore [0] or empty list [])
    doc_ids = getattr(payload, "selectedDocumentIds", None)
    if doc_ids and (doc_ids == [0] or len(doc_ids) == 0):
        doc_ids = None

    # 1. Retrieve vector chunks (with optional @ mention document filtering)
    relevant_chunks = await search_relevant_chunks(
        db=db,
        query=payload.question,
        organization_id=payload.organizationId,
        document_ids=doc_ids,
        top_k=10
    )

    # 2. Generate answer using Gemini LLM
    answer = await generate_rag_answer(payload.question, relevant_chunks)

    # 3. Format source citations (Only if a valid answer was found in documents)
    sources = []
    
    no_info_phrases = [
        "couldn't find any relevant information", 
        "no information", 
        "not mentioned",
        "provided documents do not contain"
    ]
    is_not_found = any(phrase in answer.lower() for phrase in no_info_phrases)

    if not is_not_found:
        seen_sources = set()
        for chunk in relevant_chunks:
            source_key = (chunk.file_name, chunk.page_number)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append(SourceCitation(
                    document=chunk.file_name,
                    page=chunk.page_number
                ))

    # 4. Save Chat History to Database using CRUD layer
    await crud.create_chat_entry(
        db=db,
        organization_id=payload.organizationId,
        question=payload.question,
        answer=answer
    )

    return ChatResponse(
        answer=answer, 
        sources=sources,
        selectedDocumentIds=doc_ids
    )


@router.post("/chat/stream")
async def chat_with_docs_stream(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=payload.organizationId)
    if not org:
        raise EntityNotFoundException("Organization not found")

    # Sanitize selectedDocumentIds (Ignore [0] or empty list [])
    doc_ids = getattr(payload, "selectedDocumentIds", None)
    if doc_ids and (doc_ids == [0] or len(doc_ids) == 0):
        doc_ids = None

    # Retrieve vector chunks
    relevant_chunks = await search_relevant_chunks(
        db=db,
        query=payload.question,
        organization_id=payload.organizationId,
        document_ids=doc_ids,
        top_k=10
    )

    async def event_generator():
        full_answer = []
        try:
            async for sse_chunk in generate_rag_response_stream(payload.question, relevant_chunks):
                yield sse_chunk
                
                # Accumulate the response text from the SSE chunk
                if sse_chunk.startswith("data: "):
                    data_str = sse_chunk[6:-2]
                    if data_str == "[DONE]":
                        continue
                    try:
                        data_json = json.loads(data_str)
                        if "text" in data_json:
                            full_answer.append(data_json["text"])
                    except Exception:
                        pass
            
            # Persist full response on stream completion
            answer_text = "".join(full_answer).strip()
            if not answer_text:
                answer_text = "I'm sorry, I couldn't find any relevant information in the organization's documents to answer your question."
            
            async with AsyncSessionLocal() as bg_db:
                await crud.create_chat_entry(
                    db=bg_db,
                    organization_id=payload.organizationId,
                    question=payload.question,
                    answer=answer_text
                )
        except asyncio.CancelledError:
            print("Streaming connection cancelled by client.")
            answer_text = "".join(full_answer).strip()
            if answer_text:
                async with AsyncSessionLocal() as bg_db:
                    await crud.create_chat_entry(
                        db=bg_db,
                        organization_id=payload.organizationId,
                        question=payload.question,
                        answer=f"[Cancelled] {answer_text}"
                    )
            raise

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


@router.get("/chat/history/{organization_id}", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    organization_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch all previous chat questions and answers for a specific organization (paginated).
    """
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")

    return await crud.list_chat_history_by_org(
        db=db,
        organization_id=organization_id,
        skip=skip,
        limit=limit
    )
