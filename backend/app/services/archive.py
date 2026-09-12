"""导入导出通用工具: frontmatter 解析、zip 打包与正文图片改写。

文章与日记的导入导出共用这里的实现, 避免两处逻辑漂移。
"""
import io
import json
import re
import zipfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, settings

# 正文中被引用到的上传图片 URL
_IMAGE_URL_RE = re.compile(
    r"/assets/[^\s)\"']+\.(?:png|jpe?g|gif|webp|svg|bmp|avif)", re.IGNORECASE
)

# 允许随压缩包一并导入的图片后缀
IMPORT_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif"}


def split_import_archive(
    name: str, raw: bytes
) -> tuple[list[tuple[str, str]], list[tuple[str, bytes]], str | None]:
    """拆分导入文件, 返回 (md 文件列表, 压缩包内全部条目, 错误信息)。"""
    if name.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                entries = [
                    (info.filename, zf.read(info))
                    for info in zf.infolist()
                    if not info.is_dir()
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
    """归一化正文用于查重: 忽略空白差异, 图片地址只保留文件名。"""
    body = _MD_IMAGE_RE.sub(lambda m: "](" + m.group(1).rsplit("/", 1)[-1] + ")", text or "")
    body = _HTML_IMAGE_RE.sub(
        lambda m: m.group(1) + m.group(2).rsplit("/", 1)[-1] + m.group(3), body
    )
    return re.sub(r"\s+", "", body)


def title_key(title: str) -> str:
    """标题查重键(忽略大小写与首尾空白)。"""
    return (title or "").strip().lower()


def normalize_rel(path: str) -> str:
    """归一化相对路径: 统一斜杠、去掉 ./ 与开头斜杠。"""
    return path.replace("\\", "/").lstrip("./").strip()


def collect_uploaded_images(text: str) -> list[str]:
    """提取文本中 /assets/... 图片 URL。"""
    urls: list[str] = []
    for match in _IMAGE_URL_RE.finditer(text or ""):
        url = match.group(0)
        if url not in urls:
            urls.append(url)
    return urls


def image_url_to_path(url: str) -> Path | None:
    """将 /assets/... URL 映射为服务器上的图片文件路径。"""
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
    """把正文引用的上传图片写进压缩包的 folder/ 下, 并把 URL 改写为包内相对路径。"""
    for url in collect_uploaded_images(text_for_images):
        path = image_url_to_path(url)
        if path is None:
            continue
        rel = path.relative_to(PROJECT_ROOT / "assets")
        zpath = f"{folder}/{rel.as_posix()}"
        if zpath not in zf.namelist():
            zf.write(str(path), zpath)
        body = body.replace(url, zpath)
    return body


def save_import_images(entries: list[tuple[str, bytes]], date_dir: str) -> dict[str, str]:
    """把压缩包中的图片保存到 uploads/import/<date_dir>/, 返回 相对路径 -> URL 映射。"""
    image_map: dict[str, str] = {}
    uploads_root = (Path(settings.upload_dir) / "import" / date_dir).resolve()
    for name, data in entries:
        if Path(name).suffix.lower() not in IMPORT_IMAGE_EXTS:
            continue
        norm = normalize_rel(name)
        parts = [part for part in norm.split("/") if part not in ("", ".", "..")]
        if not parts:
            continue
        safe_rel = "/".join(parts)
        dest = (uploads_root / safe_rel).resolve()
        if dest != uploads_root and uploads_root not in dest.parents:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        url = f"/assets/uploads/import/{date_dir}/{safe_rel}"
        image_map.setdefault(norm, url)
        image_map.setdefault(parts[-1], url)
    return image_map


def lookup_image(image_map: dict[str, str], path: str | None) -> str | None:
    """按完整相对路径或文件名查找已导入图片的 URL。"""
    if not path:
        return None
    norm = normalize_rel(path)
    return image_map.get(norm) or image_map.get(norm.rsplit("/", 1)[-1])


def rewrite_import_images(text: str, image_map: dict[str, str]) -> str:
    """把导入文本中的相对图片路径改写为服务器 URL。"""
    if not image_map or not text:
        return text

    def repl_md(match: re.Match) -> str:
        target = lookup_image(image_map, match.group(2))
        return f"![{match.group(1)}]({target})" if target else match.group(0)

    def repl_html(match: re.Match) -> str:
        target = lookup_image(image_map, match.group(2))
        return f'{match.group(1)}{target}{match.group(3)}' if target else match.group(0)

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl_md, text)
    text = re.sub(r'(<img[^>]*\bsrc=")([^"]+)(")', repl_html, text)
    return text


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 Markdown 头部的 YAML frontmatter, 返回 (元信息, 正文)。"""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    block = content[3:end]
    body = content[end + 4:].lstrip("\r\n")
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
    """生成 YAML frontmatter 行(字符串加引号保证可被 JSON 解析还原)。"""
    lines = ["---"]
    for key, value in pairs:
        if isinstance(value, (str, list)):
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        elif value is not None:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return lines


def unique_slug(db: Session, model, slug: str) -> str:
    """保证 slug 唯一(重名时追加 -1, -2 ...)。"""
    base = slug
    index = 1
    while db.query(model).filter(model.slug == slug).first():
        slug = f"{base}-{index}"
        index += 1
    return slug
