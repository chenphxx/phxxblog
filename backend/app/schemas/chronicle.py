"""互联网纪事接口模型"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ChronicleTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
ChronicleSummary = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]
ChronicleContent = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200000)
]


class ChronicleIn(BaseModel):
    """新增或编辑互联网纪事"""

    title: ChronicleTitle
    summary: ChronicleSummary
    cover_image: str | None = Field(default=None, max_length=255)
    content_md: ChronicleContent
    status: int = Field(default=0, ge=0, le=4)


class ChronicleStatusIn(BaseModel):
    """互联网纪事状态流转请求"""

    status: int = Field(ge=0, le=4)


class ChronicleListItem(BaseModel):
    """互联网纪事卡片列表项"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str
    cover_image: str | None = None
    status: int
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChronicleDetail(ChronicleListItem):
    """互联网纪事详情"""

    content_md: str
    content_html: str | None = None
