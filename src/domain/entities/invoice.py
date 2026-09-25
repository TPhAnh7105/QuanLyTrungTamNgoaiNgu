from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime
from src.infrastructure.database.connection import Base

class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    enrollment_id = Column(Integer, ForeignKey('enrollments.id', ondelete='CASCADE'), nullable=False)
    amount = Column(DECIMAL(18, 2), nullable=False)
    payment_status = Column(String(20), default='Pending', nullable=False)  # Pending, Paid, Overdue
    due_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Integer, default=0)
