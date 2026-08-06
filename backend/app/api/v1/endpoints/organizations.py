from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_organizations():
    return [{"id": 1, "name": "Acme"}]

@router.post("/")
def create_organization():
    return {"id": 1, "name": "Acme"}