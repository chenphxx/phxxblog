"""分类接口。"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.post import Category, Post
from app.models.user import User
from app.schemas.post import CategoryIn, CategoryOut
from app.services.log import write_operation_log

router = APIRouter(prefix="/categories", tags=["分类"])


def _category_out(db: Session, category: Category) -> CategoryOut:
    """组装分类输出(含文章数)。"""
    count = (
        db.query(func.count(Post.id))
        .filter(Post.category_id == category.id, Post.status == 2)
        .scalar()
    )
    return CategoryOut(
        id=category.id, name=category.name, slug=category.slug,
        parent_id=category.parent_id, description=category.description,
        sort_order=category.sort_order, post_count=count,
    )


@router.get("", response_model=dict)
def list_categories(db: Session = Depends(get_db)):
    """分类列表(公开)。"""
    categories = db.query(Category).order_by(Category.sort_order, Category.id).all()
    return ok([_category_out(db, c) for c in categories])


@router.post("", response_model=dict)
def create_category(
    data: CategoryIn,
    request: Request,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新增分类。"""
    if db.query(Category).filter(Category.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="分类别名已存在")
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    write_operation_log(
        db, request=request, user=_, module="category", action="create",
        target_type="category", target_id=category.id, detail={"name": category.name},
    )
    return ok(_category_out(db, category), "创建成功")


@router.put("/{category_id}", response_model=dict)
def update_category(
    category_id: int,
    data: CategoryIn,
    request: Request,
    _: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """编辑分类。"""
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    for field, value in data.model_dump().items():
        setattr(category, field, value)
    db.commit()
    write_operation_log(
        db, request=request, user=_, module="category", action="update",
        target_type="category", target_id=category_id,
    )
    return ok(_category_out(db, category), "保存成功")


@router.delete("/{category_id}", response_model=dict)
def delete_category(
    category_id: int,
    request: Request,
    _: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除分类。"""
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(category)
    db.commit()
    write_operation_log(
        db, request=request, user=_, module="category", action="delete",
        target_type="category", target_id=category_id,
    )
    return ok(message="删除成功")
