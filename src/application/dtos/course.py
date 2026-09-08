from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class CourseBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    level: str = Field(..., pattern="^(A1|A2|B1|B2|C1|C2)$")
    fee: Decimal = Field(..., gt=0)
    max_capacity: int = Field(..., gt=0)
    is_active: int = Field(1, ge=0, le=1)

class CreateCourseDto(CourseBase):
    pass

class CourseResponseDto(CourseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
