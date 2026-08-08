"""文章接口: 前台浏览、后台管理、发布流程、点赞、归档。"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    get_client_ip,
    get_current_user,
    get_optional_user,
    require_permission,
)
from app.core.permissions import Perm
from app.core.response import ok
from app.models.analytics import DailyStat
from app.models.post import Category, Post, PostLike, Tag
from app.models.user import User
from app.schemas.common import Page
from app.schemas.post import (
    ArchiveGroup,
    CategoryOut,
    LikeResult,
    PostCreate,
    PostDetail,
    PostListItem,
    PostStatusIn,
    PostUpdate,
    TagOut,
)
from app.services.log import write_operation_log
from app.services.markdown import render_markdown
from app.services.geo import resolve_location
from app.services.stats import record_visit

router = APIRouter(prefix="/posts", tags=["文章"])


def _can_manage(user: User, post: Post) -> bool:
    """作者本人或拥有 post:manage 权限可管理该文章。"""
    return user.id == post.author_id or Perm.POST_MANAGE in user.permission_codes


def _auto_slug(data_slug: str, title: str) -> str:
    """生成文章 slug: 优先使用传入值, 否则生成唯一短标识。"""
    if data_slug:
        return data_slug
    return f"post-{uuid.uuid4().hex[:8]}"


def _apply_payload(
    db: Session,
    post: Post,
    data: PostCreate | PostUpdate,
    user: User,
    request: Request,
) -> None:
    """将请求字段应用到文章(含状态规则、标签、HTML 渲染)。"""
    target_status = data.status
    # 非管理员不能直接发布/置私密, 降级为审核中
    if target_status in (2, 3) and Perm.POST_PUBLISH not in user.permission_codes:
        target_status = 1
    if target_status == 4 and Perm.POST_MANAGE not in user.permission_codes:
        target_status = 1

    post.title = data.title
    post.slug = _auto_slug(data.slug, data.title)
    post.summary = data.summary
    post.content_md = data.content_md
    post.content_html = render_markdown(data.content_md)
    post.cover_image = data.cover_image
    post.category_id = data.category_id
    post.status = target_status
    post.ip = get_client_ip(request)
    post.location = resolve_location(post.ip)

    if target_status == 2 and post.published_at is None:
        post.published_at = datetime.now()

    # 标签
    if data.tag_ids:
        post.tags = db.query(Tag).filter(Tag.id.in_(data.tag_ids)).all()


@router.get("", response_model=dict)
def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: int | None = Query(None, description="分类ID"),
    tag: int | None = Query(None, description="标签ID"),
    year: int | None = Query(None, description="年份筛选"),
    month: int | None = Query(None, description="月份筛选"),
    keyword: str | None = Query(None, description="关键词(标题/摘要)"),
    db: Session = Depends(get_db),
):
    """前台文章列表(仅已发布)。"""
    query = db.query(Post).filter(Post.status == 2)
    if category:
        query = query.filter(Post.category_id == category)
    if tag:
        query = query.join(Post.tags).filter(Tag.id == tag)
    if year:
        query = query.filter(func.year(Post.published_at) == year)
    if month:
        query = query.filter(func.month(Post.published_at) == month)
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
    return ok(Page[PostListItem](
        items=[PostListItem.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    ))


@router.get("/archive", response_model=dict)
def archive(db: Session = Depends(get_db)):
    """归档: 按 年-月 分组展示所有已发布文章。"""
    posts = (
        db.query(Post)
        .filter(Post.status == 2)
        .order_by(Post.published_at.desc())
        .all()
    )
    groups: dict[tuple[int, int], list[Post]] = {}
    for post in posts:
        published_at = post.published_at or post.created_at
        key = (published_at.year, published_at.month)
        groups.setdefault(key, []).append(post)
    result = [
        ArchiveGroup(
            year=key[0],
            month=key[1],
            count=len(items),
            posts=[PostListItem.model_validate(p) for p in items],
        )
        for key, items in sorted(groups.items(), reverse=True)
    ]
    return ok(result)


@router.get("/admin", response_model=dict)
def admin_list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: int | None = Query(None, description="0草稿 1审核中 2已发布 3私密 4回收站"),
    keyword: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """后台文章管理列表(管理员看全部, 作者只看自己)。"""
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
    return ok(Page[PostListItem](
        items=[PostListItem.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    ))


@router.get("/{post_id}", response_model=dict)
def get_post(
    post_id: int,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """文章详情(已发布公开, 非公开仅作者/管理员可见)。"""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if post.status != 2:
        if user is None or not _can_manage(user, post):
            raise HTTPException(status_code=404, detail="文章不存在")
    if post.status == 2:
        record_visit(db, request=request, post=post)
    return ok(PostDetail.model_validate(post))


@router.post("", response_model=dict)
def create_post(
    data: PostCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新增文章(默认草稿, 可提交审核)。"""
    if Perm.POST_CREATE not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:create")
    post = Post(author_id=user.id)
    _apply_payload(db, post, data, user, request)
    db.add(post)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="create",
        target_type="post", target_id=post.id, detail={"title": post.title},
    )
    return ok(PostDetail.model_validate(post), "已保存")


@router.put("/{post_id}", response_model=dict)
def update_post(
    post_id: int,
    data: PostUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑文章。"""
    if Perm.POST_EDIT not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:edit")
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not _can_manage(user, post):
        raise HTTPException(status_code=403, detail="只能编辑自己的文章")
    _apply_payload(db, post, data, user, request)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="update",
        target_type="post", target_id=post.id, detail={"title": post.title},
    )
    return ok(PostDetail.model_validate(post), "保存成功")


@router.delete("/{post_id}", response_model=dict)
def trash_post(
    post_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除文章(移入回收站)。"""
    if Perm.POST_DELETE not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:delete")
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not _can_manage(user, post):
        raise HTTPException(status_code=403, detail="只能删除自己的文章")
    post.status = 4
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="trash",
        target_type="post", target_id=post_id,
    )
    return ok(message="已移入回收站")


@router.delete("/{post_id}/force", response_model=dict)
def force_delete_post(
    post_id: int,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """彻底删除文章。"""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    title = post.title
    db.delete(post)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="force_delete",
        target_type="post", target_id=post_id, detail={"title": title},
    )
    return ok(message="已彻底删除")


@router.post("/{post_id}/restore", response_model=dict)
def restore_post(
    post_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从回收站恢复(恢复为草稿)。"""
    post = db.get(Post, post_id)
    if post is None or post.status != 4:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not _can_manage(user, post):
        raise HTTPException(status_code=403, detail="无权限")
    post.status = 0
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="restore",
        target_type="post", target_id=post_id,
    )
    return ok(message="已恢复为草稿")


@router.post("/{post_id}/publish", response_model=dict)
def change_post_status(
    post_id: int,
    data: PostStatusIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """状态流转: 0草稿 1审核中(提交审核) 2发布 3私密。"""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not _can_manage(user, post):
        raise HTTPException(status_code=403, detail="只能操作自己的文章")

    target = data.status
    if target == 2:
        if Perm.POST_PUBLISH not in user.permission_codes:
            raise HTTPException(status_code=403, detail="缺少权限: post:publish")
        post.published_at = datetime.now()
    elif target == 3 and Perm.POST_MANAGE not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:manage")
    post.status = target
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action=f"status:{target}",
        target_type="post", target_id=post_id,
    )
    status_names = {0: "草稿", 1: "审核中", 2: "已发布", 3: "私密", 4: "回收站"}
    return ok(message=f"已切换为{status_names.get(target, target)}")


@router.post("/{post_id}/like", response_model=dict)
def like_post(
    post_id: int,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """点赞/取消点赞(游客按 IP 去重, 登录用户按账号去重)。"""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    ip = get_client_ip(request)

    query = db.query(PostLike).filter(PostLike.post_id == post_id)
    existing = (
        query.filter(PostLike.user_id == user.id).first()
        if user
        else query.filter(PostLike.ip == ip).first()
    )

    if existing:
        db.delete(existing)
        post.likes_count = max(0, post.likes_count - 1)
        liked = False
    else:
        db.add(PostLike(post_id=post_id, user_id=user.id if user else None, ip=ip))
        post.likes_count += 1
        liked = True
        today_stat = db.query(DailyStat).filter(DailyStat.stat_date == datetime.now().date()).first()
        if today_stat is None:
            today_stat = DailyStat(stat_date=datetime.now().date())
            db.add(today_stat)
        today_stat.likes = (today_stat.likes or 0) + 1

    db.commit()
    return ok(LikeResult(liked=liked, likes_count=post.likes_count))
