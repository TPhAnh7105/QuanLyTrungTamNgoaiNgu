from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, condecimal

class StudentBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: datetime
    phone: Optional[str] = Field(None, max_length=20)
    weekly_study_hours: int = Field(0, ge=0)
    absence_rate: float = Field(0.0, ge=0.0, le=1.0)
    motivation_score: int = Field(0, ge=0, le=10)
    parental_support: str = Field("Medium", pattern="^(Low|Medium|High)$")

class CreateStudentDto(StudentBase):
    user_id: int = Field(..., gt=0)

class StudentResponseDto(StudentBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
