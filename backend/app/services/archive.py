"""导入导出通用工具: frontmatter 解析, zip 打包与正文图片改写

文章, 日记与互联网纪事的导入导出共用这里的实现, 避免多处逻辑漂移
"""

import io
import json
import mimetypes
import re
import uuid
import zipfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, settings
from app.models.media import Media

# 正文中被引用到的上传图片 URL
_IMAGE_URL_RE = re.compile(
    r"/assets/[^\s)\"']+\.(?:png|jpe?g|gif|webp|svg|bmp|avif)", re.IGNORECASE
)

# 允许随压缩包一并导入的图片后缀
IMPORT_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif"}


def split_import_archive(
    name: str, raw: bytes
) -> tuple[list[tuple[str, str]], list[tuple[str, bytes]], str | None]:
    """拆分导入文件, 返回 (md 文件列表, 压缩包内全部条目, 错误信息)"""
    if name.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                entries = [
                    (info.filename, zf.read(info)) for info in zf.infolist() if not info.is_dir()
                ]
        except zipfile.BadZipFile:
            return [], [], f"{name}: 不是有效的 zip 压缩包"
        md_files = [
            (fname, data.decode("utf-8", errors="replace"))
            for fname, data in entries
            if fname.lower().endswith(".md")
        ]
        return md_files, entries, None
    if name.lower().endswith(".md"):
        return [(name, raw.decode("utf-8", errors="replace"))], [], None
    return [], [], f"{name}: 仅支持 .md 或 .zip 文件"


# 查重时把图片地址归一为文件名(相对路径与导入后的 /assets 地址视为同一张图)
_MD_IMAGE_RE = re.compile(r"\]\(([^)\s]+)\)")
_HTML_IMAGE_RE = re.compile(r'(<img[^>]*\bsrc=")([^"]+)(")')


def normalize_content(text: str) -> str:
    """归一化正文用于查重: 忽略空白差异, 图片地址只保留文件名"""
    body = _MD_IMAGE_RE.sub(lambda m: "](" + m.group(1).rsplit("/", 1)[-1] + ")", text or "")
    body = _HTML_IMAGE_RE.sub(
        lambda m: m.group(1) + m.group(2).rsplit("/", 1)[-1] + m.group(3), body
    )
    return re.sub(r"\s+", "", body)


def title_key(title: str) -> str:
    """标题查重键(忽略大小写与首尾空白)"""
    return (title or "").strip().lower()


def normalize_rel(path: str) -> str:
    """归一化相对路径: 统一斜杠, 去掉 ./ 与开头斜杠"""
    return path.replace("\\", "/").lstrip("./").strip()


def collect_uploaded_images(text: str) -> list[str]:
    """提取文本中 /assets/... 图片 URL"""
    urls: list[str] = []
    for match in _IMAGE_URL_RE.finditer(text or ""):
        url = match.group(0)
        if url not in urls:
            urls.append(url)
    return urls


def image_url_to_path(url: str) -> Path | None:
    """将 /assets/... URL 映射为服务器上的图片文件路径"""
    assets_root = (PROJECT_ROOT / "assets").resolve()
    candidate = (PROJECT_ROOT / url.lstrip("/")).resolve()
    if candidate.is_file() and assets_root in candidate.parents:
        return candidate
    return None


def pack_images(
    zf: zipfile.ZipFile,
    body: str,
    text_for_images: str,
    folder: str,
) -> str:
    """把正文引用的上传图片扁平写入压缩包, 并把 URL 改写为包内相对路径"""
    used_names: set[str] = set()
    for url in collect_uploaded_images(text_for_images):
        path = image_url_to_path(url)
        if path is None:
            continue
        name = path.name
        candidate = name
        index = 2
        while candidate.lower() in used_names:
            candidate = f"{path.stem}-{index}{path.suffix}"
            index += 1
        used_names.add(candidate.lower())
        zpath = f"{folder}/{candidate}"
        if zpath not in zf.namelist():
            # writestr 会保留 zip 标准要求的 / 分隔符; Windows 下 zf.write 会把
            # arcname 当成文件系统路径, 可能写入反斜杠并在重新读取时损坏名称
            zf.writestr(zpath, path.read_bytes())
        body = body.replace(url, zpath)
    return body


def save_import_images(
    entries: list[tuple[str, bytes]],
    date_dir: str,
    *,
    db: Session,
    uploader_id: int | None,
    module: str,
) -> dict[str, str]:
    """保存导入图片, 登记媒体库记录, 返回相对路径 -> URL 映射"""
    image_map: dict[str, str] = {}
    uploads_root = (Path(settings.upload_dir) / "import" / date_dir).resolve()
    for name, data in entries:
        suffix = Path(name).suffix.lower()
        if suffix not in IMPORT_IMAGE_EXTS:
            continue
        norm = normalize_rel(name)
        original_name = Path(name).name[:255] or f"image{suffix}"
        stored_name = f"{uuid.uuid4().hex}{suffix}"
        dest = (uploads_root / stored_name).resolve()
        uploads_root.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        url = f"/assets/uploads/import/{date_dir}/{stored_name}"
        mime_type = mimetypes.guess_type(original_name)[0] or f"image/{suffix.lstrip('.')}"
        db.add(
            Media(
                uploader_id=uploader_id,
                original_name=original_name,
                filename=stored_name,
                path=str(dest).replace("\\", "/"),
                url=url,
                mime_type=mime_type,
                size=len(data),
                type="image",
                related_type=module[:20],
            )
        )
        image_map.setdefault(norm, url)
        image_map.setdefault(original_name, url)
    return image_map


def lookup_image(image_map: dict[str, str], path: str | None) -> str | None:
    """按完整相对路径或文件名查找已导入图片的 URL"""
    if not path:
        return None
    norm = normalize_rel(path)
    return image_map.get(norm) or image_map.get(norm.rsplit("/", 1)[-1])


def rewrite_import_images(text: str, image_map: dict[str, str]) -> str:
    """把导入文本中的相对图片路径改写为服务器 URL"""
    if not image_map or not text:
        return text

    def repl_md(match: re.Match) -> str:
        target = lookup_image(image_map, match.group(2))
        return f"![{match.group(1)}]({target})" if target else match.group(0)

    def repl_html(match: re.Match) -> str:
        target = lookup_image(image_map, match.group(2))
        return f"{match.group(1)}{target}{match.group(3)}" if target else match.group(0)

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl_md, text)
    text = re.sub(r'(<img[^>]*\bsrc=")([^"]+)(")', repl_html, text)
    return text


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 Markdown 头部的 YAML frontmatter, 返回 (元信息, 正文)"""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    block = content[3:end]
    body = content[end + 4 :].lstrip("\r\n")
    meta: dict = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            try:
                value = json.loads(value)
            except Exception:
                pass
        elif value.startswith("[") and value.endswith("]"):
            try:
                value = json.loads(value)
            except Exception:
                pass
        meta[key] = value
    return meta, body


def frontmatter_lines(pairs: list[tuple[str, object]]) -> list[str]:
    """生成 YAML frontmatter 行(字符串加引号保证可被 JSON 解析还原)"""
    lines = ["---"]
    for key, value in pairs:
        if isinstance(value, (str, list)):
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        elif value is not None:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return lines


def unique_slug(db: Session, model, slug: str) -> str:
    """保证 slug 唯一(重名时追加 -1, -2 ...)"""
    base = slug
    index = 1
    while db.query(model).filter(model.slug == slug).first():
        slug = f"{base}-{index}"
        index += 1
    return slug
