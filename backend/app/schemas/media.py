"""媒体模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaOut(BaseModel):
    """媒体信息输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    uploader_id: int | None = None
    original_name: str
    url: str
    mime_type: str | None = None
    size: int
    type: str
    related_type: str | None = None
    related_id: int | None = None
    created_at: datetime
