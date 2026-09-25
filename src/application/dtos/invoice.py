from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class InvoiceResponseDto(BaseModel):
    id: int
    student_id: int
    enrollment_id: int
    amount: Decimal
    payment_status: str
    due_date: datetime
    payment_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PayInvoiceResponseDto(BaseModel):
    invoice_id: int
    amount: Decimal
    payment_status: str
    payment_date: datetime
    message: str = "Thanh toán học phí thành công!"
