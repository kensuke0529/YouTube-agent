from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl

from app.services.subtitles import get_subtitles_text, get_video_info
from app.services.llm import summarize_text
from app.services.token_manager import token_manager
from app.dependencies.auth import require_api_key
from app.services.api_key_manager import APIKey


class SubtitlesRequest(BaseModel):
    url: HttpUrl
    language_code: str = "en"


class SubtitlesResponse(BaseModel):
    text: str
    video_info: dict


class ExtractAndSummarizeRequest(BaseModel):
    url: HttpUrl
    language_code: str = "en"
    level: str = "quick"  # quick | detailed


class ExtractAndSummarizeResponse(BaseModel):
    text: str
    video_info: dict
    summary: str


router = APIRouter(prefix="/subtitles", tags=["subtitles"])


@router.post("/extract", response_model=SubtitlesResponse)
def extract_subtitles(payload: SubtitlesRequest, api_key: APIKey = Depends(require_api_key)):
    try:
        text = get_subtitles_text(str(payload.url), payload.language_code)
        video_info = get_video_info(str(payload.url))
        return SubtitlesResponse(text=text, video_info=video_info)
    except Exception as e:  # noqa: BLE001 - return as 400 for client errors
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/extract-and-summarize", response_model=ExtractAndSummarizeResponse)
def extract_and_summarize(payload: ExtractAndSummarizeRequest, api_key: APIKey = Depends(require_api_key)):
    """Extract subtitles and summarize in one optimized operation"""
    try:
        # Step 1: Extract subtitles
        text = get_subtitles_text(str(payload.url), payload.language_code)
        video_info = get_video_info(str(payload.url))
        
        # Step 2: Check text length and estimate tokens
        if not token_manager.check_text_length(text):
            raise HTTPException(
                status_code=400,
                detail=f"Transcript too long. Maximum allowed: {token_manager.max_text_length} characters"
            )
        
        estimated_tokens = token_manager.estimate_tokens(text) + 500  # Add buffer for prompt and response
        
        # Step 3: Check if request is allowed
        can_make_request, error_message = token_manager.can_make_request(estimated_tokens)
        if not can_make_request:
            raise HTTPException(status_code=429, detail=error_message)
        
        # Step 4: Generate summary
        summary = summarize_text(text, payload.level)
        
        return ExtractAndSummarizeResponse(
            text=text,
            video_info=video_info,
            summary=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract and summarize: {str(e)}") from e


