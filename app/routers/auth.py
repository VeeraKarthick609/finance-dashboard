from fastapi import APIRouter

from app.models.user import RegisterRequest, LoginRequest
from app.services import auth_service

router = APIRouter()


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    user = auth_service.register(body.email, body.password, body.name)
    return {"success": True, "data": user}


@router.post("/login")
async def login(body: LoginRequest):
    result = auth_service.login(body.email, body.password)
    return {"success": True, "data": result}
