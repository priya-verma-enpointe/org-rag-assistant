import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db, AsyncSessionLocal
from app.core.security import verify_api_key
from app.core.exceptions import EntityNotFoundException
from app.schemas.document import DocumentResponse, DocumentUpdate, DocumentUploadResponse, DocumentStatusResponse
from app.services.ingestion import extract_text_from_file, chunk_document_pages
from app.services.retrieval import get_embeddings_batch
from app.models.document import DocumentChunk
import app.crud as crud

router = APIRouter(dependencies=[Depends(verify_api_key)])

async def process_document_ingestion(
    organization_id: int,
    document_id: int,
    file_bytes: bytes,
    filename: str
):
    """
    Background worker routine to parse documents, chunk text, generate embeddings
    and perform bulk database insertion.
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch document and update status to PROCESSING
            doc = await crud.get_document_by_id(db=db, document_id=document_id, organization_id=organization_id)
            if not doc:
                return
            await crud.update_document_status(db=db, db_obj=doc, status="PROCESSING")

            # 2. Extract text (non-blocking)
            pages_data = await asyncio.to_thread(extract_text_from_file, file_bytes, filename)
            
            # 3. Chunk pages (non-blocking)
            chunks = await asyncio.to_thread(chunk_document_pages, pages_data)
            if not chunks:
                await crud.update_document_status(db=db, db_obj=doc, status="COMPLETED")
                return

            # 4. Generate embeddings (parallel batch calls)
            chunk_contents = [c["content"] for c in chunks]
            embeddings = await get_embeddings_batch(chunk_contents)

            # 5. Create chunk models
            chunk_models = []
            for chunk, embedding_vector in zip(chunks, embeddings):
                chunk_model = DocumentChunk(
                    document_id=document_id,
                    organization_id=organization_id,
                    chunk_content=chunk["content"],
                    page_number=chunk["page"],
                    embedding=embedding_vector
                )
                chunk_models.append(chunk_model)

            # 6. Bulk Insert
            await crud.bulk_insert_chunks(db=db, chunks=chunk_models)

            # 7. Update status to COMPLETED
            await crud.update_document_status(db=db, db_obj=doc, status="COMPLETED")

        except Exception as e:
            # Handle ingestion failures gracefully
            doc = await crud.get_document_by_id(db=db, document_id=document_id, organization_id=organization_id)
            if doc:
                await crud.update_document_status(db=db, db_obj=doc, status="FAILED", error_message=str(e))


@router.post("/{organization_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    organization_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")

    file_bytes = await file.read()
    file_type = file.filename.split(".")[-1].lower()
    if file_type not in ["pdf", "docx", "txt"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_type}")

    # 1. Save Document metadata as PENDING
    doc_model = await crud.create_document_metadata(
        db=db,
        organization_id=organization_id,
        file_name=file.filename,
        file_type=file_type,
        status="PENDING"
    )

    # 2. Add task to background tasks
    background_tasks.add_task(
        process_document_ingestion,
        organization_id=organization_id,
        document_id=doc_model.id,
        file_bytes=file_bytes,
        filename=file.filename
    )

    return DocumentUploadResponse(
        job_id=str(doc_model.id),
        id=doc_model.id,
        status=doc_model.status,
        file_name=doc_model.file_name,
        message="File uploaded successfully. Processing started in the background."
    )


@router.get("/{organization_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    organization_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")

    return await crud.list_documents_by_org(db=db, organization_id=organization_id, skip=skip, limit=limit)


@router.get("/{organization_id}/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    organization_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")

    document = await crud.get_document_by_id(db=db, document_id=document_id, organization_id=organization_id)
    if not document:
        raise EntityNotFoundException("Document not found")

    chunks_count = await crud.get_document_chunks_count(db=db, document_id=document_id)

    return DocumentStatusResponse(
        id=document.id,
        status=document.status,
        error_message=document.error_message,
        chunks_count=chunks_count
    )


@router.get("/{organization_id}/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    organization_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")

    document = await crud.get_document_by_id(db=db, document_id=document_id, organization_id=organization_id)
    if not document:
        raise EntityNotFoundException("Document not found")
    return document


@router.put("/{organization_id}/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    organization_id: int,
    document_id: int,
    doc_in: DocumentUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")

    document = await crud.get_document_by_id(db=db, document_id=document_id, organization_id=organization_id)
    if not document:
        raise EntityNotFoundException("Document not found")

    document.file_name = doc_in.file_name
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.delete("/{organization_id}/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    organization_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")

    document = await crud.get_document_by_id(db=db, document_id=document_id, organization_id=organization_id)
    if not document:
        raise EntityNotFoundException("Document not found")

    file_name = document.file_name
    await crud.delete_document(db=db, db_obj=document)

    return {
        "status": "success",
        "message": f"Document '{file_name}' (ID: {document_id}) has been successfully deleted."
    }