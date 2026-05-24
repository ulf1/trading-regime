"""
Global Exception Handling in FastAPI.
How to catch Service Layer exceptions at the Transport (API) layer.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

app = FastAPI()

# --- Custom Service Exceptions ---

class ServiceError(Exception):
    """Base for all services."""
    pass

class ItemNotFoundError(ServiceError):
    """Specifically for missing items."""
    pass

class UnauthorizedActionError(ServiceError):
    """Specifically for security issues."""
    pass


# --- Global Exception Handlers ---

@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    """
    Catch service-level ItemNotFoundError and map to HTTP 404.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "not_found", "message": str(exc)},
    )

@app.exception_handler(UnauthorizedActionError)
async def unauthorized_handler(request: Request, exc: UnauthorizedActionError):
    """
    Catch service-level security errors and map to HTTP 403.
    """
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"error": "forbidden", "message": "You do not have permission to perform this action"},
    )

@app.exception_handler(ServiceError)
async def general_service_handler(request: Request, exc: ServiceError):
    """
    Catch all other service-level errors and map to HTTP 500.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error", "message": "An internal service error occurred"},
    )
