from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate

router = APIRouter()

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate, 
    db: AsyncSession = Depends(get_db)
):
    new_org = Organization(name=org_in.name)
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)
    return new_org


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization))
    organizations = result.scalars().all()
    return organizations


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    org_in: OrganizationUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    org.name = org_in.name
    await db.commit()
    await db.refresh(org)
    return org


'''@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    await db.delete(org)
    await db.commit()
    return None'''

@router.delete("/{organization_id}", status_code=status.HTTP_200_OK)
async def delete_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch organization
    result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    org = result.scalars().first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Organization not found"
        )
    
    org_name = org.name  

    
    await db.delete(org)
    await db.commit()
    
    # 3. Explicit JSON Response
    return {
        "status": "success",
        "message": f"Organization '{org_name}' (ID: {organization_id}) and all associated documents have been successfully deleted."
    }