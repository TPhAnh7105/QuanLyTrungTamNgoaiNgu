from fastapi import APIRouter, Header, status
from sqlalchemy import text
from typing import Optional
import uuid

from src.infrastructure.database.connection import AsyncSessionLocal
from src.application.dtos.auth import (
    RegisterRequestDto, 
    LoginRequestDto, 
    RefreshTokenRequestDto, 
    TokenResponseDto, 
    UserResponseDto
)
from src.infrastructure.services.security_service import SecurityService
from src.domain.exceptions.base import DomainException
from src.api.auth_helper import verify_auth_sql

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC (Direct SQL Queries)"])

@router.post("/register", response_model=UserResponseDto, status_code=status.HTTP_201_CREATED)
async def register(dto: RegisterRequestDto):
    """
    Đăng ký tài khoản người dùng mới bằng SQL Query.
    """
    async with AsyncSessionLocal() as session:
        # 1. Kiểm tra email tồn tại
        exist_res = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": dto.email}
        )
        if exist_res.mappings().first():
            raise DomainException("Email đã tồn tại trên hệ thống", error_code="EMAIL_EXISTS", status_code=409)

        # 2. Băm mật khẩu
        hashed_password = SecurityService.hash_password(dto.password)

        # 3. Insert user mới
        insert_query = text("""
            INSERT INTO users (email, password_hash, role, refresh_token, created_at)
            VALUES (:email, :password_hash, :role, NULL, NOW())
        """)
        await session.execute(insert_query, {
            "email": dto.email,
            "password_hash": hashed_password,
            "role": dto.role
        })
        await session.commit()

        # 4. Trả về user
        get_res = await session.execute(
            text("SELECT id, email, role, created_at FROM users WHERE email = :email"),
            {"email": dto.email}
        )
        user = get_res.mappings().first()
        return dict(user)

@router.post("/login", response_model=TokenResponseDto)
async def login(dto: LoginRequestDto):
    """
    Đăng nhập hệ thống bằng SQL Query.
    """
    async with AsyncSessionLocal() as session:
        # 1. Tìm user theo email
        res = await session.execute(
            text("SELECT id, email, password_hash, role FROM users WHERE email = :email"),
            {"email": dto.email}
        )
        user = res.mappings().first()
        if not user:
            raise DomainException("Email hoặc mật khẩu không chính xác", error_code="INVALID_CREDENTIALS", status_code=401)

        # 2. Xác thực mật khẩu
        if not SecurityService.verify_password(dto.password, user["password_hash"]):
            raise DomainException("Email hoặc mật khẩu không chính xác", error_code="INVALID_CREDENTIALS", status_code=401)

        # 3. Sinh token
        access_token = SecurityService.create_access_token({"sub": str(user["id"]), "email": user["email"], "role": user["role"]})
        refresh_token = SecurityService.create_refresh_token({"sub": str(user["id"]), "email": user["email"], "role": user["role"], "jti": str(uuid.uuid4())})

        # 4. Lưu refresh token vào DB
        await session.execute(
            text("UPDATE users SET refresh_token = :token WHERE id = :id"),
            {"token": refresh_token, "id": user["id"]}
        )
        await session.commit()

        return TokenResponseDto(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
            role=user["role"],
            user_id=user["id"]
        )

@router.post("/refresh", response_model=TokenResponseDto)
async def refresh_token(dto: RefreshTokenRequestDto):
    """
    Xoay vòng Refresh Token bằng SQL Query.
    """
    payload = SecurityService.decode_token(dto.refresh_token)
    if not payload or payload.get("token_type") != "refresh":
        raise DomainException("Refresh Token không hợp lệ hoặc đã hết hạn", error_code="INVALID_REFRESH_TOKEN", status_code=401)

    user_id = int(payload.get("sub"))
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            text("SELECT id, email, role, refresh_token FROM users WHERE id = :id"),
            {"id": user_id}
        )
        user = res.mappings().first()
        if not user or user["refresh_token"] != dto.refresh_token:
            raise DomainException("Refresh Token không khớp hoặc đã bị thu hồi", error_code="REVOKED_TOKEN", status_code=401)

        new_access_token = SecurityService.create_access_token({"sub": str(user["id"]), "email": user["email"], "role": user["role"]})
        new_refresh_token = SecurityService.create_refresh_token({"sub": str(user["id"]), "email": user["email"], "role": user["role"], "jti": str(uuid.uuid4())})

        await session.execute(
            text("UPDATE users SET refresh_token = :token WHERE id = :id"),
            {"token": new_refresh_token, "id": user["id"]}
        )
        await session.commit()

        return TokenResponseDto(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=900,
            role=user["role"],
            user_id=user["id"]
        )

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(authorization: Optional[str] = Header(None)):
    """
    Đăng xuất bằng SQL Query.
    """
    user = await verify_auth_sql(authorization)
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("UPDATE users SET refresh_token = NULL WHERE id = :id"),
            {"id": user["id"]}
        )
        await session.commit()
    return {"message": "Logged out successfully. Refresh token revoked."}

@router.get("/me", response_model=UserResponseDto)
async def get_my_profile(authorization: Optional[str] = Header(None)):
    """
    Lấy thông tin tài khoản hiện tại bằng SQL Query.
    """
    user = await verify_auth_sql(authorization)
    return user
