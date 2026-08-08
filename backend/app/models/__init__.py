"""ORM 模型汇总, 确保所有表注册到 Base.metadata。"""
from app.models.analytics import DailyStat, VisitLog
from app.models.comment import Comment
from app.models.diary import DiaryEntry
from app.models.log import OperationLog
from app.models.media import Media
from app.models.post import Category, Post, PostLike, Tag, post_tags
from app.models.setting import Setting
from app.models.user import Permission, Role, User, refresh_tokens, role_permissions, user_roles

__all__ = [
    "User",
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    "refresh_tokens",
    "Category",
    "Tag",
    "Post",
    "PostLike",
    "post_tags",
    "Comment",
    "DiaryEntry",
    "Media",
    "VisitLog",
    "DailyStat",
    "OperationLog",
    "Setting",
]
