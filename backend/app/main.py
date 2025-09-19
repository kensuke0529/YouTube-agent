import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import subtitles, rag
from app.services.token_manager import token_manager
from app.middleware.rate_limiter import rate_limit_middleware

load_dotenv()

app = FastAPI(title="YouTube Learning AI API", version="0.1.0")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/usage")
def get_usage():
    """Get current token usage statistics"""
    usage_stats = token_manager.get_usage_stats()
    
    
    return usage_stats




app.include_router(subtitles.router)
app.include_router(rag.router)


