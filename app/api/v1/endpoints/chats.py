from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import google.generativeai as genai
from pydantic import BaseModel
from app.core.database import get_db
from app.core.config import settings
from app.models.documents import DocumentChunk

router = APIRouter()
genai.configure(api_key=settings.GEMINI_API_KEY)

class ChatRequest(BaseModel):
    query: str

async def generate_rag_response(query: str, db: Session):
    # 1. Embed incoming search query
    emb_res = await genai.embed_content_async(
        model="models/gemini-embedding-001",
        content=query,
        task_type="retrieval_query",
        output_dimensionality=768,
    )
    query_vector = emb_res["embedding"]

    # 2. Vector search in Postgres using CosineDistance
    top_chunks = (
        db.query(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(5)
        .all()
    )

    context = "\n\n".join([f"Page {c.meta_info.get('page')}: {c.content}" for c in top_chunks])

    # 3. Initialize Gemini Model with System Instruction
    model = genai.GenerativeModel(
        model_name="gemini-3.8-flash",
        system_instruction=f"Answer question based on context below:\n{context}"
    )

    # 4. Stream tokens asynchronously
    response = await model.generate_content_async(query, stream=True)

    async for chunk in response:
        if chunk.text:
            yield f"data: {chunk.text}\n\n"

@router.post("/stream")
def stream_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    return StreamingResponse(
        generate_rag_response(payload.query, db),
        media_type="text/event-stream"
    )