from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from src.infrastructure.database.connection import Base

class Exam(Base):
    __tablename__ = 'exams'

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(100), nullable=False)
    exam_type = Column(String(20), nullable=False)  # Placement, Midterm, Final
    max_score = Column(Numeric(5, 2), default=10.00)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
