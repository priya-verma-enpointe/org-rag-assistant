from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate

async def create_organization(db: AsyncSession, org_in: OrganizationCreate) -> Organization:
    db_obj = Organization(name=org_in.name)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_organization_by_id(db: AsyncSession, organization_id: int) -> Organization | None:
    result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    return result.scalars().first()

async def list_organizations(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Organization]:
    result = await db.execute(select(Organization).offset(skip).limit(limit))
    return list(result.scalars().all())

async def update_organization(db: AsyncSession, db_obj: Organization, org_in: OrganizationUpdate) -> Organization:
    db_obj.name = org_in.name
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

from sqlalchemy import delete

async def delete_organization(db: AsyncSession, db_obj: Organization) -> Organization:
    await db.execute(delete(Organization).where(Organization.id == db_obj.id))
    await db.commit()
    return db_obj
