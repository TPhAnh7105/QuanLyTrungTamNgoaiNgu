from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class TeacherBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    specialization: str = Field(..., pattern="^(TOEFL|IELTS|TOEIC|Communicative English)$")
    bio: Optional[str] = Field(None, max_length=1000)

class CreateTeacherDto(TeacherBase):
    user_id: int = Field(..., gt=0)

class UpdateTeacherDto(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    specialization: Optional[str] = Field(None, pattern="^(TOEFL|IELTS|TOEIC|Communicative English)$")
    bio: Optional[str] = Field(None, max_length=1000)

class TeacherResponseDto(TeacherBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
