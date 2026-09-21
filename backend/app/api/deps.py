from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.orm import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_ownership(resource, user: User | None) -> None:
    """Enforce that a resource with an owner can only be accessed by that
    owner. A resource created anonymously (owner_id is None) stays
    accessible to anyone holding its ID, matching the optional-auth model
    used throughout the API — only OWNED resources are access-controlled."""
    owner_id = getattr(resource, "owner_id", None)
    if owner_id is None:
        return
    if user is None or user.id != owner_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this resource.")


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        return None
    return db.get(User, user_id)
