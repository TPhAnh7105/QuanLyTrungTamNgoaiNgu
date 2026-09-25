from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.domain.entities.invoice import Invoice
from src.infrastructure.repositories.base_repository import BaseRepository

class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, session: AsyncSession):
        super().__init__(Invoice, session)

    async def get_by_enrollment_id(self, enrollment_id: int) -> Optional[Invoice]:
        """Find invoice associated with a specific enrollment."""
        stmt = (
            select(Invoice)
            .where(
                Invoice.enrollment_id == enrollment_id,
                Invoice.is_deleted == 0
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_student_invoices(self, student_id: int) -> List[Invoice]:
        """Retrieve all invoices of a student."""
        stmt = (
            select(Invoice)
            .where(
                Invoice.student_id == student_id,
                Invoice.is_deleted == 0
            )
            .order_by(Invoice.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_as_paid(self, invoice_id: int) -> Optional[Invoice]:
        """Mark an invoice as Paid with current timestamp."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(Invoice)
            .where(Invoice.id == invoice_id, Invoice.is_deleted == 0)
            .values(payment_status="Paid", payment_date=now)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_by_id(invoice_id)
