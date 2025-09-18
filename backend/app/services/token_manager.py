from __future__ import annotations

import os
import time
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class TokenUsage:
    """Track token usage for different operations"""
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    embedding_tokens: int = 0
    last_reset: datetime = None
    hourly_usage: int = 0
    hourly_reset: datetime = None
    
    def __post_init__(self):
        if self.last_reset is None:
            self.last_reset = datetime.now()
        if self.hourly_reset is None:
            self.hourly_reset = datetime.now()


class TokenManager:
    """Manages token usage limits and tracking"""
    
    def __init__(self):
        # Configuration from environment variables
        self.daily_limit = int(os.getenv("DAILY_TOKEN_LIMIT", "1000000"))  # 1M tokens per day (effectively unlimited)
        self.hourly_limit = int(os.getenv("HOURLY_TOKEN_LIMIT", "100000"))  # 100k tokens per hour (effectively unlimited)
        self.request_limit = int(os.getenv("REQUEST_TOKEN_LIMIT", "50000"))  # 50k tokens per request (effectively unlimited)
        self.max_text_length = int(os.getenv("MAX_TEXT_LENGTH", "50000"))  # 50k characters max
        self.max_question_length = int(os.getenv("MAX_QUESTION_LENGTH", "1000"))  # 1k characters max
        
        # Storage file for persistence
        self.storage_file = os.getenv("TOKEN_STORAGE_FILE", "data/token_usage.json")
        self.usage = self._load_usage()
    
    def _load_usage(self) -> TokenUsage:
        """Load usage data from file"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    usage = TokenUsage(
                        total_tokens=data.get('total_tokens', 0),
                        prompt_tokens=data.get('prompt_tokens', 0),
                        completion_tokens=data.get('completion_tokens', 0),
                        embedding_tokens=data.get('embedding_tokens', 0),
                        last_reset=datetime.fromisoformat(data.get('last_reset', datetime.now().isoformat())),
                        hourly_usage=data.get('hourly_usage', 0),
                        hourly_reset=datetime.fromisoformat(data.get('hourly_reset', datetime.now().isoformat()))
                    )
                    # Reset if it's a new day
                    if self._should_reset_daily(usage.last_reset):
                        usage = TokenUsage()
                    # Reset hourly usage if it's been more than an hour
                    elif self._should_reset_hourly(usage.hourly_reset):
                        usage.hourly_usage = 0
                        usage.hourly_reset = datetime.now()
                    return usage
        except Exception:
            pass
        return TokenUsage()
    
    def _save_usage(self):
        """Save usage data to file"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump({
                    'total_tokens': self.usage.total_tokens,
                    'prompt_tokens': self.usage.prompt_tokens,
                    'completion_tokens': self.usage.completion_tokens,
                    'embedding_tokens': self.usage.embedding_tokens,
                    'last_reset': self.usage.last_reset.isoformat(),
                    'hourly_usage': self.usage.hourly_usage,
                    'hourly_reset': self.usage.hourly_reset.isoformat()
                }, f)
        except Exception:
            pass
    
    def _should_reset_daily(self, last_reset: datetime) -> bool:
        """Check if daily usage should be reset"""
        return datetime.now().date() > last_reset.date()
    
    def _should_reset_hourly(self, hourly_reset: datetime) -> bool:
        """Check if hourly usage should be reset"""
        return datetime.now() - hourly_reset > timedelta(hours=1)
    
    def _get_hourly_usage(self) -> int:
        """Get current hourly usage"""
        # Reset hourly usage if it's been more than an hour
        if self._should_reset_hourly(self.usage.hourly_reset):
            self.usage.hourly_usage = 0
            self.usage.hourly_reset = datetime.now()
            # Save the reset to persist the change
            self._save_usage()
        return self.usage.hourly_usage
    
    def check_text_length(self, text: str, operation: str = "general") -> bool:
        """Check if text length is within limits"""
        if operation == "question":
            return len(text) <= self.max_question_length
        return len(text) <= self.max_text_length
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters for English)"""
        return len(text) // 4
    
    def can_make_request(self, estimated_tokens: int, operation: str = "completion") -> tuple[bool, str]:
        """Check if request can be made within limits"""
        # Check daily limit
        if self.usage.total_tokens + estimated_tokens > self.daily_limit:
            return False, f"Daily token limit exceeded ({self.daily_limit}). Current usage: {self.usage.total_tokens}, Request would add: {estimated_tokens}"
        
        # Check hourly limit
        hourly_usage = self._get_hourly_usage()
        if hourly_usage + estimated_tokens > self.hourly_limit:
            return False, f"Hourly token limit exceeded ({self.hourly_limit}). Current hourly usage: {hourly_usage}, Request would add: {estimated_tokens}"
        
        # Check per-request limit
        if estimated_tokens > self.request_limit:
            return False, f"Request token limit exceeded ({self.request_limit}). Estimated tokens: {estimated_tokens}"
        
        return True, ""
    
    def record_usage(self, prompt_tokens: int, completion_tokens: int = 0, embedding_tokens: int = 0):
        """Record actual token usage"""
        total_new_tokens = prompt_tokens + completion_tokens + embedding_tokens
        
        # Check if we need to reset hourly usage first
        if self._should_reset_hourly(self.usage.hourly_reset):
            self.usage.hourly_usage = 0
            self.usage.hourly_reset = datetime.now()
        
        self.usage.prompt_tokens += prompt_tokens
        self.usage.completion_tokens += completion_tokens
        self.usage.embedding_tokens += embedding_tokens
        self.usage.total_tokens += total_new_tokens
        self.usage.hourly_usage += total_new_tokens
        self._save_usage()
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        # Ensure hourly usage is up to date
        hourly_usage = self._get_hourly_usage()
        
        # Save if hourly usage was reset
        if self._should_reset_hourly(self.usage.hourly_reset):
            self._save_usage()
        
        return {
            "total_tokens": self.usage.total_tokens,
            "prompt_tokens": self.usage.prompt_tokens,
            "completion_tokens": self.usage.completion_tokens,
            "embedding_tokens": self.usage.embedding_tokens,
            "hourly_usage": hourly_usage,
            "daily_limit": self.daily_limit,
            "hourly_limit": self.hourly_limit,
            "request_limit": self.request_limit,
            "daily_remaining": max(0, self.daily_limit - self.usage.total_tokens),
            "hourly_remaining": max(0, self.hourly_limit - hourly_usage),
            "last_reset": self.usage.last_reset.isoformat()
        }
    
    def reset_daily_usage(self):
        """Manually reset daily usage (for testing or admin purposes)"""
        self.usage = TokenUsage()
        self._save_usage()


# Global token manager instance
token_manager = TokenManager()
