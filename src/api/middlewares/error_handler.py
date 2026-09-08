import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from src.domain.exceptions.base import DomainException

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that transforms exceptions into RFC 7807 Problem Details.
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    
    if isinstance(exc, DomainException):
        # Handle custom domain exceptions
        logger.warning(f"[{correlation_id}] Domain error: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": f"https://example.com/probs/{exc.error_code.lower()}",
                "title": exc.error_code,
                "status": exc.status_code,
                "detail": exc.message,
                "instance": str(request.url),
                "correlation_id": correlation_id
            }
        )

    # Handle unhandled server errors
    logger.error(f"[{correlation_id}] Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://example.com/probs/internal-server-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again later.",
            "instance": str(request.url),
            "correlation_id": correlation_id
        }
    )
