from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, message: str, errors: list | None = None):
        self.status_code = status_code
        self.message = message
        self.errors = errors


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    body = {"success": False, "message": exc.message}
    if exc.errors:
        body["errors"] = exc.errors
    return JSONResponse(status_code=exc.status_code, content=body)


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"},
    )
