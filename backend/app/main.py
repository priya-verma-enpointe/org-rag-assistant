from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api.v1.router import api_router
from app.core.exceptions import EntityNotFoundException, RateLimitException, IngestionException

app = FastAPI(title="Organization Knowledge Assistant API")

# Include v1 routes
app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(EntityNotFoundException)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message}
    )

@app.exception_handler(RateLimitException)
async def rate_limit_handler(request: Request, exc: RateLimitException):
    return JSONResponse(
        status_code=429,
        content={"detail": exc.message}
    )

@app.exception_handler(IngestionException)
async def ingestion_handler(request: Request, exc: IngestionException):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message}
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Enter your API Key to access secure endpoints"
        }
    }
    # Set security on all API v1 endpoints
    for path, path_item in openapi_schema.get("paths", {}).items():
        if path.startswith("/api/v1"):
            for method in path_item:
                path_item[method]["security"] = [{"ApiKeyAuth": []}]
                
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
def root():
    return {"message": "API is running!"}
