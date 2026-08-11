from pydantic import BaseModel
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
    sources: List[SourceCitation]