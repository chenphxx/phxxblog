"""标签接口"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.post import Post, Tag, post_tags
from app.models.user import User
from app.schemas.post import TagIn, TagOut
from app.services.log import write_operation_log

router = APIRouter(prefix="/tags", tags=["标签"])


def _post_counts(db: Session) -> dict[int, int]:
    """一次 GROUP BY 取回所有标签的已发布文章数, 避免逐个 COUNT(n+1)"""
    rows = (
        db.query(post_tags.c.tag_id, func.count(Post.id))
        .join(post_tags, post_tags.c.post_id == Post.id)
        .filter(Post.status == 2)
        .group_by(post_tags.c.tag_id)
        .all()
    )
    return {tag_id: count for tag_id, count in rows}


def _tag_out(tag: Tag, counts: dict[int, int]) -> TagOut:
    """组装标签输出(含文章数)"""
    return TagOut(
        id=tag.id,
        name=tag.name,
        slug=tag.slug,
        color=tag.color,
        post_count=counts.get(tag.id, 0),
    )


def _ensure_unique(db: Session, *, name: str, slug: str, exclude_id: int | None = None) -> None:
    """校验标签名称与别名没有被别的记录占用

    新增与编辑都要校验: 只靠库里的唯一索引时, 重名会以 IntegrityError 收场(500),
    提示是数据库原文, 编辑的人看不出哪里错了

    @param db 数据库会话
    @param name 标签名称
    @param slug 标签别名
    @param exclude_id 编辑时传当前标签 id, 把"自己"排除掉(只改大小写是允许的)
    @throws HTTPException 名称或别名已被占用(400)
    """
    name_query = db.query(Tag).filter(Tag.name == name)
    slug_query = db.query(Tag).filter(Tag.slug == slug)
    if exclude_id is not None:
        name_query = name_query.filter(Tag.id != exclude_id)
        slug_query = slug_query.filter(Tag.id != exclude_id)
    if name_query.first():
        raise HTTPException(status_code=400, detail="标签名称已存在")
    if slug_query.first():
        raise HTTPException(status_code=400, detail="标签别名已存在")


@router.get("", response_model=dict)
def list_tags(db: Session = Depends(get_db)):
    """标签列表(公开)"""
    tags = db.query(Tag).order_by(Tag.id).all()
    counts = _post_counts(db)
    return ok([_tag_out(t, counts) for t in tags])


@router.post("", response_model=dict)
def create_tag(
    data: TagIn,
    request: Request,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新增标签"""
    _ensure_unique(db, name=data.name, slug=data.slug)
    tag = Tag(**data.model_dump())
    db.add(tag)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=_,
        module="tag",
        action="create",
        target_type="tag",
        target_id=tag.id,
        detail={"name": tag.name},
    )
    return ok(_tag_out(tag, _post_counts(db)), "创建成功")


@router.put("/{tag_id}", response_model=dict)
def update_tag(
    tag_id: int,
    data: TagIn,
    request: Request,
    _: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """编辑标签"""
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    _ensure_unique(db, name=data.name, slug=data.slug, exclude_id=tag_id)
    tag.name = data.name
    tag.slug = data.slug
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=_,
        module="tag",
        action="update",
        target_type="tag",
        target_id=tag_id,
    )
    return ok(_tag_out(tag, _post_counts(db)), "保存成功")


@router.delete("/{tag_id}", response_model=dict)
def delete_tag(
    tag_id: int,
    request: Request,
    _: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除标签"""
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    db.delete(tag)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=_,
        module="tag",
        action="delete",
        target_type="tag",
        target_id=tag_id,
    )
    return ok(message="删除成功")
