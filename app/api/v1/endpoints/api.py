from fastapi import APIRouter
from app.api.v1.endpoints import documents, chats

# 1. Create the master router for v1
api_router = APIRouter()

# 2. Attach individual routers with their respective prefixes and documentation tags
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

api_router.include_router(
    chats.router,
    prefix="/chats",
    tags=["chats"]
)