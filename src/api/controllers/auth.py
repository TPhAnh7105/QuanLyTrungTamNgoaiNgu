from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.connection import get_db_session
from src.application.dtos.auth import (
    RegisterRequestDto, 
    LoginRequestDto, 
    RefreshTokenRequestDto, 
    TokenResponseDto, 
    UserResponseDto
)
from src.application.services.auth_service import AuthService
from src.api.dependencies import get_current_user
from src.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

@router.post("/register", response_model=UserResponseDto, status_code=status.HTTP_201_CREATED)
async def register(
    dto: RegisterRequestDto,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Đăng ký tài khoản người dùng mới (Admin / Teacher / Student) kèm mật khẩu băm bcrypt an toàn.
    """
    auth_service = AuthService(db)
    user = await auth_service.register(dto)
    return user

@router.post("/login", response_model=TokenResponseDto)
async def login(
    dto: LoginRequestDto,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Đăng nhập hệ thống: Trả về cặp JWT Access Token (15 phút) và Refresh Token (7 ngày).
    """
    auth_service = AuthService(db)
    tokens = await auth_service.login(dto)
    return tokens

@router.post("/refresh", response_model=TokenResponseDto)
async def refresh_token(
    dto: RefreshTokenRequestDto,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Xoay vòng Refresh Token: Cấp cặp Access + Refresh Token mới và thu hồi Refresh Token cũ.
    """
    auth_service = AuthService(db)
    tokens = await auth_service.refresh_tokens(dto.refresh_token)
    return tokens

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Đăng xuất: Thu hồi Refresh Token của người dùng hiện tại trong cơ sở dữ liệu.
    """
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id)
    return {"message": "Logged out successfully. Refresh token revoked."}

@router.get("/me", response_model=UserResponseDto)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Lấy thông tin tài khoản và vai trò của người dùng hiện tại từ JWT Access Token.
    """
    return current_user
