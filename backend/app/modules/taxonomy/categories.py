"""分类接口"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.post import Category, Post, post_categories
from app.models.user import User
from app.schemas.post import CategoryIn, CategoryOut
from app.services.log import write_operation_log

router = APIRouter(prefix="/categories", tags=["分类"])


def _post_counts(db: Session) -> dict[int, int]:
    """一次 GROUP BY 取回所有分类的已发布文章数, 避免逐个 COUNT(n+1)"""
    rows = (
        db.query(post_categories.c.category_id, func.count(post_categories.c.post_id))
        .join(Post, Post.id == post_categories.c.post_id)
        .filter(Post.status == 2)
        .group_by(post_categories.c.category_id)
        .all()
    )
    return {category_id: count for category_id, count in rows}


def _category_out(category: Category, counts: dict[int, int]) -> CategoryOut:
    """组装分类输出(含文章数)"""
    return CategoryOut(
        id=category.id,
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        description=category.description,
        color=category.color,
        sort_order=category.sort_order,
        post_count=counts.get(category.id, 0),
    )


def _ensure_unique(db: Session, *, name: str, slug: str, exclude_id: int | None = None) -> None:
    """校验分类名称与别名没有被别的记录占用

    新增与编辑都要校验: 库里的 name 没有唯一约束, 漏掉一次就会出现两个同名分类; 而
    slug 有唯一索引, 不先拦下来会以数据库的 IntegrityError 收场(500 + 报错看不懂)

    @param db 数据库会话
    @param name 分类名称
    @param slug 分类别名
    @param exclude_id 编辑时传当前分类 id, 把"自己"排除掉(只改大小写是允许的)
    @throws HTTPException 名称或别名已被占用(400)
    """
    name_query = db.query(Category).filter(Category.name == name)
    slug_query = db.query(Category).filter(Category.slug == slug)
    if exclude_id is not None:
        name_query = name_query.filter(Category.id != exclude_id)
        slug_query = slug_query.filter(Category.id != exclude_id)
    if name_query.first():
        raise HTTPException(status_code=400, detail="分类名称已存在")
    if slug_query.first():
        raise HTTPException(status_code=400, detail="分类别名已存在")


@router.get("", response_model=dict)
def list_categories(db: Session = Depends(get_db)):
    """分类列表(公开)"""
    categories = db.query(Category).order_by(Category.sort_order, Category.id).all()
    counts = _post_counts(db)
    return ok([_category_out(c, counts) for c in categories])


@router.post("", response_model=dict)
def create_category(
    data: CategoryIn,
    request: Request,
    _: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """新增分类"""
    _ensure_unique(db, name=data.name, slug=data.slug)
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=_,
        module="category",
        action="create",
        target_type="category",
        target_id=category.id,
        detail={"name": category.name},
    )
    return ok(_category_out(category, _post_counts(db)), "创建成功")


@router.put("/{category_id}", response_model=dict)
def update_category(
    category_id: int,
    data: CategoryIn,
    request: Request,
    _: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """编辑分类"""
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    _ensure_unique(db, name=data.name, slug=data.slug, exclude_id=category_id)
    for field, value in data.model_dump().items():
        setattr(category, field, value)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=_,
        module="category",
        action="update",
        target_type="category",
        target_id=category_id,
    )
    return ok(_category_out(category, _post_counts(db)), "保存成功")


@router.delete("/{category_id}", response_model=dict)
def delete_category(
    category_id: int,
    request: Request,
    _: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除分类"""
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(category)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=_,
        module="category",
        action="delete",
        target_type="category",
        target_id=category_id,
    )
    return ok(message="删除成功")
