from fastapi import APIRouter
from app.api.v1.endpoints import organizations, documents, chat

api_router = APIRouter()

api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(documents.router, tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])