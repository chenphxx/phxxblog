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


def _tag_out(db: Session, tag: Tag) -> TagOut:
    """组装标签输出(含文章数)。"""
    count = (
        db.query(func.count(Post.id))
        .join(post_tags, post_tags.c.post_id == Post.id)
        .filter(post_tags.c.tag_id == tag.id, Post.status == 2)
        .scalar()
    )
    return TagOut(id=tag.id, name=tag.name, slug=tag.slug, post_count=count)


@router.get("", response_model=dict)
def list_tags(db: Session = Depends(get_db)):
    """标签列表(公开)。"""
    tags = db.query(Tag).order_by(Tag.id).all()
    return ok([_tag_out(db, t) for t in tags])


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
    return ok(_tag_out(db, tag), "创建成功")


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
    return ok(_tag_out(db, tag), "保存成功")


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
