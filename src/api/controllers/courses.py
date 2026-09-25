from fastapi import APIRouter, Header, Query, status
from sqlalchemy import text
from typing import Optional
import math

from src.infrastructure.database.connection import AsyncSessionLocal
from src.application.dtos.course import CreateCourseDto, UpdateCourseDto, CourseResponseDto
from src.application.dtos.pagination import PaginatedResponse
from src.domain.exceptions.base import DomainException
from src.api.auth_helper import verify_auth_sql

router = APIRouter(prefix="/courses", tags=["Courses (Direct SQL Queries)"])

@router.post("/", response_model=CourseResponseDto, status_code=status.HTTP_201_CREATED)
async def create_course(
    dto: CreateCourseDto,
    authorization: Optional[str] = Header(None)
):
    """
    Tạo khóa học mới bằng SQL Query trực tiếp (Yêu cầu quyền: Admin).
    """
    await verify_auth_sql(authorization, required_roles=["Admin"])

    async with AsyncSessionLocal() as session:
        query = text("""
            INSERT INTO courses (name, level, fee, max_capacity, is_active, is_deleted, created_at)
            VALUES (:name, :level, :fee, :max_capacity, :is_active, 0, NOW())
        """)
        await session.execute(query, {
            "name": dto.name,
            "level": dto.level,
            "fee": float(dto.fee),
            "max_capacity": dto.max_capacity,
            "is_active": dto.is_active
        })
        await session.commit()

        # Truy vấn khóa học vừa tạo
        get_query = text("SELECT * FROM courses WHERE is_deleted = 0 ORDER BY id DESC LIMIT 1")
        res = await session.execute(get_query)
        course = res.mappings().first()
        return dict(course)

@router.get("/{id}", response_model=CourseResponseDto)
async def get_course(id: int):
    """
    Xem chi tiết khóa học bằng SQL Query.
    """
    async with AsyncSessionLocal() as session:
        query = text("SELECT * FROM courses WHERE id = :id AND is_deleted = 0")
        res = await session.execute(query, {"id": id})
        course = res.mappings().first()
        if not course:
            raise DomainException(f"Course with ID {id} not found", status_code=404)
        return dict(course)

@router.get("/", response_model=PaginatedResponse[CourseResponseDto])
async def list_courses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("id"),
    sort_desc: bool = Query(False),
    name: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    is_active: Optional[int] = Query(None)
):
    """
    Lấy danh sách khóa học bằng SQL Query có phân trang, lọc và sắp xếp.
    """
    async with AsyncSessionLocal() as session:
        where_clauses = ["is_deleted = 0"]
        params = {"limit": size, "offset": (page - 1) * size}

        if name:
            where_clauses.append("name LIKE :name")
            params["name"] = f"%{name}%"
        if level:
            where_clauses.append("level = :level")
            params["level"] = level
        if is_active is not None:
            where_clauses.append("is_active = :is_active")
            params["is_active"] = is_active

        where_sql = " AND ".join(where_clauses)
        order_col = sort_by if sort_by in ["id", "name", "level", "fee", "created_at"] else "id"
        order_dir = "DESC" if sort_desc else "ASC"

        count_query = text(f"SELECT COUNT(*) FROM courses WHERE {where_sql}")
        total = (await session.execute(count_query, params)).scalar() or 0

        data_query = text(f"SELECT * FROM courses WHERE {where_sql} ORDER BY {order_col} {order_dir} LIMIT :limit OFFSET :offset")
        res = await session.execute(data_query, params)
        items = [dict(row) for row in res.mappings().all()]

        pages = math.ceil(total / size) if size > 0 else 0
        return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

@router.put("/{id}", response_model=CourseResponseDto)
async def update_course(
    id: int,
    dto: UpdateCourseDto,
    authorization: Optional[str] = Header(None)
):
    """
    Cập nhật khóa học bằng SQL Query (Yêu cầu quyền: Admin).
    """
    await verify_auth_sql(authorization, required_roles=["Admin"])

    async with AsyncSessionLocal() as session:
        # Kiểm tra tồn tại
        check_query = text("SELECT * FROM courses WHERE id = :id AND is_deleted = 0")
        res = await session.execute(check_query, {"id": id})
        existing = res.mappings().first()
        if not existing:
            raise DomainException(f"Course with ID {id} not found", status_code=404)

        update_data = dto.model_dump(exclude_unset=True)
        if update_data:
            set_clauses = [f"{k} = :{k}" for k in update_data.keys()]
            set_sql = ", ".join(set_clauses)
            update_data["id"] = id
            update_query = text(f"UPDATE courses SET {set_sql} WHERE id = :id AND is_deleted = 0")
            await session.execute(update_query, update_data)
            await session.commit()

        res = await session.execute(check_query, {"id": id})
        return dict(res.mappings().first())

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Xóa mềm khóa học bằng SQL Query (Yêu cầu quyền: Admin).
    """
    await verify_auth_sql(authorization, required_roles=["Admin"])

    async with AsyncSessionLocal() as session:
        check_query = text("SELECT * FROM courses WHERE id = :id AND is_deleted = 0")
        res = await session.execute(check_query, {"id": id})
        if not res.mappings().first():
            raise DomainException(f"Course with ID {id} not found", status_code=404)

        delete_query = text("UPDATE courses SET is_deleted = 1 WHERE id = :id")
        await session.execute(delete_query, {"id": id})
        await session.commit()
