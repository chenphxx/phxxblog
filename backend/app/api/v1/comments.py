"""评论接口: 前台发表/查看, 后台管理。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_client_ip, get_current_user, get_optional_user, require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.analytics import DailyStat
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentIn, CommentOut
from app.schemas.common import Page
from app.services.geo import resolve_location
from app.services.log import write_operation_log

router = APIRouter(tags=["评论"])


def _build_tree(items: list[Comment]) -> list[CommentOut]:
    """把平铺评论按 parent_id 组装成树。

    注意: model_validate 会读取 ORM 的 replies 关系, 必须先清空,
    否则子评论会被关系装载一次、循环又追加一次, 造成重复。
    """
    nodes: dict[int, CommentOut] = {}
    for comment in items:
        node = CommentOut.model_validate(comment)
        node.replies = []
        nodes[comment.id] = node
    roots: list[CommentOut] = []
    for comment in items:
        node = nodes[comment.id]
        if comment.parent_id in nodes:
            nodes[comment.parent_id].replies.append(node)
        else:
            roots.append(node)
    return roots


def _can_manage_comment(comment: Comment, user: User | None, ip: str) -> tuple[bool, bool]:
    """判断当前请求能否编辑/删除评论(管理员/作者本人/同 IP 游客)。"""
    if user is not None:
        if "admin" in user.role_codes or user.id == comment.user_id:
            return True, True
        return False, False
    # 游客: 同 IP 且为游客评论
    if comment.user_id is None and comment.ip and comment.ip == ip:
        return True, True
    return False, False


@router.get("/posts/{post_id}/comments", response_model=dict)
def list_comments(
    post_id: int,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """文章评论列表(公开, 按时间正序组装成树)。"""
    if db.get(Post, post_id) is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    ip = get_client_ip(request)
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.status == 1)
        .order_by(Comment.created_at.asc())
        .all()
    )
    for comment in comments:
        comment.can_edit, comment.can_delete = _can_manage_comment(comment, user, ip)
    return ok(_build_tree(comments))


@router.post("/posts/{post_id}/comments", response_model=dict)
def create_comment(
    post_id: int,
    data: CommentIn,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """发表评论(游客需提供昵称, 登录用户自动使用账号信息)。"""
    post = db.get(Post, post_id)
    if post is None or post.status != 2:
        raise HTTPException(status_code=404, detail="文章不存在")
    if data.parent_id:
        parent = db.get(Comment, data.parent_id)
        if parent is None or parent.post_id != post_id:
            raise HTTPException(status_code=400, detail="父评论不存在")

    ip = get_client_ip(request)
    location = resolve_location(ip)

    if user:
        comment = Comment(
            post_id=post_id,
            parent_id=data.parent_id,
            user_id=user.id,
            author_name=user.nickname,
            author_email=user.email,
            content=data.content,
            ip=ip,
            location=location,
        )
    else:
        if not data.author_name:
            raise HTTPException(status_code=400, detail="游客评论请填写昵称")
        comment = Comment(
            post_id=post_id,
            parent_id=data.parent_id,
            author_name=data.author_name,
            author_email=data.author_email,
            content=data.content,
            ip=ip,
            location=location,
        )
    db.add(comment)

    today_stat = db.query(DailyStat).filter(DailyStat.stat_date == datetime.now().date()).first()
    if today_stat is None:
        today_stat = DailyStat(stat_date=datetime.now().date())
        db.add(today_stat)
    today_stat.comments = (today_stat.comments or 0) + 1
    db.commit()
    return ok(CommentOut.model_validate(comment), "评论成功")


@router.get("/comments/admin", response_model=dict)
def admin_list_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: int | None = Query(None, description="1正常 0隐藏 2回收站"),
    post_id: int | None = None,
    _: User = Depends(require_permission(Perm.COMMENT_MANAGE)),
    db: Session = Depends(get_db),
):
    """后台评论管理列表。"""
    query = db.query(Comment)
    if status is not None:
        query = query.filter(Comment.status == status)
    if post_id:
        query = query.filter(Comment.post_id == post_id)
    total = query.count()
    items = (
        query.order_by(Comment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(Page[CommentOut](
        items=[CommentOut.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size,
    ))


@router.put("/comments/{comment_id}", response_model=dict)
def update_comment(
    comment_id: int,
    data: CommentIn,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """编辑评论内容(管理员/作者本人/同 IP 游客)。"""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    can_edit, _ = _can_manage_comment(comment, user, get_client_ip(request))
    if not can_edit:
        raise HTTPException(status_code=403, detail="只能编辑自己的评论")
    comment.content = data.content
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="comment", action="update",
        target_type="comment", target_id=comment_id,
    )
    return ok(CommentOut.model_validate(comment), "评论已更新")


@router.patch("/comments/{comment_id}/status", response_model=dict)
def update_comment_status(
    comment_id: int,
    request: Request,
    status: int = Query(ge=0, le=2),
    admin: User = Depends(require_permission(Perm.COMMENT_MANAGE)),
    db: Session = Depends(get_db),
):
    """修改评论状态(管理员: 隐藏/显示/回收站)。"""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    comment.status = status
    db.commit()
    write_operation_log(
        db, request=request, user=admin, module="comment", action=f"status:{status}",
        target_type="comment", target_id=comment_id,
    )
    return ok(message="状态已更新")


@router.delete("/comments/{comment_id}", response_model=dict)
def delete_comment(
    comment_id: int,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """删除评论(管理员/作者本人/同 IP 游客, 级联删除回复)。"""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    _, can_delete = _can_manage_comment(comment, user, get_client_ip(request))
    if not can_delete:
        raise HTTPException(status_code=403, detail="只能删除自己的评论")
    db.delete(comment)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="comment", action="delete",
        target_type="comment", target_id=comment_id,
    )
    return ok(message="删除成功")
