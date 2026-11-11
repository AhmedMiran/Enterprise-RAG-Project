import shutil
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.documents import Document, DocumentStatus
from app.schemas.document import DocumentCreateResponse
from app.worker.tasks import process_pdf_task

router = APIRouter()
UPLOAD_DIR = "./uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = Document(title=file.filename, file_path=file_path.replace("\\", "/"), status=DocumentStatus.PENDING)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Offload to Celery
    process_pdf_task.delay(doc.id)

    return {
        "document_id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "message": "File upload accepted. Ingestion process running in background."
    }