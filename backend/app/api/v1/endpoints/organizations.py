from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from app.core.security import verify_api_key
from app.core.exceptions import EntityNotFoundException
import app.crud as crud

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate, 
    db: AsyncSession = Depends(get_db)
):
    return await crud.create_organization(db=db, org_in=org_in)


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    return await crud.list_organizations(db=db, skip=skip, limit=limit)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")
    return org


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    org_in: OrganizationUpdate,
    db: AsyncSession = Depends(get_db)
):
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")
    return await crud.update_organization(db=db, db_obj=org, org_in=org_in)


@router.delete("/{organization_id}", status_code=status.HTTP_200_OK)
async def delete_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    org = await crud.get_organization_by_id(db=db, organization_id=organization_id)
    if not org:
        raise EntityNotFoundException("Organization not found")
    
    org_name = org.name
    await crud.delete_organization(db=db, db_obj=org)
    
    return {
        "status": "success",
        "message": f"Organization '{org_name}' (ID: {organization_id}) and all associated documents have been successfully deleted."
    }