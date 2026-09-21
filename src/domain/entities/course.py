from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime
from src.infrastructure.database.connection import Base

class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    level = Column(String(10), nullable=False)  # A1/A2/B1/B2/C1/C2
    fee = Column(DECIMAL(18, 2), nullable=False)
    max_capacity = Column(Integer, nullable=False, default=30)
    is_active = Column(Integer, default=1)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
