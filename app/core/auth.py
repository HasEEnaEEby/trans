from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from app.core.config import settings


security = HTTPBearer(auto_error=False)


def create_jwt(sub: str, expires_minutes: int = 60, admin: bool = False) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "role": "admin" if admin else "user",
        "admin": admin,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing credentials")
    try:
        payload = jwt.decode(
            creds.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user
