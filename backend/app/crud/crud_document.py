from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.document import Document, DocumentChunk

async def create_document_metadata(
    db: AsyncSession, 
    organization_id: int, 
    file_name: str, 
    file_type: str,
    status: str = "PENDING"
) -> Document:
    db_obj = Document(
        organization_id=organization_id,
        file_name=file_name,
        file_type=file_type,
        status=status
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_document_by_id(db: AsyncSession, document_id: int, organization_id: int) -> Document | None:
    result = await db.execute(
        select(Document).filter(Document.id == document_id, Document.organization_id == organization_id)
    )
    return result.scalars().first()

async def list_documents_by_org(
    db: AsyncSession, 
    organization_id: int, 
    skip: int = 0, 
    limit: int = 20
) -> list[Document]:
    result = await db.execute(
        select(Document)
        .filter(Document.organization_id == organization_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())

async def update_document_status(
    db: AsyncSession, 
    db_obj: Document, 
    status: str, 
    error_message: str | None = None
) -> Document:
    db_obj.status = status
    db_obj.error_message = error_message
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def bulk_insert_chunks(
    db: AsyncSession, 
    chunks: list[DocumentChunk]
) -> None:
    if chunks:
        db.add_all(chunks)
        await db.commit()

from sqlalchemy import delete

async def delete_document(db: AsyncSession, db_obj: Document) -> Document:
    await db.execute(delete(Document).where(Document.id == db_obj.id))
    await db.commit()
    return db_obj

async def get_document_chunks_count(db: AsyncSession, document_id: int) -> int:
    result = await db.execute(
        select(func.count(DocumentChunk.id)).filter(DocumentChunk.document_id == document_id)
    )
    return result.scalar() or 0
