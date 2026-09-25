from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.invoice import PayInvoiceResponseDto
from src.domain.exceptions.base import DomainException
from src.infrastructure.repositories.invoice_repository import InvoiceRepository

class InvoiceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.invoice_repo = InvoiceRepository(session)

    async def pay_invoice(self, invoice_id: int) -> PayInvoiceResponseDto:
        """
        Thực hiện thanh toán hóa đơn.
        """
        try:
            invoice = await self.invoice_repo.get_by_id(invoice_id)
            if not invoice:
                raise DomainException("Hóa đơn không tồn tại.", status_code=404)
            
            if invoice.payment_status == "Paid":
                raise DomainException("Hóa đơn này đã được thanh toán.", error_code="ALREADY_PAID", status_code=400)

            # Cập nhật trạng thái
            now = datetime.now(timezone.utc)
            invoice.payment_status = "Paid"
            invoice.payment_date = now
            
            await self.session.commit()

            return PayInvoiceResponseDto(
                invoice_id=invoice.id,
                amount=invoice.amount,
                payment_status=invoice.payment_status,
                payment_date=invoice.payment_date
            )

        except DomainException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise DomainException(f"Lỗi khi thanh toán hóa đơn: {str(e)}", error_code="PAYMENT_FAILED", status_code=500)
