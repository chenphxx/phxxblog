"""认证相关模型。"""
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    """注册请求。"""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=50)


class LoginIn(BaseModel):
    """登录请求。"""

    username: str
    password: str


class TokenPair(BaseModel):
    """令牌对。"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    """刷新令牌请求。"""

    refresh_token: str


class PasswordChangeIn(BaseModel):
    """修改密码请求。"""

    old_password: str
    new_password: str = Field(min_length=6, max_length=64)


class EmailChangeIn(BaseModel):
    """修改邮箱请求。"""

    email: EmailStr


class ProfileUpdateIn(BaseModel):
    """修改用户名/昵称请求。"""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
