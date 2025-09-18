import os
import hashlib
import secrets
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json


class APIKey:
    """Represents an API key with metadata"""
    
    def __init__(self, key: str, name: str, permissions: List[str] = None, 
                 daily_limit: int = None, hourly_limit: int = None, 
                 expires_at: datetime = None, created_at: datetime = None):
        self.key = key
        self.name = name
        self.permissions = permissions or ["read"]
        self.daily_limit = daily_limit
        self.hourly_limit = hourly_limit
        self.expires_at = expires_at
        self.created_at = created_at or datetime.now()
        self.is_active = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "key": self.key,
            "name": self.name,
            "permissions": self.permissions,
            "daily_limit": self.daily_limit,
            "hourly_limit": self.hourly_limit,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "APIKey":
        """Create from dictionary"""
        return cls(
            key=data["key"],
            name=data["name"],
            permissions=data.get("permissions", ["read"]),
            daily_limit=data.get("daily_limit"),
            hourly_limit=data.get("hourly_limit"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            is_active=data.get("is_active", True)
        )
    
    def is_valid(self) -> bool:
        """Check if API key is valid"""
        if not self.is_active:
            return False
        
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        
        return True


class APIKeyManager:
    """Manages API keys for authentication and authorization"""
    
    def __init__(self):
        self.storage_file = os.getenv("API_KEYS_FILE", "data/api_keys.json")
        self.master_key = os.getenv("MASTER_API_KEY")
        self.require_api_key = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"
        
        # Load existing API keys
        self.api_keys: Dict[str, APIKey] = self._load_api_keys()
        
        # Create master key if it doesn't exist
        if self.master_key and "master" not in self.api_keys:
            self.create_api_key(
                name="master",
                permissions=["admin"],
                daily_limit=None,  # Unlimited
                hourly_limit=None,  # Unlimited
                expires_at=None  # Never expires
            )
    
    def _load_api_keys(self) -> Dict[str, APIKey]:
        """Load API keys from storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    return {
                        key: APIKey.from_dict(key_data) 
                        for key, key_data in data.items()
                    }
        except Exception:
            pass
        return {}
    
    def _save_api_keys(self):
        """Save API keys to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump({
                    key: api_key.to_dict() 
                    for key, api_key in self.api_keys.items()
                }, f, indent=2)
        except Exception:
            pass
    
    def generate_api_key(self) -> str:
        """Generate a new API key"""
        # Generate a secure random key
        key = secrets.token_urlsafe(32)
        return f"ytai_{key}"
    
    def create_api_key(self, name: str, permissions: List[str] = None, 
                      daily_limit: int = None, hourly_limit: int = None,
                      expires_at: datetime = None) -> str:
        """Create a new API key"""
        key = self.generate_api_key()
        api_key = APIKey(
            key=key,
            name=name,
            permissions=permissions or ["read"],
            daily_limit=daily_limit,
            hourly_limit=hourly_limit,
            expires_at=expires_at
        )
        
        self.api_keys[key] = api_key
        self._save_api_keys()
        return key
    
    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate an API key and return the APIKey object if valid"""
        if not key:
            return None
        
        # Check if it's the master key from environment
        if self.master_key and key == self.master_key:
            return APIKey(
                key=key,
                name="master",
                permissions=["admin"],
                daily_limit=None,
                hourly_limit=None
            )
        
        # Check stored API keys
        api_key = self.api_keys.get(key)
        if api_key and api_key.is_valid():
            return api_key
        
        return None
    
    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key"""
        if key in self.api_keys:
            self.api_keys[key].is_active = False
            self._save_api_keys()
            return True
        return False
    
    def list_api_keys(self) -> List[Dict]:
        """List all API keys (without exposing the actual keys)"""
        return [
            {
                "name": api_key.name,
                "permissions": api_key.permissions,
                "daily_limit": api_key.daily_limit,
                "hourly_limit": api_key.hourly_limit,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "created_at": api_key.created_at.isoformat(),
                "is_active": api_key.is_active,
                "key_preview": f"{api_key.key[:8]}...{api_key.key[-4:]}" if api_key.key else None
            }
            for api_key in self.api_keys.values()
        ]
    
    def check_permission(self, api_key: APIKey, required_permission: str) -> bool:
        """Check if API key has required permission"""
        if not api_key:
            return False
        
        if "admin" in api_key.permissions:
            return True
        
        return required_permission in api_key.permissions
    
    def get_rate_limits(self, api_key: APIKey) -> Dict[str, int]:
        """Get rate limits for an API key"""
        if not api_key:
            return {
                "daily_limit": int(os.getenv("DAILY_TOKEN_LIMIT", "10000")),
                "hourly_limit": int(os.getenv("HOURLY_TOKEN_LIMIT", "1000"))
            }
        
        return {
            "daily_limit": api_key.daily_limit or int(os.getenv("DAILY_TOKEN_LIMIT", "10000")),
            "hourly_limit": api_key.hourly_limit or int(os.getenv("HOURLY_TOKEN_LIMIT", "1000"))
        }


# Global API key manager instance
api_key_manager = APIKeyManager()
