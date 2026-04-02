from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings
from app.database import supabase
from app.exceptions import AppError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expires_in),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def register(email: str, password: str, name: str) -> dict:
    # Check if email already exists
    existing = (
        supabase.table("users")
        .select("id")
        .eq("email", email)
        .execute()
    )
    if existing.data:
        raise AppError(409, "Email already registered")

    hashed = hash_password(password)

    response = (
        supabase.table("users")
        .insert({
            "email": email,
            "password": hashed,
            "name": name,
            "role": "viewer",
        })
        .execute()
    )

    user = response.data[0]
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "is_active": user["is_active"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


def login(email: str, password: str) -> dict:
    response = (
        supabase.table("users")
        .select("*")
        .eq("email", email)
        .execute()
    )

    if not response.data:
        raise AppError(401, "Invalid email or password")

    user = response.data[0]

    if not user["is_active"]:
        raise AppError(403, "Account is deactivated")

    if not verify_password(password, user["password"]):
        raise AppError(401, "Invalid email or password")

    token = create_token(user["id"], user["role"])

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        },
    }
