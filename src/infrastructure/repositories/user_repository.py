from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.domain.entities.user import User
from src.infrastructure.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_refresh_token(self, user_id: int, refresh_token: Optional[str]) -> None:
        stmt = update(User).where(User.id == user_id).values(refresh_token=refresh_token)
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_by_refresh_token(self, refresh_token: str) -> Optional[User]:
        stmt = select(User).where(User.refresh_token == refresh_token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
