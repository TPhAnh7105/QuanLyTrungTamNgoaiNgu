from typing import Optional, List, Dict, Any
from sqlalchemy import text
from src.infrastructure.database.connection import AsyncSessionLocal
from src.infrastructure.services.security_service import SecurityService
from src.domain.exceptions.base import DomainException

async def verify_auth_sql(authorization: Optional[str], required_roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Xác thực người dùng trực tiếp bằng SQL Query thay vì FastAPI Depends.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise DomainException("Chưa cung cấp Authorization token hợp lệ", error_code="UNAUTHORIZED", status_code=401)

    token = authorization.split(" ")[1]
    payload = SecurityService.decode_token(token)
    if not payload or payload.get("token_type") != "access":
        raise DomainException("Token không hợp lệ hoặc đã hết hạn", error_code="INVALID_TOKEN", status_code=401)

    user_id = int(payload.get("sub"))
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT id, email, role, created_at FROM users WHERE id = :id"),
            {"id": user_id}
        )
        user = result.mappings().first()
        if not user:
            raise DomainException("Người dùng không tồn tại", error_code="USER_NOT_FOUND", status_code=401)

        if required_roles and user["role"] not in required_roles:
            raise DomainException(
                f"Bạn không có quyền thực hiện thao tác này. Yêu cầu quyền: {', '.join(required_roles)}",
                error_code="FORBIDDEN",
                status_code=403
            )
        return dict(user)
