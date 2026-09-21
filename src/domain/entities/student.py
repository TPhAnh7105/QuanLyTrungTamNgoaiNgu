from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime, Date
from src.infrastructure.database.connection import Base

class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    phone = Column(String(20), nullable=True)
    weekly_study_hours = Column(Integer, default=5)
    absence_rate = Column(DECIMAL(5, 2), default=0.0)
    motivation_score = Column(Integer, default=7)
    parental_support = Column(String(10), default="Medium")  # Low/Medium/High
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Integer, default=0)
