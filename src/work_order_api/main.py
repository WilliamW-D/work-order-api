from fastapi import FastAPI

app = FastAPI(
    title="Work Order Management API",
    description=(
        "Backend API for managing equipment, "
        "maintenance work orders, and service history."
    ),
    version="0.1.0",
)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Work Order Management API"
    }

@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy"
    }
