"""文章写入相关的业务规则。

为什么单独抽一个模块:
    以前"谁能把文章改成什么状态"这条规则散落在三处, 而且已经**不一致**:
      - api/v1/posts.py::_apply_payload    (新增/修改) 无权限时静默降级为"审核中"
      - api/v1/posts.py::_import_markdown  (导入)     无权限时降级为"草稿"
      - api/v1/posts.py::change_post_status(状态流转) 无权限时**抛 403**
    三处各写一遍, 改一处忘两处。现在统一到这里, 路由只负责取参与返回。
"""
from sqlalchemy.orm import Session

from app.core.permissions import Perm
from app.models.post import Category, Post, Tag
from app.models.user import User

# 文章状态: 0草稿 1审核中 2已发布 3私密 4回收站
STATUS_DRAFT = 0
STATUS_REVIEW = 1
STATUS_PUBLISHED = 2
STATUS_PRIVATE = 3
STATUS_TRASH = 4

STATUS_NAMES: dict[int, str] = {
    STATUS_DRAFT: "草稿",
    STATUS_REVIEW: "审核中",
    STATUS_PUBLISHED: "已发布",
    STATUS_PRIVATE: "私密",
    STATUS_TRASH: "回收站",
}

# 需要 post:publish 才能直接落到的状态
NEEDS_PUBLISH = (STATUS_PUBLISHED,)
# 需要 post:manage 才能直接落到的状态
NEEDS_MANAGE = (STATUS_PRIVATE, STATUS_TRASH)


def can_manage(user: User, post: Post) -> bool:
    """作者本人或拥有 post:manage 权限即可管理该文章。"""
    return user.id == post.author_id or Perm.POST_MANAGE in user.permission_codes


def resolve_submitted_status(raw_status: int, user: User) -> int:
    """把"提交上来的状态"收敛为"实际落库的状态"。

    用于新增/修改/导入三条写入路径:
      - 有 post:publish -> 允许"已发布"
      - 有 post:manage  -> 允许"私密"与"回收站"
      - 其它情况: 只能停在 草稿/审核中, 越权的目标状态降级为"审核中"
        (静默降级是刻意设计: 作者提交发布请求时不该收到报错, 而是进入审核队列)
    """
    if raw_status in NEEDS_PUBLISH and Perm.POST_PUBLISH not in user.permission_codes:
        return STATUS_REVIEW
    if raw_status in NEEDS_MANAGE and Perm.POST_MANAGE not in user.permission_codes:
        return STATUS_REVIEW
    if raw_status in (STATUS_DRAFT, STATUS_REVIEW, STATUS_PUBLISHED, STATUS_PRIVATE, STATUS_TRASH):
        return raw_status
    return STATUS_REVIEW


def require_status_transition(target: int, user: User) -> None:
    """状态流转接口的权限校验(这里**报错**而不是降级: 用户明确点了某个按钮)。

    Raises:
        HTTPException: 403, 缺少对应权限。
    """
    from fastapi import HTTPException

    if target in NEEDS_PUBLISH and Perm.POST_PUBLISH not in user.permission_codes:
        raise HTTPException(status_code=403, detail=f"缺少权限: {Perm.POST_PUBLISH}")
    if target in NEEDS_MANAGE and Perm.POST_MANAGE not in user.permission_codes:
        raise HTTPException(status_code=403, detail=f"缺少权限: {Perm.POST_MANAGE}")


def resolve_tags(db: Session, tag_ids: list[int] | None) -> list[Tag]:
    """按 id 取标签。"""
    if not tag_ids:
        return []
    return db.query(Tag).filter(Tag.id.in_(tag_ids)).all()


def resolve_categories(db: Session, category_ids: list[int] | None) -> list[Category]:
    """按 id 取分类(一篇文章可以多选分类, 见 models/post.py 的 post_categories)。"""
    if not category_ids:
        return []
    return db.query(Category).filter(Category.id.in_(category_ids)).all()


def resolve_category_by_name(db: Session, name: str, unique_slug) -> Category:
    """按名称找分类, 不存在则新建(导入时用)。

    Args:
        unique_slug: 由调用方注入的 slug 去重函数(见 services/archive.py),
            避免本模块反向依赖具体实现。
    """
    name = name.strip()
    existing = (
        db.query(Category)
        .filter(Category.name == name[:50])
        .first()
    )
    if existing is not None:
        return existing
    from sqlalchemy import func

    existing = (
        db.query(Category)
        .filter(func.lower(Category.name) == name.lower())
        .first()
    )
    if existing is not None:
        return existing
    category = Category(name=name[:50], slug=unique_slug(name[:80]))
    db.add(category)
    db.flush()
    return category


def resolve_categories_by_name(db: Session, names: list[str], unique_slug) -> list[Category]:
    """按名称批量取分类, 不存在则新建(导入时用); 按传入顺序去重返回。

    Args:
        names: frontmatter 里的分类名列表(新旧格式都已在调用方归一化)。
        unique_slug: 由调用方注入的 slug 去重函数(见 services/archive.py)。
    """
    result: list[Category] = []
    seen: set[int] = set()
    for raw_name in names:
        name = str(raw_name).strip()
        if not name:
            continue
        category = resolve_category_by_name(db, name, unique_slug)
        if category.id in seen:
            continue
        seen.add(category.id)
        result.append(category)
    return result
