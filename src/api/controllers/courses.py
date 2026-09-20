from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.infrastructure.database.connection import get_db_session
from src.application.dtos.course import CreateCourseDto, UpdateCourseDto, CourseResponseDto
from src.application.dtos.pagination import PaginatedResponse
from src.infrastructure.repositories.course_repository import CourseRepository
from src.domain.exceptions.base import DomainException
import math

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/", response_model=CourseResponseDto, status_code=status.HTTP_201_CREATED)
async def create_course(
    dto: CreateCourseDto, 
    db: AsyncSession = Depends(get_db_session)
):
    repo = CourseRepository(db)
    course = await repo.create(dto.model_dump())
    return course

@router.get("/{id}", response_model=CourseResponseDto)
async def get_course(
    id: int, 
    db: AsyncSession = Depends(get_db_session)
):
    repo = CourseRepository(db)
    course = await repo.get_by_id(id)
    if not course:
        raise DomainException(f"Course with ID {id} not found", status_code=404)
    return course

@router.get("/", response_model=PaginatedResponse[CourseResponseDto])
async def list_courses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_desc: bool = Query(False),
    name: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    is_active: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    repo = CourseRepository(db)
    filters = {"name": name, "level": level, "is_active": is_active}
    # Remove None values
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

@router.put("/{id}", response_model=CourseResponseDto)
async def update_course(
    id: int,
    dto: UpdateCourseDto,
    db: AsyncSession = Depends(get_db_session)
):
    repo = CourseRepository(db)
    course = await repo.update(id, dto.model_dump(exclude_unset=True))
    return course

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    id: int,
    db: AsyncSession = Depends(get_db_session)
):
    repo = CourseRepository(db)
    await repo.soft_delete(id)
