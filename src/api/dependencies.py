from typing import List, Callable
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.connection import get_db_session
from src.infrastructure.services.security_service import SecurityService
from src.infrastructure.repositories.user_repository import UserRepository
from src.domain.entities.user import User
from src.domain.exceptions.base import DomainException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Dependency that decodes the Bearer JWT Access Token and fetches the active User.
    """
    if not token:
        raise DomainException(
            message="Authentication credentials were not provided",
            error_code="UNAUTHORIZED",
            status_code=401
        )

    # Decode and validate token claims
    payload = SecurityService.decode_token(token)
    
    if payload.get("token_type") != "access":
        raise DomainException(
            message="Invalid token type: Access Token required",
            error_code="INVALID_TOKEN_TYPE",
            status_code=401
        )

    user_id = payload.get("sub")
    if not user_id:
        raise DomainException(
            message="Token payload is missing subject identifier",
            error_code="MALFORMED_TOKEN",
            status_code=401
        )

    repo = UserRepository(db)
    user = await repo.get_by_id(int(user_id))
    if not user:
        raise DomainException(
            message="User account associated with this token no longer exists",
            error_code="USER_NOT_FOUND",
            status_code=401
        )

    return user

def require_roles(allowed_roles: List[str]) -> Callable:
    """
    RBAC (Role-Based Access Control) Guard Dependency Factory.
    Usage: Depends(require_roles(["Admin", "Teacher"]))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise DomainException(
                message=f"Access denied: This action requires one of the following roles: {allowed_roles}. Current role: '{current_user.role}'",
                error_code="FORBIDDEN_ROLE",
                status_code=403
            )
        return current_user

    return role_checker
