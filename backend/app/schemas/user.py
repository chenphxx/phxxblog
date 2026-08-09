"""用户/角色/权限模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    """用户信息输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    nickname: str
    avatar: str | None = None
    bio: str | None = None
    website: str | None = None
    social: dict | None = None
    status: int
    role_codes: list[str] = []
    last_login_at: datetime | None = None
    created_at: datetime


class UserCreate(BaseModel):
    """创建用户(管理端)。"""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=50)
    roles: list[str] = []


class UserUpdate(BaseModel):
    """编辑用户(管理端)。"""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    avatar: str | None = None
    bio: str | None = None
    website: str | None = None
    social: dict | None = None
    status: int | None = Field(default=None, ge=0, le=1)
    roles: list[str] | None = None


class PasswordResetIn(BaseModel):
    """重置密码(管理员操作)。"""

    password: str = Field(min_length=6, max_length=64)


class RoleOut(BaseModel):
    """角色信息输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None = None
    permission_codes: list[str] = []


class RoleIn(BaseModel):
    """角色创建/编辑。"""

    name: str = Field(min_length=1, max_length=50)
    code: str = Field(min_length=1, max_length=50)
    description: str | None = None
    permission_codes: list[str] = []


class PermissionOut(BaseModel):
    """权限信息输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None = None
