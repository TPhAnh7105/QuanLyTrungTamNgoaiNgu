from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.grade import Grade
from src.infrastructure.repositories.base_repository import BaseRepository

class GradeRepository(BaseRepository[Grade]):
    def __init__(self, session: AsyncSession):
        super().__init__(Grade, session)

    async def get_by_student_id(self, student_id: int) -> List[Grade]:
        """
        Lấy danh sách điểm số / bài thi của một học viên.
        """
        stmt = (
            select(Grade)
            .where(Grade.student_id == student_id, Grade.is_deleted == 0)
            .order_by(Grade.graded_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
