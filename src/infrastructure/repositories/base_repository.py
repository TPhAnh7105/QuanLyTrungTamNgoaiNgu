from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from src.infrastructure.database.connection import Base
from src.domain.exceptions.base import DomainException

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    def _soft_delete_filter(self):
        """Returns a SQLAlchemy filter clause for is_deleted == 0, if the model has that column."""
        if hasattr(self.model, 'is_deleted'):
            return self.model.is_deleted == 0
        return True  # No filter if column doesn't exist

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id, self._soft_delete_filter())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, id: int, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            raise DomainException(f"{self.model.__name__} with id {id} not found", status_code=404)
        
        for field, value in obj_in.items():
            if value is not None:
                setattr(db_obj, field, value)
                
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def soft_delete(self, id: int) -> bool:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            raise DomainException(f"{self.model.__name__} with id {id} not found", status_code=404)
            
        if hasattr(db_obj, 'is_deleted'):
            db_obj.is_deleted = 1
            await self.session.commit()
            return True
        return False

    async def get_paginated(
        self, 
        page: int = 1, 
        size: int = 20, 
        sort_by: Optional[str] = None, 
        sort_desc: bool = False,
        **filters
    ) -> tuple[List[ModelType], int]:
        stmt = select(self.model).where(self._soft_delete_filter())
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                if isinstance(value, str):
                    stmt = stmt.where(getattr(self.model, key).ilike(f"%{value}%"))
                else:
                    stmt = stmt.where(getattr(self.model, key) == value)

        # Apply sorting
        if sort_by and hasattr(self.model, sort_by):
            column = getattr(self.model, sort_by)
            if sort_desc:
                stmt = stmt.order_by(column.desc())
            else:
                stmt = stmt.order_by(column.asc())
                
        # Total count query
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(count_stmt)
        
        # Apply pagination
        stmt = stmt.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(stmt)
        return result.scalars().all(), total or 0
