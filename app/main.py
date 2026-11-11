from fastapi import FastAPI
from app.api.v1.endpoints.api import api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "healthy", "engine": "FastAPI RAG Backend"}