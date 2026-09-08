from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime
from src.infrastructure.database.connection import Base

class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    level = Column(String, nullable=False)  # A1/A2/B1/B2/C1/C2
    fee = Column(DECIMAL, nullable=False)
    max_capacity = Column(Integer, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
