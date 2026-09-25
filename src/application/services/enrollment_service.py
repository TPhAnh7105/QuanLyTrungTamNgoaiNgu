from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.application.dtos.enrollment import CreateEnrollmentDto, EnrollmentResultDto
from src.domain.exceptions.base import DomainException
from src.domain.entities.enrollment import Enrollment
from src.domain.entities.invoice import Invoice
from src.domain.entities.course import Course
from src.domain.entities.student import Student
from src.infrastructure.repositories.enrollment_repository import EnrollmentRepository
from src.infrastructure.repositories.invoice_repository import InvoiceRepository

class EnrollmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.enrollment_repo = EnrollmentRepository(session)
        self.invoice_repo = InvoiceRepository(session)

    async def enroll_student_transaction(self, dto: CreateEnrollmentDto) -> EnrollmentResultDto:
        """
        Thực thi ACID Giao dịch: Kiểm tra sĩ số -> Tạo Ghi danh -> Sinh Hóa đơn
        Sử dụng SELECT ... FOR UPDATE để chống Race Condition (Overbooking).
        """
        try:
            # 1. Khóa dòng khóa học để kiểm tra sĩ số (Chống Race Condition)
            course_stmt = (
                select(Course)
                .where(Course.id == dto.course_id, Course.is_deleted == 0)
                .with_for_update()
            )
            course = (await self.session.execute(course_stmt)).scalar_one_or_none()
            if not course:
                raise DomainException("Khóa học không tồn tại hoặc đã bị xóa.", status_code=404)
            if course.is_active == 0:
                raise DomainException("Khóa học hiện không hoạt động.", status_code=400)

            # 2. Kiểm tra học viên tồn tại
            student_stmt = select(Student).where(Student.id == dto.student_id, Student.is_deleted == 0)
            student = (await self.session.execute(student_stmt)).scalar_one_or_none()
            if not student:
                raise DomainException("Học viên không tồn tại.", status_code=404)

            # 3. Kiểm tra trùng lặp ghi danh
            existing_enrollment = await self.enrollment_repo.get_by_student_and_course(dto.student_id, dto.course_id)
            if existing_enrollment:
                raise DomainException("Học viên đã được ghi danh vào khóa học này rồi.", error_code="ALREADY_ENROLLED", status_code=409)

            # 4. Kiểm tra sĩ số (Capacity Check)
            current_enrolled = await self.enrollment_repo.get_active_enrollments_count(dto.course_id)
            if current_enrolled >= course.max_capacity:
                raise DomainException(f"Khóa học đã đạt giới hạn sĩ số ({course.max_capacity}). Không thể ghi danh thêm.", error_code="COURSE_FULL", status_code=400)

            # 5. Tạo bản ghi Enrollment
            enrollment = Enrollment(
                student_id=dto.student_id,
                course_id=dto.course_id,
                enrollment_date=datetime.now(timezone.utc),
                status="Active"
            )
            self.session.add(enrollment)
            await self.session.flush()  # Để lấy enrollment.id

            # 6. Tạo bản ghi Invoice
            due_date = datetime.now(timezone.utc) + timedelta(days=7)
            invoice = Invoice(
                student_id=dto.student_id,
                enrollment_id=enrollment.id,
                amount=course.fee,
                payment_status="Pending",
                due_date=due_date
            )
            self.session.add(invoice)
            await self.session.flush()  # Để lấy invoice.id

            # 7. Commit toàn bộ giao dịch
            await self.session.commit()

            return EnrollmentResultDto(
                enrollment_id=enrollment.id,
                student_id=student.id,
                course_id=course.id,
                course_name=course.name,
                status=enrollment.status,
                enrollment_date=enrollment.enrollment_date,
                invoice_id=invoice.id,
                tuition_amount=invoice.amount,
                invoice_status=invoice.payment_status,
                due_date=invoice.due_date
            )

        except DomainException:
            # Re-raise domain exceptions so error handler catches them, after rollback
            await self.session.rollback()
            raise
        except Exception as e:
            # Lỗi hệ thống bất ngờ -> Tự động Rollback 100%
            await self.session.rollback()
            raise DomainException(f"Lỗi hệ thống khi ghi danh: {str(e)}", error_code="TRANSACTION_FAILED", status_code=500)
