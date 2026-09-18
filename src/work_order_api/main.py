from fastapi import (
    FastAPI,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError

from work_order_api.config import settings
from work_order_api.database import (
    check_database_connection,
)
from work_order_api.routers import (
    auth,
    users,
)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend API for managing equipment, "
        "maintenance work orders, and service history."
    ),
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": settings.app_name,
    }

@app.get("/health")
def health_check() -> dict[str, str]:
    try:
        check_database_connection()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable.",
        ) from exc
    
    return {
        "status": "healthy",
        "database": "connected",
    }
