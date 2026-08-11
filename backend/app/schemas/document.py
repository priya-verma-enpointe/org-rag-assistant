from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Input schema for updating document info
class DocumentUpdate(BaseModel):
    file_name: str

# Response schema for uploaded document info
class DocumentResponse(BaseModel):
    id: int
    organization_id: int
    file_name: str
    file_type: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True