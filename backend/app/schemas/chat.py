from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Exact JSON payload for POST /chat
class ChatRequest(BaseModel):
    organizationId: int
    question: str
    selectedDocumentIds: Optional[List[int]] = None

# Source attribution citation item
class SourceCitation(BaseModel):
    document: str
    page: Optional[int] = None

# Exact Response structure for POST /chat
class ChatResponse(BaseModel):
    answer: str
    #sources: List[SourceCitation]
    selectedDocumentIds: Optional[List[int]] = None

class ChatHistoryResponse(BaseModel):
    id: int
    organization_id: int
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True    