"""评论模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentIn(BaseModel):
    """发表评论请求(游客/用户通用)。"""

    content: str = Field(min_length=1, max_length=2000)
    parent_id: int | None = None
    author_name: str | None = Field(default=None, max_length=50)
    author_email: str | None = Field(default=None, max_length=100)


class CommentOut(BaseModel):
    """评论输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    parent_id: int | None = None
    user_id: int | None = None
    author_name: str | None = None
    author_email: str | None = None
    content: str
    ip: str | None = None
    location: str | None = None
    status: int
    can_edit: bool = False
    can_delete: bool = False
    created_at: datetime
    replies: list["CommentOut"] = []


CommentOut.model_rebuild()
