from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.domain.entities.enrollment import Enrollment
from src.infrastructure.repositories.base_repository import BaseRepository

class EnrollmentRepository(BaseRepository[Enrollment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Enrollment, session)

    async def get_active_enrollments_count(self, course_id: int) -> int:
        """Count active enrollments for a specific course."""
        stmt = (
            select(func.count(Enrollment.id))
            .where(
                Enrollment.course_id == course_id,
                Enrollment.status == "Active",
                Enrollment.is_deleted == 0
            )
        )
        result = await self.session.scalar(stmt)
        return result or 0

    async def get_by_student_and_course(self, student_id: int, course_id: int) -> Optional[Enrollment]:
        """Find enrollment record by student and course ID."""
        stmt = (
            select(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
                Enrollment.is_deleted == 0
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_student_enrollments(self, student_id: int) -> List[Enrollment]:
        """Retrieve all enrollments of a student."""
        stmt = (
            select(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.is_deleted == 0
            )
            .order_by(Enrollment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
