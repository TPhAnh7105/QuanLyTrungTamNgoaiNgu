from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from src.infrastructure.database.connection import Base

class Teacher(Base):
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)  # TOEFL/IELTS/TOEIC/Communicative English
    bio = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Integer, default=0)
