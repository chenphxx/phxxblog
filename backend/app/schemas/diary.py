"""日记模型。"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class DiaryIn(BaseModel):
    """创建/编辑日记。"""

    content_md: str = Field(min_length=1, max_length=50000)
    entry_date: date | None = None


class DiaryOut(BaseModel):
    """日记输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    content_md: str
    content_html: str | None = None
    entry_date: date
    created_at: datetime
    updated_at: datetime
