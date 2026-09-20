from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.repositories.base_repository import BaseRepository
from src.domain.entities.student import Student

class StudentRepository(BaseRepository[Student]):
    def __init__(self, session: AsyncSession):
        super().__init__(Student, session)
