from fastapi import APIRouter, Header, Query, status
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timezone
import math

from src.infrastructure.database.connection import AsyncSessionLocal
from src.application.dtos.invoice import InvoiceResponseDto, PayInvoiceResponseDto
from src.application.dtos.pagination import PaginatedResponse
from src.domain.exceptions.base import DomainException
from src.api.auth_helper import verify_auth_sql

router = APIRouter(prefix="/invoices", tags=["Invoices (Direct SQL Queries)"])

@router.get("/{id}", response_model=InvoiceResponseDto)
async def get_invoice(
    id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Xem chi tiết hóa đơn bằng SQL Query.
    """
    await verify_auth_sql(authorization)

    async with AsyncSessionLocal() as session:
        query = text("SELECT * FROM invoices WHERE id = :id AND is_deleted = 0")
        res = await session.execute(query, {"id": id})
        invoice = res.mappings().first()
        if not invoice:
            raise DomainException(f"Invoice with ID {id} not found", status_code=404)
        return dict(invoice)

@router.get("/", response_model=PaginatedResponse[InvoiceResponseDto])
async def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = Query(None),
    payment_status: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    Lấy danh sách hóa đơn bằng SQL Query.
    """
    await verify_auth_sql(authorization)

    async with AsyncSessionLocal() as session:
        where_clauses = ["is_deleted = 0"]
        params = {"limit": size, "offset": (page - 1) * size}

        if student_id:
            where_clauses.append("student_id = :student_id")
            params["student_id"] = student_id
        if payment_status:
            where_clauses.append("payment_status = :payment_status")
            params["payment_status"] = payment_status

        where_sql = " AND ".join(where_clauses)
        count_query = text(f"SELECT COUNT(*) FROM invoices WHERE {where_sql}")
        total = (await session.execute(count_query, params)).scalar() or 0

        data_query = text(f"SELECT * FROM invoices WHERE {where_sql} ORDER BY id DESC LIMIT :limit OFFSET :offset")
        res = await session.execute(data_query, params)
        items = [dict(row) for row in res.mappings().all()]

        pages = math.ceil(total / size) if size > 0 else 0
        return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

@router.post("/{id}/pay", response_model=PayInvoiceResponseDto, status_code=status.HTTP_200_OK)
async def pay_invoice(
    id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Thanh toán hóa đơn học phí bằng SQL Query.
    """
    await verify_auth_sql(authorization, required_roles=["Admin", "Teacher"])

    async with AsyncSessionLocal() as session:
        check_query = text("SELECT * FROM invoices WHERE id = :id AND is_deleted = 0")
        res = await session.execute(check_query, {"id": id})
        invoice = res.mappings().first()
        if not invoice:
            raise DomainException("Hóa đơn không tồn tại.", status_code=404)

        if invoice["payment_status"] == "Paid":
            raise DomainException("Hóa đơn này đã được thanh toán.", error_code="ALREADY_PAID", status_code=400)

        now = datetime.now(timezone.utc)
        update_query = text("UPDATE invoices SET payment_status = 'Paid', payment_date = :now WHERE id = :id AND is_deleted = 0")
        await session.execute(update_query, {"now": now, "id": id})
        await session.commit()

        res_updated = await session.execute(check_query, {"id": id})
        updated = res_updated.mappings().first()

        return PayInvoiceResponseDto(
            invoice_id=updated["id"],
            amount=float(updated["amount"]),
            payment_status=updated["payment_status"],
            payment_date=updated["payment_date"]
        )
