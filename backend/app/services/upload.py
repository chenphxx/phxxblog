"""文件上传服务: 校验、落盘到 assets/ 并生成记录。"""
import uuid
from datetime import date
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv"}


def save_upload(file: UploadFile) -> dict:
    """保存上传文件, 返回 {original_name, filename, path, url, mime_type, size, type}。"""
    original_name = file.filename or "unnamed"
    suffix = Path(original_name).suffix.lower()

    if suffix in IMAGE_EXTS:
        file_type = "image"
    elif suffix in VIDEO_EXTS:
        file_type = "video"
    else:
        file_type = "file"

    # 按 年/月 分目录存储, 文件名使用 UUID 避免冲突
    sub_dir = Path(settings.upload_dir) / str(date.today().year) / f"{date.today().month:02d}"
    sub_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    target = sub_dir / filename

    size = 0
    with target.open("wb") as f:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_size:
                f.close()
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="文件超过大小限制")
            f.write(chunk)

    path = str(target).replace("\\", "/")
    url = f"/assets/uploads/{date.today().year}/{date.today().month:02d}/{filename}"
    return {
        "original_name": original_name,
        "filename": filename,
        "path": path,
        "url": url,
        "mime_type": file.content_type,
        "size": size,
        "type": file_type,
    }
