"""日记接口(仅管理员)。"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.diary import DiaryEntry
from app.models.user import User
from app.schemas.diary import DiaryIn, DiaryOut
from app.services.log import write_operation_log
from app.services.markdown import render_markdown

router = APIRouter(prefix="/diaries", tags=["日记"])


def _require_admin(user: User) -> None:
    """仅管理员可访问日记功能。"""
    if "admin" not in user.role_codes:
        raise HTTPException(status_code=403, detail="仅管理员可访问")


@router.get("", response_model=dict)
def list_diaries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """日记列表(按日期倒序)。"""
    _require_admin(user)
    query = db.query(DiaryEntry)
    total = query.count()
    items = (
        query.order_by(DiaryEntry.entry_date.desc(), DiaryEntry.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok({
        "items": [DiaryOut.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("", response_model=dict)
def create_diary(
    data: DiaryIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新增日记。"""
    _require_admin(user)
    entry = DiaryEntry(
        user_id=user.id,
        content_md=data.content_md,
        content_html=render_markdown(data.content_md),
        entry_date=data.entry_date or date.today(),
    )
    db.add(entry)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="diary", action="create",
        target_type="diary", target_id=entry.id,
    )
    return ok(DiaryOut.model_validate(entry), "日记已保存")


@router.put("/{diary_id}", response_model=dict)
def update_diary(
    diary_id: int,
    data: DiaryIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑日记。"""
    _require_admin(user)
    entry = db.get(DiaryEntry, diary_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="日记不存在")
    entry.content_md = data.content_md
    entry.content_html = render_markdown(data.content_md)
    if data.entry_date:
        entry.entry_date = data.entry_date
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="diary", action="update",
        target_type="diary", target_id=diary_id,
    )
    return ok(DiaryOut.model_validate(entry), "保存成功")


@router.delete("/{diary_id}", response_model=dict)
def delete_diary(
    diary_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除日记。"""
    _require_admin(user)
    entry = db.get(DiaryEntry, diary_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="日记不存在")
    db.delete(entry)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="diary", action="delete",
        target_type="diary", target_id=diary_id,
    )
    return ok(message="删除成功")
