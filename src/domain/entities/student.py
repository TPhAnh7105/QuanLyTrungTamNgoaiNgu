from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime
from src.infrastructure.database.connection import Base

class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    phone = Column(String, nullable=True)
    weekly_study_hours = Column(Integer, default=0)
    absence_rate = Column(DECIMAL, default=0.0)
    motivation_score = Column(Integer, default=0)
    parental_support = Column(String, default="Medium")  # Low/Medium/High
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Integer, default=0)
