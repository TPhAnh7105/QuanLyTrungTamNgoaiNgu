from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.exam import Exam
from src.infrastructure.repositories.base_repository import BaseRepository

class ExamRepository(BaseRepository[Exam]):
    def __init__(self, session: AsyncSession):
        super().__init__(Exam, session)

    async def get_or_create_placement_exam(self) -> Exam:
        """
        Lấy kỳ thi Placement Test mặc định hoặc tạo mới nếu chưa tồn tại.
        """
        stmt = (
            select(Exam)
            .where(Exam.exam_type == "Placement", Exam.is_deleted == 0)
            .limit(1)
        )
        exam = (await self.session.execute(stmt)).scalar_one_or_none()
        if not exam:
            exam = Exam(
                name="Bài thi Xếp lớp Tiếng Anh (AI Placement Test)",
                exam_type="Placement",
                max_score=10.00
            )
            self.session.add(exam)
            await self.session.flush()
        return exam
