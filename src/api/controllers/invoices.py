from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from src.infrastructure.database.connection import get_db_session
from src.application.dtos.invoice import InvoiceResponseDto, PayInvoiceResponseDto
from src.application.dtos.pagination import PaginatedResponse
from src.application.services.invoice_service import InvoiceService
from src.infrastructure.repositories.invoice_repository import InvoiceRepository
from src.domain.exceptions.base import DomainException
from src.domain.entities.user import User
from src.api.dependencies import require_roles, get_current_user

router = APIRouter(prefix="/invoices", tags=["Invoices (Hóa đơn Học phí)"])

@router.get("/{id}", response_model=InvoiceResponseDto)
async def get_invoice(
    id: int, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Xem chi tiết hóa đơn theo ID.
    """
    repo = InvoiceRepository(db)
    invoice = await repo.get_by_id(id)
    if not invoice:
        raise DomainException(f"Invoice with ID {id} not found", status_code=404)
    return invoice

@router.get("/", response_model=PaginatedResponse[InvoiceResponseDto])
async def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = Query(None),
    payment_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách hóa đơn học phí có phân trang và lọc.
    """
    repo = InvoiceRepository(db)
    filters = {"student_id": student_id, "payment_status": payment_status}
    filters = {k: v for k, v in filters.items() if v is not None}
    
    items, total = await repo.get_paginated(
        page=page, 
        size=size, 
        sort_by="created_at", 
        sort_desc=True, 
        **filters
    )
    
    pages = math.ceil(total / size) if size > 0 else 0
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/{id}/pay", response_model=PayInvoiceResponseDto, status_code=status.HTTP_200_OK)
async def pay_invoice(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(["Admin", "Teacher"]))
):
    """
    Thanh toán hóa đơn học phí. Chuyển trạng thái sang 'Paid'.
    Yêu cầu quyền: Admin hoặc Teacher.
    """
    service = InvoiceService(db)
    result = await service.pay_invoice(id)
    return result
