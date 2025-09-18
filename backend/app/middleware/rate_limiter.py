import os
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import hashlib


class RateLimiter:
    """Simple in-memory rate limiter for Railway/Vercel deployment"""
    
    def __init__(self):
        # Rate limiting configuration
        self.requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.requests_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
        self.requests_per_day = int(os.getenv("RATE_LIMIT_PER_DAY", "10000"))
        
        # In-memory storage (will reset on deployment restart)
        self.request_counts: Dict[str, Dict[str, int]] = {}
        self.request_timestamps: Dict[str, Dict[str, float]] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _cleanup_old_entries(self, client_id: str):
        """Clean up old entries to prevent memory leaks"""
        current_time = time.time()
        
        # Clean up minute-level entries older than 1 minute
        if "minute" in self.request_timestamps.get(client_id, {}):
            if current_time - self.request_timestamps[client_id]["minute"] > 60:
                self.request_counts[client_id]["minute"] = 0
                self.request_timestamps[client_id]["minute"] = current_time
        
        # Clean up hour-level entries older than 1 hour
        if "hour" in self.request_timestamps.get(client_id, {}):
            if current_time - self.request_timestamps[client_id]["hour"] > 3600:
                self.request_counts[client_id]["hour"] = 0
                self.request_timestamps[client_id]["hour"] = current_time
        
        # Clean up day-level entries older than 1 day
        if "day" in self.request_timestamps.get(client_id, {}):
            if current_time - self.request_timestamps[client_id]["day"] > 86400:
                self.request_counts[client_id]["day"] = 0
                self.request_timestamps[client_id]["day"] = current_time
    
    def is_allowed(self, request: Request) -> tuple[bool, str]:
        """Check if request is allowed based on rate limits"""
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Initialize client data if not exists
        if client_id not in self.request_counts:
            self.request_counts[client_id] = {"minute": 0, "hour": 0, "day": 0}
            self.request_timestamps[client_id] = {"minute": current_time, "hour": current_time, "day": current_time}
        
        # Clean up old entries
        self._cleanup_old_entries(client_id)
        
        # Check minute limit
        if self.request_counts[client_id]["minute"] >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        # Check hour limit
        if self.request_counts[client_id]["hour"] >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Check day limit
        if self.request_counts[client_id]["day"] >= self.requests_per_day:
            return False, f"Rate limit exceeded: {self.requests_per_day} requests per day"
        
        # Increment counters
        self.request_counts[client_id]["minute"] += 1
        self.request_counts[client_id]["hour"] += 1
        self.request_counts[client_id]["day"] += 1
        
        return True, ""
    
    def get_remaining_requests(self, request: Request) -> Dict[str, int]:
        """Get remaining requests for client"""
        client_id = self._get_client_id(request)
        
        if client_id not in self.request_counts:
            return {
                "minute": self.requests_per_minute,
                "hour": self.requests_per_hour,
                "day": self.requests_per_day
            }
        
        self._cleanup_old_entries(client_id)
        
        return {
            "minute": max(0, self.requests_per_minute - self.request_counts[client_id]["minute"]),
            "hour": max(0, self.requests_per_hour - self.request_counts[client_id]["hour"]),
            "day": max(0, self.requests_per_day - self.request_counts[client_id]["day"])
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    # Skip rate limiting for health checks and usage endpoints
    if request.url.path in ["/health", "/usage", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    is_allowed, error_message = rate_limiter.is_allowed(request)
    
    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": error_message,
                "remaining": rate_limiter.get_remaining_requests(request)
            },
            headers={
                "Retry-After": "60",  # Retry after 60 seconds
                "X-RateLimit-Limit": str(rate_limiter.requests_per_minute),
                "X-RateLimit-Remaining": str(rate_limiter.get_remaining_requests(request)["minute"]),
                "X-RateLimit-Reset": str(int(time.time()) + 60)
            }
        )
    
    response = await call_next(request)
    
    # Add rate limit headers to response
    remaining = rate_limiter.get_remaining_requests(request)
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining["minute"])
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    return response
