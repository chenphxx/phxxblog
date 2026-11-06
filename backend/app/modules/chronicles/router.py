"""互联网纪事接口"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.pagination import paginate
from app.core.permissions import Perm
from app.core.response import ok
from app.models.chronicle import ChronicleEntry
from app.models.user import User
from app.schemas.chronicle import ChronicleDetail, ChronicleIn, ChronicleListItem
from app.services.log import write_operation_log
from app.services.markdown import render_markdown

router = APIRouter(prefix="/chronicles", tags=["互联网纪事"])


def _apply_payload(entry: ChronicleEntry, data: ChronicleIn) -> None:
    """把表单字段写入实体, 并同步渲染 Markdown"""
    entry.title = data.title
    entry.summary = data.summary
    entry.cover_image = data.cover_image or None
    entry.content_md = data.content_md
    entry.content_html = render_markdown(data.content_md)


@router.get("", response_model=dict)
def list_chronicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    keyword: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    """纪事卡片列表(按创建时间倒序)"""
    query = db.query(ChronicleEntry)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(ChronicleEntry.title.like(pattern), ChronicleEntry.summary.like(pattern))
        )
    query = query.order_by(ChronicleEntry.created_at.desc(), ChronicleEntry.id.desc())
    return ok(paginate(query, page, page_size, ChronicleListItem))


@router.get("/{chronicle_id}", response_model=dict)
def get_chronicle(chronicle_id: int, db: Session = Depends(get_db)):
    """纪事详情"""
    entry = db.get(ChronicleEntry, chronicle_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="纪事不存在")
    return ok(ChronicleDetail.model_validate(entry))


@router.post("", response_model=dict)
def create_chronicle(
    data: ChronicleIn,
    request: Request,
    user: User = Depends(require_permission(Perm.CHRONICLE_MANAGE)),
    db: Session = Depends(get_db),
):
    """新增纪事"""
    entry = ChronicleEntry(author_id=user.id)
    _apply_payload(entry, data)
    db.add(entry)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=user,
        module="chronicles",
        action="create",
        target_type="chronicle",
        target_id=entry.id,
    )
    return ok(ChronicleDetail.model_validate(entry), "纪事已保存")


@router.put("/{chronicle_id}", response_model=dict)
def update_chronicle(
    chronicle_id: int,
    data: ChronicleIn,
    request: Request,
    user: User = Depends(require_permission(Perm.CHRONICLE_MANAGE)),
    db: Session = Depends(get_db),
):
    """编辑纪事"""
    entry = db.get(ChronicleEntry, chronicle_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="纪事不存在")
    _apply_payload(entry, data)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=user,
        module="chronicles",
        action="update",
        target_type="chronicle",
        target_id=chronicle_id,
    )
    return ok(ChronicleDetail.model_validate(entry), "保存成功")


@router.delete("/{chronicle_id}", response_model=dict)
def delete_chronicle(
    chronicle_id: int,
    request: Request,
    user: User = Depends(require_permission(Perm.CHRONICLE_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除纪事"""
    entry = db.get(ChronicleEntry, chronicle_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="纪事不存在")
    db.delete(entry)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=user,
        module="chronicles",
        action="delete",
        target_type="chronicle",
        target_id=chronicle_id,
    )
    return ok(message="删除成功")
