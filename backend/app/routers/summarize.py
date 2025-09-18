from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.llm import summarize_text
from app.services.token_manager import token_manager
from app.dependencies.auth import require_api_key
from app.services.api_key_manager import APIKey


class SummarizeRequest(BaseModel):
    text: str
    level: str = "quick"  # quick | detailed


class SummarizeResponse(BaseModel):
    summary: str


router = APIRouter(prefix="/summarize", tags=["summarize"])


@router.post("", response_model=SummarizeResponse)
def summarize(payload: SummarizeRequest, api_key: APIKey = Depends(require_api_key)):
    # Check text length
    if not token_manager.check_text_length(payload.text):
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum allowed: {token_manager.max_text_length} characters"
        )
    
    # Estimate tokens
    estimated_tokens = token_manager.estimate_tokens(payload.text)
    
    # Check if request is allowed
    can_make_request, error_message = token_manager.can_make_request(estimated_tokens)
    if not can_make_request:
        raise HTTPException(status_code=429, detail=error_message)
    
    result = summarize_text(payload.text, payload.level)
    return SummarizeResponse(summary=result)


