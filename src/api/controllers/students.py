from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from src.infrastructure.database.connection import get_db_session
from src.application.dtos.student import CreateStudentDto, UpdateStudentDto, StudentResponseDto
from src.application.dtos.pagination import PaginatedResponse
from src.infrastructure.repositories.student_repository import StudentRepository
from src.domain.exceptions.base import DomainException
from src.domain.entities.user import User
from src.api.dependencies import require_roles

router = APIRouter(prefix="/students", tags=["Students"])

@router.post("/", response_model=StudentResponseDto, status_code=status.HTTP_201_CREATED)
async def create_student(
    dto: CreateStudentDto, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(["Admin", "Teacher"]))
):
    """
    Tạo hồ sơ học viên mới (Yêu cầu quyền: Admin hoặc Teacher).
    """
    repo = StudentRepository(db)
    student = await repo.create(dto.model_dump())
    return student

@router.get("/{id}", response_model=StudentResponseDto)
async def get_student(
    id: int, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Xem chi tiết hồ sơ học viên theo ID.
    """
    repo = StudentRepository(db)
    student = await repo.get_by_id(id)
    if not student:
        raise DomainException(f"Student with ID {id} not found", status_code=404)
    return student

@router.get("/", response_model=PaginatedResponse[StudentResponseDto])
async def list_students(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_desc: bool = Query(False),
    full_name: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    parental_support: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Lấy danh sách học viên có phân trang, lọc và sắp xếp.
    """
    repo = StudentRepository(db)
    filters = {"full_name": full_name, "phone": phone, "parental_support": parental_support}
    filters = {k: v for k, v in filters.items() if v is not None}
    
    items, total = await repo.get_paginated(
        page=page, 
        size=size, 
        sort_by=sort_by, 
        sort_desc=sort_desc, 
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

@router.put("/{id}", response_model=StudentResponseDto)
async def update_student(
    id: int,
    dto: UpdateStudentDto,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(["Admin", "Teacher", "Student"]))
):
    """
    Cập nhật thông tin học viên (Yêu cầu quyền: Admin, Teacher hoặc chính Student).
    """
    repo = StudentRepository(db)
    student = await repo.update(id, dto.model_dump(exclude_unset=True))
    return student

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(["Admin"]))
):
    """
    Xóa mềm học viên (Yêu cầu quyền: Admin).
    """
    repo = StudentRepository(db)
    await repo.soft_delete(id)
