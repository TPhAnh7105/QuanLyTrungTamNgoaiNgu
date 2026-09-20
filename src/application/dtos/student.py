from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

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

class UpdateStudentDto(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    date_of_birth: Optional[datetime] = None
    phone: Optional[str] = Field(None, max_length=20)
    weekly_study_hours: Optional[int] = Field(None, ge=0)
    absence_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    motivation_score: Optional[int] = Field(None, ge=0, le=10)
    parental_support: Optional[str] = Field(None, pattern="^(Low|Medium|High)$")

class StudentResponseDto(StudentBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
