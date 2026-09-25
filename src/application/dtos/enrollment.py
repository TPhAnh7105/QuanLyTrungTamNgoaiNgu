from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class CreateEnrollmentDto(BaseModel):
    student_id: int = Field(..., gt=0, description="ID của học viên cần ghi danh")
    course_id: int = Field(..., gt=0, description="ID của khóa học")

class UpdateEnrollmentStatusDto(BaseModel):
    status: str = Field(..., pattern="^(Active|Completed|Dropped)$", description="Trạng thái: Active, Completed, Dropped")

class EnrollmentResponseDto(BaseModel):
    id: int
    student_id: int
    course_id: int
    enrollment_date: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class EnrollmentResultDto(BaseModel):
    enrollment_id: int
    student_id: int
    course_id: int
    course_name: str
    status: str
    enrollment_date: datetime
    invoice_id: int
    tuition_amount: Decimal
    invoice_status: str
    due_date: datetime
    message: str = "Ghi danh và tạo hóa đơn thành công!"
