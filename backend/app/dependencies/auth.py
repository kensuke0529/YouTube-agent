from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.api_key_manager import api_key_manager, APIKey

# Security scheme for API key authentication
security = HTTPBearer(auto_error=False)


async def get_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[APIKey]:
    """Extract and validate API key from request"""
    
    # If API key is not required, return None
    if not api_key_manager.require_api_key:
        return None
    
    # Try to get API key from Authorization header
    api_key = None
    if credentials:
        api_key = credentials.credentials
    else:
        # Try to get from X-API-Key header
        api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide it via Authorization header (Bearer token) or X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate the API key
    validated_key = api_key_manager.validate_api_key(api_key)
    if not validated_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return validated_key


async def require_api_key(api_key: Optional[APIKey] = Depends(get_api_key)) -> APIKey:
    """Require a valid API key"""
    if api_key_manager.require_api_key and not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key


async def require_permission(permission: str):
    """Create a dependency that requires a specific permission"""
    async def _require_permission(api_key: Optional[APIKey] = Depends(get_api_key)) -> APIKey:
        if api_key_manager.require_api_key:
            if not api_key:
                raise HTTPException(
                    status_code=401,
                    detail="API key required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not api_key_manager.check_permission(api_key, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission '{permission}' required",
                )
        
        return api_key
    
    return _require_permission


async def require_admin(api_key: Optional[APIKey] = Depends(get_api_key)) -> APIKey:
    """Require admin permissions"""
    if api_key_manager.require_api_key:
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not api_key_manager.check_permission(api_key, "admin"):
            raise HTTPException(
                status_code=403,
                detail="Admin permissions required",
            )
    
    return api_key
