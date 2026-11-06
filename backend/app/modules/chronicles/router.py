"""互联网纪事接口"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user, require_permission
from app.core.pagination import paginate
from app.core.permissions import Perm
from app.core.response import ok
from app.models.chronicle import ChronicleEntry
from app.models.user import User
from app.schemas.chronicle import (
    ChronicleDetail,
    ChronicleIn,
    ChronicleListItem,
    ChronicleStatusIn,
)
from app.services.log import write_operation_log
from app.services.markdown import render_markdown

router = APIRouter(prefix="/chronicles", tags=["互联网纪事"])

STATUS_DRAFT = 0
STATUS_REVIEW = 1
STATUS_PUBLISHED = 2
STATUS_PRIVATE = 3
STATUS_TRASH = 4


def _apply_payload(entry: ChronicleEntry, data: ChronicleIn) -> None:
    """把表单字段写入实体, 并同步渲染 Markdown"""
    entry.title = data.title
    entry.summary = data.summary
    entry.cover_image = data.cover_image or None
    entry.status = data.status
    entry.content_md = data.content_md
    entry.content_html = render_markdown(data.content_md)
    if data.status == STATUS_PUBLISHED and entry.published_at is None:
        entry.published_at = datetime.now()


def _set_status(entry: ChronicleEntry, status: int) -> None:
    """更新状态, 首次发布时补写发布时间"""
    entry.status = status
    if status == STATUS_PUBLISHED and entry.published_at is None:
        entry.published_at = datetime.now()


@router.get("", response_model=dict)
def list_chronicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    keyword: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    """前台纪事卡片列表(仅已发布)"""
    query = db.query(ChronicleEntry).filter(ChronicleEntry.status == STATUS_PUBLISHED)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(ChronicleEntry.title.like(pattern), ChronicleEntry.summary.like(pattern))
        )
    query = query.order_by(ChronicleEntry.published_at.desc(), ChronicleEntry.id.desc())
    return ok(paginate(query, page, page_size, ChronicleListItem))


@router.get("/admin", response_model=dict)
def admin_list_chronicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: int | None = Query(None, ge=0, le=4),
    keyword: str | None = Query(None, max_length=100),
    _user: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """后台纪事列表(包含全部状态)"""
    query = db.query(ChronicleEntry)
    if status is not None:
        query = query.filter(ChronicleEntry.status == status)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(ChronicleEntry.title.like(pattern), ChronicleEntry.summary.like(pattern))
        )
    query = query.order_by(ChronicleEntry.updated_at.desc(), ChronicleEntry.id.desc())
    return ok(paginate(query, page, page_size, ChronicleListItem))


@router.get("/{chronicle_id}", response_model=dict)
def get_chronicle(
    chronicle_id: int,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """纪事详情"""
    entry = db.get(ChronicleEntry, chronicle_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="纪事不存在")
    if entry.status != STATUS_PUBLISHED:
        if user is None or Perm.POST_MANAGE not in user.permission_codes:
            raise HTTPException(status_code=404, detail="纪事不存在")
    return ok(ChronicleDetail.model_validate(entry))


@router.post("", response_model=dict)
def create_chronicle(
    data: ChronicleIn,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_MANAGE)),
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
    user: User = Depends(require_permission(Perm.POST_MANAGE)),
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


@router.post("/{chronicle_id}/status", response_model=dict)
def change_chronicle_status(
    chronicle_id: int,
    data: ChronicleStatusIn,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """切换纪事状态"""
    entry = db.get(ChronicleEntry, chronicle_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="纪事不存在")
    _set_status(entry, data.status)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=user,
        module="chronicles",
        action=f"status:{data.status}",
        target_type="chronicle",
        target_id=chronicle_id,
    )
    return ok(ChronicleDetail.model_validate(entry), "状态已更新")


@router.post("/{chronicle_id}/restore", response_model=dict)
def restore_chronicle(
    chronicle_id: int,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """从回收站恢复为草稿"""
    entry = db.get(ChronicleEntry, chronicle_id)
    if entry is None or entry.status != STATUS_TRASH:
        raise HTTPException(status_code=404, detail="纪事不存在")
    _set_status(entry, STATUS_DRAFT)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=user,
        module="chronicles",
        action="restore",
        target_type="chronicle",
        target_id=chronicle_id,
    )
    return ok(ChronicleDetail.model_validate(entry), "已恢复为草稿")


@router.delete("/{chronicle_id}", response_model=dict)
def trash_chronicle(
    chronicle_id: int,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """将纪事移入回收站"""
    entry = db.get(ChronicleEntry, chronicle_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="纪事不存在")
    _set_status(entry, STATUS_TRASH)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=user,
        module="chronicles",
        action="trash",
        target_type="chronicle",
        target_id=chronicle_id,
    )
    return ok(message="已移入回收站")


@router.delete("/{chronicle_id}/force", response_model=dict)
def force_delete_chronicle(
    chronicle_id: int,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """彻底删除纪事"""
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
        action="force_delete",
        target_type="chronicle",
        target_id=chronicle_id,
    )
    return ok(message="已彻底删除")
