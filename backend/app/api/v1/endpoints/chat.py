from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, SourceCitation
from app.services.retrieval import search_relevant_chunks
from app.services.llm import generate_rag_answer
from app.models.chat import ChatHistory

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_docs(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # UPDATE 1 (Line 18 - 23): Sanitize selectedDocumentIds (Ignore [0] or empty list [])
    doc_ids = getattr(payload, "selectedDocumentIds", None)
    if doc_ids and (doc_ids == [0] or len(doc_ids) == 0):
        doc_ids = None

    # 1. Retrieve vector chunks (with optional @ mention document filtering)
    relevant_chunks = await search_relevant_chunks(
        db=db,
        query=payload.question,
        organization_id=payload.organizationId,
        document_ids=doc_ids,  # Updated parameter pass
        top_k=10
    )

    # 2. Generate answer using Gemini LLM
    answer = await generate_rag_answer(payload.question, relevant_chunks)

    # 3. Format source citations (Only if a valid answer was found in documents)
    sources = []
    
    # Check if answer indicates "no information found"
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

    # 4. Save Chat History to Database
    chat_record = ChatHistory(
        organization_id=payload.organizationId,
        question=payload.question,
        answer=answer
    )
    
    db.add(chat_record)
    await db.commit()
    await db.refresh(chat_record)

    # UPDATE 2 (Line 60): Pass sanitized selectedDocumentIds along with sources to response model
    return ChatResponse(
        answer=answer, 
        sources=sources,
        selectedDocumentIds=doc_ids
    )








'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, SourceCitation
from app.services.retrieval import search_relevant_chunks
from app.services.llm import generate_rag_answer
from app.models.chat import ChatHistory

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_docs(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Retrieve vector chunks (with optional @ mention document filtering)
    relevant_chunks = await search_relevant_chunks(
        db=db,
        query=payload.question,
        organization_id=payload.organizationId,
        document_ids=getattr(payload, "selectedDocumentIds", None),
        top_k=10
    )

    # 2. Generate answer using Gemini LLM
    answer = await generate_rag_answer(payload.question, relevant_chunks)

    # 3. Format source citations (Only if a valid answer was found in documents)
    sources = []
    
    # Check if answer indicates "no information found"
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

    # 4. Save Chat History to Database
    chat_record = ChatHistory(
        organization_id=payload.organizationId,
        question=payload.question,
        answer=answer
    )
    
    db.add(chat_record)
    await db.commit()
    await db.refresh(chat_record)

    return ChatResponse(answer=answer, sources=sources)'''

'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, SourceCitation
from app.services.retrieval import search_relevant_chunks
from app.services.llm import generate_rag_answer
from app.models.chat import ChatHistory

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_docs(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Retrieve vector chunks (with optional @ mention document filtering)
    relevant_chunks = await search_relevant_chunks(
        db=db,
        query=payload.question,
        organization_id=payload.organizationId,
        document_ids=getattr(payload, "selectedDocumentIds", None),
        top_k=10
    )

    # 2. Generate answer using Gemini LLM
    answer = await generate_rag_answer(payload.question, relevant_chunks)

    # 3. Format source citations (Only if a valid answer was found in documents)
    sources = []
    
    # Check if answer indicates "no information found"
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

    return ChatResponse(answer=answer, sources=sources)'''