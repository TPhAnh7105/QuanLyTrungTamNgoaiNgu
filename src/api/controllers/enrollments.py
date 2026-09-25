from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from src.infrastructure.database.connection import get_db_session
from src.application.dtos.enrollment import (
    CreateEnrollmentDto, 
    EnrollmentResponseDto, 
    EnrollmentResultDto,
    UpdateEnrollmentStatusDto
)
from src.application.dtos.pagination import PaginatedResponse
from src.application.services.enrollment_service import EnrollmentService
from src.infrastructure.repositories.enrollment_repository import EnrollmentRepository
from src.domain.exceptions.base import DomainException
from src.domain.entities.user import User
from src.api.dependencies import require_roles, get_current_user

router = APIRouter(prefix="/enrollments", tags=["Enrollments (ACID Transactions)"])

@router.post("/", response_model=EnrollmentResultDto, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    student_id: int = Query(..., description="ID của học viên"),
    course_id: int = Query(..., description="ID của khóa học"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(["Admin", "Teacher"]))
):
    """
    Ghi danh học viên vào khóa học (ACID Transaction).
    Sử dụng Query Parameters thay vì Body.
    Tự động: Khóa khóa học -> Kiểm tra sĩ số -> Tạo Ghi danh -> Sinh Hóa đơn -> Commit.
    Yêu cầu quyền: Admin hoặc Teacher.
    """
    dto = CreateEnrollmentDto(student_id=student_id, course_id=course_id)
    service = EnrollmentService(db)
    result = await service.enroll_student_transaction(dto)
    return result

@router.get("/{id}", response_model=EnrollmentResponseDto)
async def get_enrollment(
    id: int, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Xem chi tiết ghi danh theo ID.
    """
    repo = EnrollmentRepository(db)
    enrollment = await repo.get_by_id(id)
    if not enrollment:
        raise DomainException(f"Enrollment with ID {id} not found", status_code=404)
    return enrollment

@router.get("/", response_model=PaginatedResponse[EnrollmentResponseDto])
async def list_enrollments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách ghi danh có phân trang và lọc.
    """
    repo = EnrollmentRepository(db)
    filters = {"student_id": student_id, "course_id": course_id, "status": status}
    filters = {k: v for k, v in filters.items() if v is not None}
    
    items, total = await repo.get_paginated(
        page=page, 
        size=size, 
        sort_by="created_at", 
        sort_desc=True, 
        **filters
    )
    
    pages = math.ceil(total / size) if size > 0 else 0
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.put("/{id}/status", response_model=EnrollmentResponseDto)
async def update_enrollment_status(
    id: int,
    status: str = Query(..., description="Trạng thái: Active, Completed, Dropped"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(["Admin", "Teacher"]))
):
    """
    Cập nhật trạng thái ghi danh (Active, Completed, Dropped).
    Yêu cầu quyền: Admin hoặc Teacher.
    """
    dto = UpdateEnrollmentStatusDto(status=status)
    repo = EnrollmentRepository(db)
    enrollment = await repo.update(id, {"status": dto.status})
    if not enrollment:
        raise DomainException(f"Enrollment with ID {id} not found", status_code=404)
    return enrollment
