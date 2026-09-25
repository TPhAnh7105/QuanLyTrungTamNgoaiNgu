from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, Numeric, DateTime, ForeignKey
from src.infrastructure.database.connection import Base

class Grade(Base):
    __tablename__ = 'grades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    exam_id = Column(Integer, ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    
    # AI NLP Features
    essay_text = Column(Text, nullable=True)
    ai_evaluation_json = Column(Text, nullable=True)
    
    graded_by = Column(Integer, ForeignKey('teachers.id', ondelete='SET NULL'), nullable=True)
    graded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Integer, default=0)
