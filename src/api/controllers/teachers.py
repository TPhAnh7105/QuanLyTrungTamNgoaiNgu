from fastapi import APIRouter, Header, Query, status
from sqlalchemy import text
from typing import Optional
import math

from src.infrastructure.database.connection import AsyncSessionLocal
from src.application.dtos.teacher import CreateTeacherDto, UpdateTeacherDto, TeacherResponseDto
from src.application.dtos.pagination import PaginatedResponse
from src.domain.exceptions.base import DomainException
from src.api.auth_helper import verify_auth_sql

router = APIRouter(prefix="/teachers", tags=["Teachers (Direct SQL Queries)"])

@router.post("/", response_model=TeacherResponseDto, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    dto: CreateTeacherDto,
    authorization: Optional[str] = Header(None)
):
    """
    Tạo thông tin giáo viên bằng SQL Query (Yêu cầu quyền: Admin).
    """
    await verify_auth_sql(authorization, required_roles=["Admin"])

    async with AsyncSessionLocal() as session:
        # Kiểm tra user_id
        user_res = await session.execute(text("SELECT id FROM users WHERE id = :user_id"), {"user_id": dto.user_id})
        if not user_res.mappings().first():
            raise DomainException("User ID không tồn tại", status_code=400)

        exist_res = await session.execute(text("SELECT id FROM teachers WHERE user_id = :user_id AND is_deleted = 0"), {"user_id": dto.user_id})
        if exist_res.mappings().first():
            raise DomainException("User ID này đã được liên kết với giáo viên khác", status_code=409)

        insert_query = text("""
            INSERT INTO teachers (user_id, full_name, specialization, bio, is_deleted, created_at)
            VALUES (:user_id, :full_name, :specialization, :bio, 0, NOW())
        """)
        await session.execute(insert_query, {
            "user_id": dto.user_id,
            "full_name": dto.full_name,
            "specialization": dto.specialization,
            "bio": dto.bio
        })
        await session.commit()

        get_query = text("SELECT * FROM teachers WHERE is_deleted = 0 ORDER BY id DESC LIMIT 1")
        res = await session.execute(get_query)
        teacher = res.mappings().first()
        return dict(teacher)

@router.get("/{id}", response_model=TeacherResponseDto)
async def get_teacher(
    id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Xem chi tiết giáo viên bằng SQL Query.
    """
    await verify_auth_sql(authorization, required_roles=["Admin", "Teacher", "Student"])

    async with AsyncSessionLocal() as session:
        query = text("SELECT * FROM teachers WHERE id = :id AND is_deleted = 0")
        res = await session.execute(query, {"id": id})
        teacher = res.mappings().first()
        if not teacher:
            raise DomainException(f"Teacher with ID {id} not found", status_code=404)
        return dict(teacher)

@router.get("/", response_model=PaginatedResponse[TeacherResponseDto])
async def list_teachers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("id"),
    sort_desc: bool = Query(False),
    full_name: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    Lấy danh sách giáo viên bằng SQL Query.
    """
    await verify_auth_sql(authorization, required_roles=["Admin", "Teacher", "Student"])

    async with AsyncSessionLocal() as session:
        where_clauses = ["is_deleted = 0"]
        params = {"limit": size, "offset": (page - 1) * size}

        if full_name:
            where_clauses.append("full_name LIKE :full_name")
            params["full_name"] = f"%{full_name}%"
        if specialization:
            where_clauses.append("specialization LIKE :specialization")
            params["specialization"] = f"%{specialization}%"

        where_sql = " AND ".join(where_clauses)
        order_col = sort_by if sort_by in ["id", "full_name", "specialization", "created_at"] else "id"
        order_dir = "DESC" if sort_desc else "ASC"

        count_query = text(f"SELECT COUNT(*) FROM teachers WHERE {where_sql}")
        total = (await session.execute(count_query, params)).scalar() or 0

        data_query = text(f"SELECT * FROM teachers WHERE {where_sql} ORDER BY {order_col} {order_dir} LIMIT :limit OFFSET :offset")
        res = await session.execute(data_query, params)
        items = [dict(row) for row in res.mappings().all()]

        pages = math.ceil(total / size) if size > 0 else 0
        return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

@router.put("/{id}", response_model=TeacherResponseDto)
async def update_teacher(
    id: int,
    dto: UpdateTeacherDto,
    authorization: Optional[str] = Header(None)
):
    """
    Cập nhật thông tin giáo viên bằng SQL Query (Yêu cầu quyền: Admin).
    """
    await verify_auth_sql(authorization, required_roles=["Admin"])

    async with AsyncSessionLocal() as session:
        check_query = text("SELECT * FROM teachers WHERE id = :id AND is_deleted = 0")
        res = await session.execute(check_query, {"id": id})
        if not res.mappings().first():
            raise DomainException(f"Teacher with ID {id} not found", status_code=404)

        update_data = dto.model_dump(exclude_unset=True)
        if update_data:
            set_clauses = [f"{k} = :{k}" for k in update_data.keys()]
            set_sql = ", ".join(set_clauses)
            update_data["id"] = id
            update_query = text(f"UPDATE teachers SET {set_sql} WHERE id = :id AND is_deleted = 0")
            await session.execute(update_query, update_data)
            await session.commit()

        res = await session.execute(check_query, {"id": id})
        return dict(res.mappings().first())

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Xóa mềm giáo viên bằng SQL Query (Yêu cầu quyền: Admin).
    """
    await verify_auth_sql(authorization, required_roles=["Admin"])

    async with AsyncSessionLocal() as session:
        check_query = text("SELECT * FROM teachers WHERE id = :id AND is_deleted = 0")
        res = await session.execute(check_query, {"id": id})
        if not res.mappings().first():
            raise DomainException(f"Teacher with ID {id} not found", status_code=404)

        delete_query = text("UPDATE teachers SET is_deleted = 1 WHERE id = :id")
        await session.execute(delete_query, {"id": id})
        await session.commit()
