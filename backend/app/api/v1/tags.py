"""标签接口。"""
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
    """一次 GROUP BY 取回所有标签的已发布文章数, 避免逐个 COUNT(n+1)。"""
    rows = (
        db.query(post_tags.c.tag_id, func.count(Post.id))
        .join(post_tags, post_tags.c.post_id == Post.id)
        .filter(Post.status == 2)
        .group_by(post_tags.c.tag_id)
        .all()
    )
    return {tag_id: count for tag_id, count in rows}


def _tag_out(tag: Tag, counts: dict[int, int]) -> TagOut:
    """组装标签输出(含文章数)。"""
    return TagOut(
        id=tag.id, name=tag.name, slug=tag.slug, color=tag.color,
        post_count=counts.get(tag.id, 0),
    )


@router.get("", response_model=dict)
def list_tags(db: Session = Depends(get_db)):
    """标签列表(公开)。"""
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
    """新增标签。"""
    if db.query(Tag).filter(Tag.name == data.name).first():
        raise HTTPException(status_code=400, detail="标签名已存在")
    tag = Tag(**data.model_dump())
    db.add(tag)
    db.commit()
    write_operation_log(
        db, request=request, user=_, module="tag", action="create",
        target_type="tag", target_id=tag.id, detail={"name": tag.name},
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
    """编辑标签。"""
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    tag.name = data.name
    tag.slug = data.slug
    db.commit()
    write_operation_log(
        db, request=request, user=_, module="tag", action="update",
        target_type="tag", target_id=tag_id,
    )
    return ok(_tag_out(tag, _post_counts(db)), "保存成功")


@router.delete("/{tag_id}", response_model=dict)
def delete_tag(
    tag_id: int,
    request: Request,
    _: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除标签。"""
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    db.delete(tag)
    db.commit()
    write_operation_log(
        db, request=request, user=_, module="tag", action="delete",
        target_type="tag", target_id=tag_id,
    )
    return ok(message="删除成功")
