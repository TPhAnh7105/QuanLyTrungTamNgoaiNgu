from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.repositories.base_repository import BaseRepository
from src.domain.entities.course import Course

class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession):
        super().__init__(Course, session)
