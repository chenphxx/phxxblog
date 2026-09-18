"""文章查询: 前台/后台列表, 归档, 热门榜单与相邻文章。

为什么单独抽一个模块:
    这些查询原先都写在 api/v1/posts.py 里, 路由文件同时承担"解析参数, 构造查询,
    组装响应"三件事, 一个文件里塞了七个不同用途的接口; 查询条件本身又需要被测试
    单独覆盖(见 tests/test_core_rules.py), 放在路由模块里就只能连着路由函数一起调。

这里只负责"查什么", 统一返回 ORM 对象, 响应模型的组装留给路由层。
"""
from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.permissions import Perm
from app.models.post import Category, Post, Tag
from app.models.user import User
from app.services.post_write import STATUS_PUBLISHED


def public_list(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 10,
    category: int | None = None,
    tag: int | None = None,
    year: int | None = None,
    month: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    keyword: str | None = None,
) -> tuple[list[Post], int]:
    """前台文章列表查询(仅已发布), 返回 (当页文章, 满足条件的总数)。

    @param db 数据库会话
    @param category 分类ID(多对多关联表筛选)
    @param tag 标签ID
    @param year 按发布年份筛选
    @param month 按发布月份筛选
    @param start_date 发布起始日 YYYY-MM-DD(含当日)
    @param end_date 发布结束日 YYYY-MM-DD(含当日)
    @param keyword 关键词, 匹配标题或摘要
    @return (当页文章, 总数)
    """
    query = db.query(Post).filter(Post.status == STATUS_PUBLISHED)
    if category:
        query = query.join(Post.categories).filter(Category.id == category)
    if tag:
        query = query.join(Post.tags).filter(Tag.id == tag)
    if year:
        query = query.filter(func.year(Post.published_at) == year)
    if month:
        query = query.filter(func.month(Post.published_at) == month)
    if start_date:
        query = query.filter(Post.published_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        # 结束日含当天, 所以下界用次日零点
        query = query.filter(
            Post.published_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        )
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(Post.title.like(like), Post.summary.like(like)))

    total = query.count()
    items = (
        query.order_by(Post.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def admin_list(
    db: Session,
    *,
    user: User,
    page: int = 1,
    page_size: int = 10,
    status: int | None = None,
    keyword: str | None = None,
) -> tuple[list[Post], int]:
    """后台文章管理列表查询(管理员看全部, 作者只看自己), 返回 (当页文章, 总数)。"""
    query = db.query(Post)
    if Perm.POST_MANAGE not in user.permission_codes:
        query = query.filter(Post.author_id == user.id)
    if status is not None:
        query = query.filter(Post.status == status)
    if keyword:
        query = query.filter(Post.title.like(f"%{keyword}%"))
    total = query.count()
    items = (
        query.order_by(Post.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def month_groups(db: Session) -> list[tuple[int, int, list[Post]]]:
    """按 年-月 分组返回全部已发布文章, 月份新的在前。

    没有发布时间的文章(理论上已发布文章都有, 但历史数据可能缺)按创建时间归组,
    避免它们从归档里凭空消失。

    @return [(年, 月, 该月文章), ...]
    """
    posts = (
        db.query(Post)
        .filter(Post.status == STATUS_PUBLISHED)
        .order_by(Post.published_at.desc())
        .all()
    )
    groups: dict[tuple[int, int], list[Post]] = {}
    for post in posts:
        published_at = post.published_at or post.created_at
        groups.setdefault((published_at.year, published_at.month), []).append(post)
    return [(key[0], key[1], items) for key, items in sorted(groups.items(), reverse=True)]


def hot(db: Session, limit: int = 7) -> list[Post]:
    """热门文章查询(按浏览量倒序, 仅已发布)。

    浏览量相同时按 id 倒序, 保证多次请求的顺序稳定(否则榜单会随机跳动)。
    """
    return (
        db.query(Post)
        .filter(Post.status == STATUS_PUBLISHED)
        .order_by(Post.views.desc(), Post.id.desc())
        .limit(limit)
        .all()
    )


def neighbors(db: Session, post: Post) -> tuple[Post | None, Post | None]:
    """查询同一发布序列中紧邻的上一篇(更早)与下一篇(更晚)。

    只在已发布文章之间取邻居, 非已发布文章(草稿预览等)没有"上一篇/下一篇"的语义。

    @param db 数据库会话
    @param post 当前文章
    @return (上一篇, 下一篇), 不存在时对应项为 None
    """
    if post.status != STATUS_PUBLISHED or post.published_at is None:
        return None, None
    published = db.query(Post).filter(Post.status == STATUS_PUBLISHED)
    prev_post = (
        published.filter(Post.published_at < post.published_at)
        .order_by(Post.published_at.desc(), Post.id.desc())
        .first()
    )
    next_post = (
        published.filter(Post.published_at > post.published_at)
        .order_by(Post.published_at.asc(), Post.id.asc())
        .first()
    )
    return prev_post, next_post
