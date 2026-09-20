from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CourseBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    level: str = Field(..., pattern="^(A1|A2|B1|B2|C1|C2)$")
    fee: Decimal = Field(..., gt=0)
    max_capacity: int = Field(..., gt=0)
    is_active: int = Field(1, ge=0, le=1)

class CreateCourseDto(CourseBase):
    pass

class UpdateCourseDto(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=150)
    level: Optional[str] = Field(None, pattern="^(A1|A2|B1|B2|C1|C2)$")
    fee: Optional[Decimal] = Field(None, gt=0)
    max_capacity: Optional[int] = Field(None, gt=0)
    is_active: Optional[int] = Field(None, ge=0, le=1)

class CourseResponseDto(CourseBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
