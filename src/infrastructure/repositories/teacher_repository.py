from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.repositories.base_repository import BaseRepository
from src.domain.entities.teacher import Teacher

class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self, session: AsyncSession):
        super().__init__(Teacher, session)
