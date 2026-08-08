"""媒体接口: 上传/列表/删除。"""
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.media import Media
from app.models.user import User
from app.schemas.common import Page
from app.schemas.media import MediaOut
from app.services.log import write_operation_log
from app.services.upload import save_upload

router = APIRouter(prefix="/media", tags=["媒体"])


@router.post("/upload", response_model=dict)
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    related_type: str | None = Form(None),
    related_id: int | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传文件到 assets/ 目录(登录用户可用, 供文章/评论插入)。"""
    if not (Perm.MEDIA_MANAGE in user.permission_codes or Perm.POST_CREATE in user.permission_codes):
        raise HTTPException(status_code=403, detail="无上传权限")
    info = save_upload(file)
    media = Media(uploader_id=user.id, related_type=related_type, related_id=related_id, **info)
    db.add(media)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="media", action="upload",
        target_type="media", target_id=media.id, detail={"filename": media.original_name},
    )
    return ok(MediaOut.model_validate(media), "上传成功")


@router.get("", response_model=dict)
def list_media(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    media_type: str | None = Query(None, alias="type", description="image/video/file"),
    _: User = Depends(require_permission(Perm.MEDIA_MANAGE)),
    db: Session = Depends(get_db),
):
    """媒体列表(管理端)。"""
    query = db.query(Media)
    if media_type:
        query = query.filter(Media.type == media_type)
    total = query.count()
    items = (
        query.order_by(Media.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(Page[MediaOut](
        items=[MediaOut.model_validate(m) for m in items],
        total=total, page=page, page_size=page_size,
    ))


@router.delete("/{media_id}", response_model=dict)
def delete_media(
    media_id: int,
    request: Request,
    admin: User = Depends(require_permission(Perm.MEDIA_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除媒体(同时删除磁盘文件)。"""
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="媒体不存在")

    # 安全删除: 解析目标路径并确认位于上传目录内
    upload_root = Path(settings.upload_dir).resolve()
    target = (Path.cwd() / media.path).resolve()
    if str(target).startswith(str(upload_root)):
        target.unlink(missing_ok=True)

    db.delete(media)
    db.commit()
    write_operation_log(
        db, request=request, user=admin, module="media", action="delete",
        target_type="media", target_id=media_id, detail={"filename": media.original_name},
    )
    return ok(message="删除成功")
