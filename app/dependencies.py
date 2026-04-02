from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.config import settings
from app.database import supabase
from app.exceptions import AppError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Extract and verify JWT token, return user dict."""
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        raise AppError(401, "Token has expired")
    except jwt.InvalidTokenError:
        raise AppError(401, "Invalid token")

    user_id = payload.get("user_id")
    if not user_id:
        raise AppError(401, "Invalid token payload")

    response = (
        supabase.table("users")
        .select("id, email, name, role, is_active")
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        raise AppError(401, "User not found")

    user = response.data
    if not user["is_active"]:
        raise AppError(403, "Account is deactivated")

    return user


def require_role(*allowed_roles: str):
    """Dependency factory that checks if the current user has one of the allowed roles."""

    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise AppError(403, "Insufficient permissions")
        return current_user

    return role_checker
