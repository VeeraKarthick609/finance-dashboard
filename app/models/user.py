from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# --- Request schemas ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UpdateUserRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    role: str | None = Field(None, pattern=r"^(viewer|analyst|admin)$")
    is_active: bool | None = None


# --- Response schemas ---

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str


class UserListResponse(BaseModel):
    success: bool = True
    data: list[UserResponse]
    meta: dict
