from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat import ChatHistory

async def create_chat_entry(
    db: AsyncSession, 
    organization_id: int, 
    question: str, 
    answer: str
) -> ChatHistory:
    db_obj = ChatHistory(
        organization_id=organization_id,
        question=question,
        answer=answer
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def list_chat_history_by_org(
    db: AsyncSession, 
    organization_id: int, 
    skip: int = 0, 
    limit: int = 20
) -> list[ChatHistory]:
    result = await db.execute(
        select(ChatHistory)
        .filter(ChatHistory.organization_id == organization_id)
        .order_by(ChatHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
