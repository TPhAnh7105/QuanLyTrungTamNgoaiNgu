import traceback
from http import HTTPStatus
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from loguru import logger
from src.domain.exceptions.base import DomainException

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that transforms all exceptions (Domain, HTTP 405, 404, 422, DB Integrity, 500)
    into standard RFC 7807 Problem Details format.
    """
    correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID", "unknown")

    # 1. Custom Domain Exceptions
    if isinstance(exc, DomainException):
        logger.warning(f"[{correlation_id}] Domain error: {exc.message} (Code: {exc.error_code}, Status: {exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": f"https://example.com/probs/{exc.error_code.lower().replace('_', '-')}",
                "title": exc.error_code,
                "status": exc.status_code,
                "detail": exc.message,
                "instance": str(request.url),
                "correlation_id": correlation_id
            }
        )

    # 2. Database Integrity Errors (Unique constraint, Foreign key violation)
    if isinstance(exc, IntegrityError):
        error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        logger.warning(f"[{correlation_id}] Database Integrity Error: {error_msg}")
        
        if "Duplicate entry" in error_msg or "UNIQUE constraint" in error_msg:
            title = "Duplicate Record Conflict"
            detail = "Bản ghi với khóa định danh duy nhất (ví dụ: email hoặc user_id) đã tồn tại trong hệ thống."
            status_code = 409
            type_url = "https://example.com/probs/duplicate-record"
        elif "foreign key constraint" in error_msg.lower() or "FOREIGN KEY" in error_msg:
            title = "Foreign Key Reference Error"
            detail = "Khóa ngoại liên kết (ví dụ: user_id) không tồn tại trong cơ sở dữ liệu."
            status_code = 400
            type_url = "https://example.com/probs/foreign-key-violation"
        else:
            title = "Data Integrity Violation"
            detail = "Dữ liệu vi phạm ràng buộc toàn vẹn của cơ sở dữ liệu."
            status_code = 400
            type_url = "https://example.com/probs/data-integrity-violation"

        return JSONResponse(
            status_code=status_code,
            content={
                "type": type_url,
                "title": title,
                "status": status_code,
                "detail": detail,
                "instance": str(request.url),
                "correlation_id": correlation_id
            }
        )

    # 3. HTTP Exceptions (405 Method Not Allowed, 404 Not Found, 401, 403, etc.)
    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        status_phrase = HTTPStatus(status_code).phrase if status_code in HTTPStatus.__members__.values() else "HTTP Error"
        
        # Specific formatting for 405 Method Not Allowed
        if status_code == 405:
            detail = f"Method '{request.method}' is not allowed for endpoint '{request.url.path}'."
            title = "Method Not Allowed"
            type_url = "https://example.com/probs/method-not-allowed"
        elif status_code == 404:
            detail = f"Resource not found at '{request.url.path}'."
            title = "Not Found"
            type_url = "https://example.com/probs/not-found"
        else:
            detail = str(exc.detail) if exc.detail else status_phrase
            title = status_phrase
            type_url = f"https://example.com/probs/{title.lower().replace(' ', '-')}"

        logger.warning(f"[{correlation_id}] HTTP {status_code} {title}: {detail}")
        return JSONResponse(
            status_code=status_code,
            headers=getattr(exc, "headers", None),
            content={
                "type": type_url,
                "title": title,
                "status": status_code,
                "detail": detail,
                "instance": str(request.url),
                "correlation_id": correlation_id
            }
        )

    # 4. Request Validation Errors (422 Unprocessable Entity)
    if isinstance(exc, RequestValidationError):
        logger.warning(f"[{correlation_id}] Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "type": "https://example.com/probs/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "Dữ liệu gửi lên không đúng định dạng hoặc thiếu trường bắt buộc.",
                "errors": exc.errors(),
                "instance": str(request.url),
                "correlation_id": correlation_id
            }
        )

    # 5. Unhandled Internal Server Errors (500)
    logger.error(f"[{correlation_id}] Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://example.com/probs/internal-server-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred on the server. Please try again later.",
            "instance": str(request.url),
            "correlation_id": correlation_id
        }
    )
