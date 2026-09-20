from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.infrastructure.database.connection import get_db_session
from src.application.dtos.teacher import CreateTeacherDto, UpdateTeacherDto, TeacherResponseDto
from src.application.dtos.pagination import PaginatedResponse
from src.infrastructure.repositories.teacher_repository import TeacherRepository
from src.domain.exceptions.base import DomainException
import math

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.post("/", response_model=TeacherResponseDto, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    dto: CreateTeacherDto, 
    db: AsyncSession = Depends(get_db_session)
):
    repo = TeacherRepository(db)
    teacher = await repo.create(dto.model_dump())
    return teacher

@router.get("/{id}", response_model=TeacherResponseDto)
async def get_teacher(
    id: int, 
    db: AsyncSession = Depends(get_db_session)
):
    repo = TeacherRepository(db)
    teacher = await repo.get_by_id(id)
    if not teacher:
        raise DomainException(f"Teacher with ID {id} not found", status_code=404)
    return teacher

@router.get("/", response_model=PaginatedResponse[TeacherResponseDto])
async def list_teachers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_desc: bool = Query(False),
    full_name: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    repo = TeacherRepository(db)
    filters = {"full_name": full_name, "specialization": specialization}
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

@router.put("/{id}", response_model=TeacherResponseDto)
async def update_teacher(
    id: int,
    dto: UpdateTeacherDto,
    db: AsyncSession = Depends(get_db_session)
):
    repo = TeacherRepository(db)
    teacher = await repo.update(id, dto.model_dump(exclude_unset=True))
    return teacher

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    id: int,
    db: AsyncSession = Depends(get_db_session)
):
    repo = TeacherRepository(db)
    await repo.soft_delete(id)
