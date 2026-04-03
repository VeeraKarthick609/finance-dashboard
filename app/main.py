from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import AppError, app_error_handler, generic_error_handler
from app.routers import auth, users, records, dashboard, reports

app = FastAPI(
    title="Finance Dashboard API",
    description="Backend for a finance dashboard with role-based access control",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(records.router, prefix="/api/records", tags=["Records"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


@app.get("/")
async def root():
    return {"success": True, "message": "Finance Dashboard API"}


@app.get("/health")
async def health():
    return {"success": True, "message": "OK"}
