"""文章/分类/标签模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    """分类输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: int | None = None
    description: str | None = None
    sort_order: int
    post_count: int = 0


class CategoryIn(BaseModel):
    """分类创建/编辑。"""

    name: str = Field(min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=80)
    parent_id: int | None = None
    description: str | None = None
    sort_order: int = 0


class TagOut(BaseModel):
    """标签输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    post_count: int = 0


class TagIn(BaseModel):
    """标签创建/编辑。"""

    name: str = Field(min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=80)


class PostBase(BaseModel):
    """文章公共字段。"""

    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(default="", max_length=220)
    summary: str | None = Field(default=None, max_length=500)
    content_md: str = ""
    cover_image: str | None = None
    category_id: int | None = None
    tag_ids: list[int] = []
    status: int = Field(default=0, ge=0, le=4)


class PostCreate(PostBase):
    """新增文章。"""


class PostUpdate(PostBase):
    """编辑文章。"""


class PostListItem(BaseModel):
    """文章列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    summary: str | None = None
    cover_image: str | None = None
    status: int
    views: int
    likes_count: int
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    category: CategoryOut | None = None
    tags: list[TagOut] = []
    author: "UserBrief | None" = None


class UserBrief(BaseModel):
    """作者简要信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    avatar: str | None = None


PostListItem.model_rebuild()


class PostDetail(PostListItem):
    """文章详情。"""

    content_md: str
    content_html: str | None = None
    ip: str | None = None
    location: str | None = None


class PostStatusIn(BaseModel):
    """状态变更请求(发布/恢复等)。"""

    status: int = Field(ge=0, le=4)


class LikeResult(BaseModel):
    """点赞结果。"""

    liked: bool
    likes_count: int


class ArchiveGroup(BaseModel):
    """归档分组(按年月)。"""

    year: int
    month: int
    count: int
    posts: list[PostListItem]
