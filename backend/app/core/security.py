"""安全相关: 密码散列与 JWT 令牌。"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """使用 bcrypt 生成密码散列。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码与散列是否匹配。"""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """生成 JWT 访问令牌(短期)。"""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """解码并校验 JWT, 失败抛出 jwt.PyJWTError。"""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def generate_refresh_token() -> str:
    """生成随机刷新令牌(原始值)。"""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """对刷新令牌做 SHA-256 散列, 数据库只存散列值。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
