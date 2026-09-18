"""文件上传服务: 校验、落盘到 assets/ 并生成记录。

安全约定(重要, 改动前请先读):
    上传目录是**同源静态托管**的(见 main.py 的 /assets 挂载), 也就是说
    上传一个能被浏览器当脚本执行的文件, 就等于拿到了本域的 XSS 能力。
    因此这里采用**扩展名白名单**: 不在白名单里的一律拒绝, 而不是"未知类型放行"。

    特别地, 以下类型被刻意排除:
      - .svg  矢量图可内嵌 <script>, 浏览器会当文档渲染并执行
      - .html/.htm/.xml  直接就是可执行文档
      - .js/.mjs/.css    同源脚本/样式注入
    若确实需要上传 SVG, 请改为部署层面单独挂一个子域, 或让反代对上传目录
    强制加 `Content-Disposition: attachment` + `X-Content-Type-Options: nosniff`。
"""

import uuid
from datetime import date
from pathlib import Path
from typing import Final

from fastapi import HTTPException, UploadFile

from app.core.config import PROJECT_ROOT, settings

# ---------------------------------------------------------------- 类型白名单

IMAGE_EXTS: Final = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico"}
VIDEO_EXTS: Final = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv"}
AUDIO_EXTS: Final = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
# 文档类只作为附件下载(部署层面应对上传目录关闭这些类型的 inline 渲染)
DOCUMENT_EXTS: Final = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".zip",
    ".7z",
    ".rar",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}

ALLOWED_EXTS: Final = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS | DOCUMENT_EXTS

# 需要校验文件头的类型(防止把 .html 改名成 .png 传上来)
MAGIC_BYTES: Final[dict[str, tuple[bytes, ...]]] = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".webp": (b"RIFF",),  # 完整校验还需 bytes[8:12] == b"WEBP"
    ".bmp": (b"BM",),
    ".ico": (b"\x00\x00\x01\x00",),
}


def _detect_type(suffix: str) -> str:
    """扩展名 -> 媒体类型。"""
    if suffix in IMAGE_EXTS:
        return "image"
    if suffix in VIDEO_EXTS:
        return "video"
    if suffix in AUDIO_EXTS:
        return "audio"
    return "file"


def upload_root() -> Path:
    """上传根目录(绝对路径)。"""
    return Path(settings.upload_dir).resolve()


def resolve_upload_file(stored_path: str) -> Path | None:
    """把数据库里记录的媒体路径解析成受信任的绝对路径; 不在上传目录内则返回 None。

    修复了两个问题:
      1. 以前 media 删除用 `str(target).startswith(str(upload_root))` 判断包含关系 ——
         `.../uploads_evil/x` 也会通过前缀校验。这里改成按路径段比较(`in parents`)。
      2. 以前用 `Path.cwd() / media.path` 解析相对路径, 依赖"从哪个目录启动进程" ——
         同样一份数据, 从仓库根目录启动和从 backend/ 启动会解析到不同位置。
         现在以 PROJECT_ROOT 为基准, 且优先信任绝对路径(上传时写的就是绝对路径)。
    """
    if not stored_path:
        return None
    raw = Path(stored_path)
    candidate = raw.resolve() if raw.is_absolute() else (PROJECT_ROOT / raw).resolve()
    root = upload_root()
    if candidate != root and root not in candidate.parents:
        return None
    return candidate


def _check_magic(header: bytes, suffix: str) -> None:
    """校验声称为图片的文件头是否匹配。"""
    expected = MAGIC_BYTES.get(suffix)
    if not expected:
        return
    if not header.startswith(expected):
        raise HTTPException(status_code=400, detail=f"文件内容与扩展名 {suffix} 不匹配")
    if suffix == ".webp" and header[8:12] != b"WEBP":
        raise HTTPException(status_code=400, detail="文件内容与扩展名 .webp 不匹配")


def save_upload(file: UploadFile) -> dict:
    """保存上传文件, 返回 {original_name, filename, path, url, mime_type, size, type}。"""
    original_name = file.filename or "unnamed"
    suffix = Path(original_name).suffix.lower()

    if suffix not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {suffix or '(无扩展名)'}; 允许: {', '.join(sorted(ALLOWED_EXTS))}",
        )

    file_type = _detect_type(suffix)

    # 按 年/月 分目录存储, 文件名使用 UUID 避免冲突
    sub_dir = Path(settings.upload_dir) / str(date.today().year) / f"{date.today().month:02d}"
    sub_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    target = sub_dir / filename

    size = 0
    checked = False
    with target.open("wb") as f:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_size:
                f.close()
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="文件超过大小限制")
            if not checked:
                # 首块就要做文件头校验: 不合格立刻删掉已经写下的字节
                try:
                    _check_magic(chunk[:16], suffix)
                except HTTPException:
                    f.close()
                    target.unlink(missing_ok=True)
                    raise
                checked = True
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
