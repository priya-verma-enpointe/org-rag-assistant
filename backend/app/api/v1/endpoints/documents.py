from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.organization import Organization
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentResponse, DocumentUpdate
from app.services.ingestion import extract_text_from_file, chunk_document_pages
from app.services.retrieval import get_embeddings_batch

router = APIRouter()

@router.post("/{organization_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    organization_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = org_result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Read and parse file
    file_bytes = await file.read()
    file_type = file.filename.split(".")[-1].lower()

    try:
        pages_data = extract_text_from_file(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parsing error: {str(e)}")

    # 1. Save Document metadata
    doc_model = Document(
        organization_id=organization_id,
        file_name=file.filename,
        file_type=file_type
    )
    db.add(doc_model)
    await db.commit()
    await db.refresh(doc_model)

    # 2. Chunk text and create embeddings in batch
    chunks = chunk_document_pages(pages_data)
    chunk_contents = [chunk["content"] for chunk in chunks]
    embeddings = await get_embeddings_batch(chunk_contents)
    
    for chunk, embedding_vector in zip(chunks, embeddings):
        chunk_model = DocumentChunk(
            document_id=doc_model.id,
            organization_id=organization_id,
            chunk_content=chunk["content"],
            page_number=chunk["page"],
            embedding=embedding_vector
        )
        db.add(chunk_model)

    await db.commit()
    return doc_model


@router.get("/{organization_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = org_result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    result = await db.execute(
        select(Document)
        .filter(Document.organization_id == organization_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return documents


@router.get("/{organization_id}/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    organization_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = org_result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    result = await db.execute(
        select(Document)
        .filter(Document.id == document_id, Document.organization_id == organization_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/{organization_id}/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    organization_id: int,
    document_id: int,
    doc_in: DocumentUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = org_result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    result = await db.execute(
        select(Document)
        .filter(Document.id == document_id, Document.organization_id == organization_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.file_name = doc_in.file_name
    await db.commit()
    await db.refresh(document)
    return document


'''@router.delete("/{organization_id}/documents/{document_id}",status_code=status.HTTP_200_OK)
async def delete_document(
    organization_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = org_result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    result = await db.execute(
        select(Document)
        .filter(Document.id == document_id, Document.organization_id == organization_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(document)
    await db.commit()
    return None

    return {
        "status": "success",
        "message": f"Document '{file_name}' (ID: {document_id}) has been successfully deleted."
    }'''

@router.delete("/{organization_id}/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    organization_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Check if organization exists
    org_result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = org_result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Fetch document
    result = await db.execute(
        select(Document)
        .filter(Document.id == document_id, Document.organization_id == organization_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    
    file_name = document.file_name

    # Delete document from DB
    await db.delete(document)
    await db.commit()

    
    return {
        "status": "success",
        "message": f"Document '{file_name}' (ID: {document_id}) has been successfully deleted."
    }