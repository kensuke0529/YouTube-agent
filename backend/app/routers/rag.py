from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.llm import embed_texts, ask_question_with_context
from app.services.vectorstore import FaissStore
from app.services.token_manager import token_manager
from app.dependencies.auth import require_api_key
from app.services.api_key_manager import APIKey


INDEX_PATH = os.getenv("INDEX_PATH", "data/faiss.index")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))


class IngestRequest(BaseModel):
    chunks: List[str]
    video_id: str
    video_info: dict


class IngestResponse(BaseModel):
    count: int
    duplicates_skipped: int


class QuestionRequest(BaseModel):
    question: str


class Source(BaseModel):
    text: str
    score: float
    metadata: dict


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Source]


router = APIRouter(prefix="/rag", tags=["rag"])


def _store() -> FaissStore:
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    return FaissStore(dim=EMBEDDING_DIM, index_path=INDEX_PATH)


@router.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest):
    store = _store()
    
    # Check for duplicates before generating embeddings
    new_chunks = []
    new_metas = []
    for i, chunk in enumerate(payload.chunks):
        if chunk not in store.texts:
            new_chunks.append(chunk)
            new_metas.append({
                "video_id": payload.video_id, 
                "chunk": i,
                "video_title": payload.video_info.get("title", "Unknown Title"),
                "video_url": payload.video_info.get("url", ""),
                "uploader": payload.video_info.get("uploader", "Unknown")
            })
    
    duplicates_skipped = len(payload.chunks) - len(new_chunks)
    
    if new_chunks:
        # Only generate embeddings for new chunks
        vectors = embed_texts(new_chunks)
        added_count = store.add_texts(vectors, new_chunks, new_metas)
    else:
        added_count = 0
    
    return IngestResponse(count=added_count, duplicates_skipped=duplicates_skipped)


@router.post("/ask", response_model=AnswerResponse)
def ask(payload: QuestionRequest, api_key: APIKey = Depends(require_api_key)):
    # Question length check removed - no restrictions
    
    # Estimate tokens for the question
    estimated_tokens = token_manager.estimate_tokens(payload.question) + 1000  # Add buffer for context
    
    # Check if request is allowed
    can_make_request, error_message = token_manager.can_make_request(estimated_tokens)
    if not can_make_request:
        raise HTTPException(status_code=429, detail=error_message)
    
    store = _store()
    [q_vec] = embed_texts([payload.question])
    results = store.search(q_vec, top_k=5)

    context = "\n\n".join([f"Source {i+1}: {t}" for i, (t, _s, _m) in enumerate(results)])
    
    # Use the new token-managed function
    answer, prompt_tokens, completion_tokens = ask_question_with_context(payload.question, context)
    
    sources = [
        Source(text=t, score=s, metadata=m) for t, s, m in results
    ]
    return AnswerResponse(answer=answer, sources=sources)


