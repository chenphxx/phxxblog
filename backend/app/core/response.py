"""统一响应结构。"""
from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一 API 响应: { code, message, data }。"""

    code: int = 0
    message: str = "ok"
    data: Any = None


def ok(data: Any = None, message: str = "ok") -> ApiResponse:
    """构造成功响应(以字典返回, 兼容 response_model=dict)。"""
    return {"code": 0, "message": message, "data": data}  # type: ignore[return-value]
