from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from src.infrastructure.database.connection import Base

class Enrollment(Base):
    __tablename__ = 'enrollments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    enrollment_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(20), default='Active', nullable=False)  # Active, Completed, Dropped
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('student_id', 'course_id', name='uq_student_course_enrollment'),
    )
