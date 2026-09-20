import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from loguru import logger

from src.api.middlewares.error_handler import global_exception_handler
from src.domain.entities.course import Course
from src.domain.entities.student import Student
from src.domain.entities.teacher import Teacher
from src.domain.entities.user import User
from src.domain.exceptions.base import DomainException
from src.infrastructure.database.connection import Base, engine


# Lifespan context manager replacing deprecated @app.on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Application started and Database initialized.")

    yield

    # Shutdown: Cleanly dispose of the DB engine connection pool
    await engine.dispose()
    logger.info("Application shutdown and DB connection closed.")


# Initialize FastAPI app
app = FastAPI(
    title="Smart Language Center Management System",
    description="Clean Architecture API with FastAPI, SQLAlchemy Core, and AI integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(DomainException, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


# Middleware for Correlation ID and Timing
@app.middleware("http")
async def add_correlation_id_and_timing_middleware(request: Request, call_next):
    # Extract or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    # Safely attach correlation ID to ASGI request scope headers
    headers = [
        (k, v) for k, v in request.scope.get("headers", []) if k.lower() != b"x-correlation-id"
    ]
    headers.append((b"x-correlation-id", correlation_id.encode("utf-8")))
    request.scope["headers"] = headers

    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        raise exc
    finally:
        process_time = time.time() - start_time

    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    logger.info(
        f"[{correlation_id}] {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Time: {process_time:.4f}s"
    )

    return response


@app.get("/")
async def root():
    return {"message": "Welcome to the Smart Language Center Management System API"}

from src.api.controllers import courses, students, teachers

app.include_router(courses.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(teachers.router, prefix="/api/v1")
