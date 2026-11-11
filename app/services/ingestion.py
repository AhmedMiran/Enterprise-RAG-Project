import fitz  # PyMuPDF
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.documents import Document, DocumentChunk, DocumentStatus

genai.configure(api_key=settings.GEMINI_API_KEY)

def run_pdf_ingestion(db: Session, document_id: int):
    doc_record = db.query(Document).filter(Document.id == document_id).first()
    if not doc_record:
        return

    doc_record.status = DocumentStatus.PROCESSING
    db.commit()

    try:
        # Step 1: Extract Text using PyMuPDF (sort=True preserves 2-column layout)
        pages_data = []
        pdf_doc = fitz.open(doc_record.file_path)
        for page_num in range(len(pdf_doc)):
            text = pdf_doc[page_num].get_text("text", sort=True)
            if text.strip():
                pages_data.append({"page": page_num + 1, "text": text})
        pdf_doc.close()

        # Step 2: Recursive Chunking (800 chars chunk size for CV sections)
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
        chunks_to_create = []
        chunk_idx = 0

        for p in pages_data:
            for text_chunk in splitter.split_text(p["text"]):
                chunks_to_create.append({
                    "index": chunk_idx,
                    "text": text_chunk,
                    "meta": {"page": p["page"]}
                })
                chunk_idx += 1

        # Fix 1: Guard against empty documents or scanned image PDFs
        if not chunks_to_create:
            doc_record.status = DocumentStatus.COMPLETED
            db.commit()
            return

        # Step 3: Embeddings using Gemini API
        texts = [c["text"] for c in chunks_to_create]

        res = genai.embed_content(
            model="models/gemini-embedding-001",
            content=texts,
            task_type="retrieval_document",
            output_dimensionality=768,
        )
        embeddings = res["embedding"]

        # Step 4: Save to Database with PGVector
        db_chunks = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=c["index"],
                content=c["text"],
                meta_info=c["meta"],
                embedding=embeddings[i]
            )
            for i, c in enumerate(chunks_to_create)
        ]
        db.bulk_save_objects(db_chunks)

        doc_record.status = DocumentStatus.COMPLETED
        db.commit()

    except Exception as e:
        db.rollback()
        doc_record.status = DocumentStatus.FAILED
        doc_record.error_message = str(e)
        db.commit()