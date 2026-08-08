"""通用模型。"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """统一分页结果。"""

    items: list[T]
    total: int
    page: int
    page_size: int
