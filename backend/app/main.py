import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import subtitles, summarize, rag
from app.services.token_manager import token_manager
from app.middleware.rate_limiter import rate_limit_middleware
from app.services.api_key_manager import api_key_manager
from app.services.monitoring import monitoring_service

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
    
    # Check for alerts based on usage
    monitoring_service.check_token_usage(usage_stats)
    
    return usage_stats


@app.post("/usage/reset")
def reset_usage():
    """Reset daily token usage (admin function)"""
    token_manager.reset_daily_usage()
    return {"message": "Daily usage reset successfully"}


@app.get("/api-keys")
def list_api_keys():
    """List all API keys (admin function)"""
    return {"api_keys": api_key_manager.list_api_keys()}


@app.post("/api-keys")
def create_api_key(name: str, permissions: str = "read", 
                  daily_limit: int = None, hourly_limit: int = None,
                  expires_days: int = None):
    """Create a new API key (admin function)"""
    from datetime import datetime, timedelta
    
    expires_at = None
    if expires_days:
        expires_at = datetime.now() + timedelta(days=expires_days)
    
    key = api_key_manager.create_api_key(
        name=name,
        permissions=permissions.split(",") if permissions else ["read"],
        daily_limit=daily_limit,
        hourly_limit=hourly_limit,
        expires_at=expires_at
    )
    
    return {
        "message": "API key created successfully",
        "api_key": key,
        "name": name,
        "permissions": permissions.split(",") if permissions else ["read"],
        "daily_limit": daily_limit,
        "hourly_limit": hourly_limit,
        "expires_at": expires_at.isoformat() if expires_at else None
    }


@app.delete("/api-keys/{key_name}")
def revoke_api_key(key_name: str):
    """Revoke an API key (admin function)"""
    # Find the key by name
    for key, api_key in api_key_manager.api_keys.items():
        if api_key.name == key_name:
            api_key_manager.revoke_api_key(key)
            return {"message": f"API key '{key_name}' revoked successfully"}
    
    raise HTTPException(status_code=404, detail="API key not found")


@app.get("/monitoring/alerts")
def get_alerts(hours: int = 24, level: str = None):
    """Get recent alerts (admin function)"""
    return {
        "alerts": monitoring_service.get_recent_alerts(hours, level),
        "summary": monitoring_service.get_alert_summary(hours)
    }


@app.post("/monitoring/cleanup")
def cleanup_alerts(days: int = 7):
    """Clean up old alerts (admin function)"""
    monitoring_service.cleanup_old_alerts(days)
    return {"message": f"Cleaned up alerts older than {days} days"}


app.include_router(subtitles.router)
app.include_router(summarize.router)
app.include_router(rag.router)


