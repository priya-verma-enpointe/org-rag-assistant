from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Input schema for POST /organizations
class OrganizationCreate(BaseModel):
    name: str

class OrganizationUpdate(BaseModel):
    name: str

# Response schema for GET & POST /organizations
class OrganizationResponse(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows ORM model conversion