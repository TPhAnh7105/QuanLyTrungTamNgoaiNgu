from sqlalchemy.ext.asyncio import AsyncSession
from src.application.dtos.auth import RegisterRequestDto, LoginRequestDto, TokenResponseDto, UserResponseDto
from src.domain.exceptions.base import DomainException
from src.domain.entities.user import User
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.services.security_service import SecurityService

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, dto: RegisterRequestDto) -> User:
        # Check if email is already in use
        existing_user = await self.user_repo.get_by_email(dto.email.strip().lower())
        if existing_user:
            raise DomainException(
                message=f"Email '{dto.email}' is already registered", 
                error_code="EMAIL_ALREADY_EXISTS", 
                status_code=400
            )

        # Hash password
        hashed_password = SecurityService.hash_password(dto.password)

        # Create user
        user = await self.user_repo.create({
            "email": dto.email.strip().lower(),
            "password_hash": hashed_password,
            "role": dto.role,
            "refresh_token": None
        })
        return user

    async def login(self, dto: LoginRequestDto) -> TokenResponseDto:
        email = dto.email.strip().lower()
        user = await self.user_repo.get_by_email(email)
        
        if not user or not SecurityService.verify_password(dto.password, user.password_hash):
            raise DomainException(
                message="Invalid email or password", 
                error_code="INVALID_CREDENTIALS", 
                status_code=401
            )

        # Generate Token Pair
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
        access_token = SecurityService.create_access_token(token_data)
        refresh_token = SecurityService.create_refresh_token(token_data)

        # Save active refresh token in database for rotation & revocation tracking
        await self.user_repo.update_refresh_token(user.id, refresh_token)

        return TokenResponseDto(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
            role=user.role,
            user_id=user.id
        )

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponseDto:
        # Decode and validate refresh token JWT
        payload = SecurityService.decode_token(refresh_token_str)
        
        if payload.get("token_type") != "refresh":
            raise DomainException(
                message="Token is not a valid refresh token", 
                error_code="INVALID_TOKEN_TYPE", 
                status_code=401
            )

        user_id = int(payload.get("sub"))
        user = await self.user_repo.get_by_id(user_id)
        
        if not user or user.refresh_token != refresh_token_str:
            raise DomainException(
                message="Refresh token is revoked, expired or mismatched", 
                error_code="REVOKED_REFRESH_TOKEN", 
                status_code=401
            )

        # Generate NEW Token Pair (Token Rotation)
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
        new_access_token = SecurityService.create_access_token(token_data)
        new_refresh_token = SecurityService.create_refresh_token(token_data)

        # Update database with new refresh token (old one invalidated)
        await self.user_repo.update_refresh_token(user.id, new_refresh_token)

        return TokenResponseDto(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=900,
            role=user.role,
            user_id=user.id
        )

    async def logout(self, user_id: int) -> None:
        # Invalidate refresh token in database
        await self.user_repo.update_refresh_token(user_id, None)
