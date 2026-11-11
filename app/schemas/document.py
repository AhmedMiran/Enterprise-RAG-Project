from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
# pyrefly: ignore[missing-import]
from app.models.documents import DocumentStatus

class DocumentCreateResponse(BaseModel):
    document_id: int
    title: str
    status: DocumentStatus
    message: str

class DocumentStatusResponse(BaseModel):
    id: int
    title: str
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True