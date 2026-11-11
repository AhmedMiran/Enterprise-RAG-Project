from app.worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.ingestion import run_pdf_ingestion

@celery_app.task(name="process_pdf_task")
def process_pdf_task(document_id: int):
    db = SessionLocal()
    try:
        run_pdf_ingestion(db, document_id)
    finally:
        db.close()