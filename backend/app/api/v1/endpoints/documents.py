from fastapi import APIRouter

router = APIRouter()

@router.get("/organizations/{id}/documents")
def get_documents(id: int):
    return []

@router.post("/organizations/{id}/documents")
def upload_document(id: int):
    return {"message": "Document uploaded successfully"}