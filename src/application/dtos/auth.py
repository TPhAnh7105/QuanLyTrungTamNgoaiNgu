from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class RegisterRequestDto(BaseModel):
    email: str = Field(..., min_length=5, max_length=100, description="Địa chỉ email")
    password: str = Field(..., min_length=6, max_length=100, description="Mật khẩu tối thiểu 6 ký tự")
    role: str = Field("Student", description="Vai trò: Admin, Teacher hoặc Student")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Email không đúng định dạng (ví dụ: user@example.com)")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v = v.strip().capitalize()
        if v not in ("Admin", "Teacher", "Student"):
            raise ValueError("Role chỉ được là một trong các giá trị: Admin, Teacher, Student")
        return v

class LoginRequestDto(BaseModel):
    email: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

class RefreshTokenRequestDto(BaseModel):
    refresh_token: str = Field(..., min_length=10, description="JWT Refresh Token đã được cấp")

class TokenResponseDto(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 phút (900 giây)
    role: str
    user_id: int

class UserResponseDto(BaseModel):
    id: int
    email: str
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
