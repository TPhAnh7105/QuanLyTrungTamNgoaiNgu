from fastapi import APIRouter, Header, Query, status
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timedelta, timezone
import math

from src.infrastructure.database.connection import AsyncSessionLocal
from src.application.dtos.enrollment import (
    EnrollmentResponseDto, 
    EnrollmentResultDto
)
from src.application.dtos.pagination import PaginatedResponse
from src.domain.exceptions.base import DomainException
from src.api.auth_helper import verify_auth_sql

router = APIRouter(prefix="/enrollments", tags=["Enrollments (Direct SQL ACID Transactions)"])

@router.post("/", response_model=EnrollmentResultDto, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    student_id: int = Query(..., description="ID của học viên"),
    course_id: int = Query(..., description="ID của khóa học"),
    authorization: Optional[str] = Header(None)
):
    """
    Ghi danh học viên vào khóa học bằng SQL ACID Transaction trực tiếp.
    Sử dụng SELECT ... FOR UPDATE chống Race Condition.
    """
    await verify_auth_sql(authorization, required_roles=["Admin", "Teacher"])

    async with AsyncSessionLocal() as session:
        try:
            # 1. Khóa dòng dữ liệu khóa học bằng SQL FOR UPDATE
            lock_course_query = text("SELECT * FROM courses WHERE id = :course_id AND is_deleted = 0 FOR UPDATE")
            res_course = await session.execute(lock_course_query, {"course_id": course_id})
            course = res_course.mappings().first()
            if not course:
                raise DomainException("Khóa học không tồn tại hoặc đã bị xóa.", status_code=404)
            if course["is_active"] == 0:
                raise DomainException("Khóa học hiện không hoạt động.", status_code=400)

            # 2. Kiểm tra học viên tồn tại
            check_student_query = text("SELECT * FROM students WHERE id = :student_id AND is_deleted = 0")
            res_student = await session.execute(check_student_query, {"student_id": student_id})
            student = res_student.mappings().first()
            if not student:
                raise DomainException("Học viên không tồn tại.", status_code=404)

            # 3. Kiểm tra trùng lặp ghi danh
            dup_query = text("SELECT id FROM enrollments WHERE student_id = :student_id AND course_id = :course_id AND is_deleted = 0")
            res_dup = await session.execute(dup_query, {"student_id": student_id, "course_id": course_id})
            if res_dup.mappings().first():
                raise DomainException("Học viên đã được ghi danh vào khóa học này rồi.", error_code="ALREADY_ENROLLED", status_code=409)

            # 4. Kiểm tra sĩ số hiện tại
            count_query = text("SELECT COUNT(*) FROM enrollments WHERE course_id = :course_id AND status = 'Active' AND is_deleted = 0")
            active_count = (await session.execute(count_query, {"course_id": course_id})).scalar() or 0
            if active_count >= course["max_capacity"]:
                raise DomainException(
                    f"Khóa học đã đạt giới hạn sĩ số ({course['max_capacity']}). Không thể ghi danh thêm.",
                    error_code="COURSE_FULL",
                    status_code=400
                )

            # 5. Insert Enrollment bằng SQL
            insert_enroll_query = text("""
                INSERT INTO enrollments (student_id, course_id, enrollment_date, status, is_deleted, created_at)
                VALUES (:student_id, :course_id, NOW(), 'Active', 0, NOW())
            """)
            await session.execute(insert_enroll_query, {"student_id": student_id, "course_id": course_id})

            # Lấy enrollment id vừa tạo
            get_enroll_id_query = text("SELECT * FROM enrollments WHERE student_id = :student_id AND course_id = :course_id ORDER BY id DESC LIMIT 1")
            enrollment = (await session.execute(get_enroll_id_query, {"student_id": student_id, "course_id": course_id})).mappings().first()

            # 6. Insert Invoice bằng SQL
            due_date = datetime.now(timezone.utc) + timedelta(days=7)
            insert_inv_query = text("""
                INSERT INTO invoices (student_id, enrollment_id, amount, payment_status, due_date, is_deleted, created_at)
                VALUES (:student_id, :enrollment_id, :amount, 'Pending', :due_date, 0, NOW())
            """)
            await session.execute(insert_inv_query, {
                "student_id": student_id,
                "enrollment_id": enrollment["id"],
                "amount": float(course["fee"]),
                "due_date": due_date
            })

            # Lấy invoice id vừa tạo
            get_inv_query = text("SELECT * FROM invoices WHERE enrollment_id = :enrollment_id ORDER BY id DESC LIMIT 1")
            invoice = (await session.execute(get_inv_query, {"enrollment_id": enrollment["id"]})).mappings().first()

            # 7. Commit Transaction
            await session.commit()

            return EnrollmentResultDto(
                enrollment_id=enrollment["id"],
                student_id=student["id"],
                course_id=course["id"],
                course_name=course["name"],
                status=enrollment["status"],
                enrollment_date=enrollment["enrollment_date"],
                invoice_id=invoice["id"],
                tuition_amount=float(invoice["amount"]),
                invoice_status=invoice["payment_status"],
                due_date=invoice["due_date"]
            )

        except DomainException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            raise DomainException(f"Lỗi hệ thống khi ghi danh: {str(e)}", error_code="TRANSACTION_FAILED", status_code=500)

@router.get("/{id}", response_model=EnrollmentResponseDto)
async def get_enrollment(
    id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Xem chi tiết ghi danh bằng SQL Query.
    """
    await verify_auth_sql(authorization)

    async with AsyncSessionLocal() as session:
        query = text("SELECT * FROM enrollments WHERE id = :id AND is_deleted = 0")
        res = await session.execute(query, {"id": id})
        enrollment = res.mappings().first()
        if not enrollment:
            raise DomainException(f"Enrollment with ID {id} not found", status_code=404)
        return dict(enrollment)

@router.get("/", response_model=PaginatedResponse[EnrollmentResponseDto])
async def list_enrollments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    Lấy danh sách ghi danh bằng SQL Query.
    """
    await verify_auth_sql(authorization)

    async with AsyncSessionLocal() as session:
        where_clauses = ["is_deleted = 0"]
        params = {"limit": size, "offset": (page - 1) * size}

        if student_id:
            where_clauses.append("student_id = :student_id")
            params["student_id"] = student_id
        if course_id:
            where_clauses.append("course_id = :course_id")
            params["course_id"] = course_id
        if status:
            where_clauses.append("status = :status")
            params["status"] = status

        where_sql = " AND ".join(where_clauses)
        count_query = text(f"SELECT COUNT(*) FROM enrollments WHERE {where_sql}")
        total = (await session.execute(count_query, params)).scalar() or 0

        data_query = text(f"SELECT * FROM enrollments WHERE {where_sql} ORDER BY id DESC LIMIT :limit OFFSET :offset")
        res = await session.execute(data_query, params)
        items = [dict(row) for row in res.mappings().all()]

        pages = math.ceil(total / size) if size > 0 else 0
        return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

@router.put("/{id}/status", response_model=EnrollmentResponseDto)
async def update_enrollment_status(
    id: int,
    status: str = Query(..., description="Trạng thái: Active, Completed, Dropped"),
    authorization: Optional[str] = Header(None)
):
    """
    Cập nhật trạng thái ghi danh bằng SQL Query.
    """
    await verify_auth_sql(authorization, required_roles=["Admin", "Teacher"])

    async with AsyncSessionLocal() as session:
        check_query = text("SELECT * FROM enrollments WHERE id = :id AND is_deleted = 0")
        res = await session.execute(check_query, {"id": id})
        if not res.mappings().first():
            raise DomainException(f"Enrollment with ID {id} not found", status_code=404)

        update_query = text("UPDATE enrollments SET status = :status WHERE id = :id AND is_deleted = 0")
        await session.execute(update_query, {"status": status, "id": id})
        await session.commit()

        res = await session.execute(check_query, {"id": id})
        return dict(res.mappings().first())
