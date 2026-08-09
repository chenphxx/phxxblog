"""文章接口: 前台浏览、后台管理、发布流程、点赞、归档。"""
import io
import json
import re
import uuid
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, settings
from app.core.database import get_db
from app.core.deps import (
    get_client_ip,
    get_current_user,
    get_optional_user,
    require_permission,
)
from app.core.permissions import Perm
from app.core.response import ok
from app.models.analytics import DailyStat
from app.models.post import Category, Post, PostLike, Tag
from app.models.user import User
from app.schemas.common import Page
from app.schemas.post import (
    ArchiveGroup,
    CategoryOut,
    LikeResult,
    PostCreate,
    PostDetail,
    PostListItem,
    PostStatusIn,
    PostUpdate,
    TagOut,
)
from app.services.log import write_operation_log
from app.services.markdown import render_markdown
from app.services.geo import resolve_location
from app.services.stats import record_visit

router = APIRouter(prefix="/posts", tags=["文章"])


def _can_manage(user: User, post: Post) -> bool:
    """作者本人或拥有 post:manage 权限可管理该文章。"""
    return user.id == post.author_id or Perm.POST_MANAGE in user.permission_codes


def _auto_slug(data_slug: str, title: str) -> str:
    """生成文章 slug: 优先使用传入值, 否则生成唯一短标识。"""
    if data_slug:
        return data_slug
    return f"post-{uuid.uuid4().hex[:8]}"


def _apply_payload(
    db: Session,
    post: Post,
    data: PostCreate | PostUpdate,
    user: User,
    request: Request,
) -> None:
    """将请求字段应用到文章(含状态规则、标签、HTML 渲染)。"""
    target_status = data.status
    # 非管理员不能直接发布/置私密, 降级为审核中
    if target_status in (2, 3) and Perm.POST_PUBLISH not in user.permission_codes:
        target_status = 1
    if target_status == 4 and Perm.POST_MANAGE not in user.permission_codes:
        target_status = 1

    post.title = data.title
    post.slug = _auto_slug(data.slug, data.title)
    post.summary = data.summary
    post.content_md = data.content_md
    post.content_html = render_markdown(data.content_md)
    post.cover_image = data.cover_image
    post.category_id = data.category_id
    post.status = target_status
    post.ip = get_client_ip(request)
    post.location = resolve_location(post.ip)

    if target_status == 2 and post.published_at is None:
        post.published_at = datetime.now()

    # 标签
    if data.tag_ids:
        post.tags = db.query(Tag).filter(Tag.id.in_(data.tag_ids)).all()


@router.get("", response_model=dict)
def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: int | None = Query(None, description="分类ID"),
    tag: int | None = Query(None, description="标签ID"),
    year: int | None = Query(None, description="年份筛选"),
    month: int | None = Query(None, description="月份筛选"),
    start_date: str | None = Query(None, description="发布时间起始 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="发布时间结束 YYYY-MM-DD"),
    keyword: str | None = Query(None, description="关键词(标题/摘要)"),
    db: Session = Depends(get_db),
):
    """前台文章列表(仅已发布)。"""
    query = db.query(Post).filter(Post.status == 2)
    if category:
        query = query.filter(Post.category_id == category)
    if tag:
        query = query.join(Post.tags).filter(Tag.id == tag)
    if year:
        query = query.filter(func.year(Post.published_at) == year)
    if month:
        query = query.filter(func.month(Post.published_at) == month)
    if start_date:
        query = query.filter(Post.published_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(
            Post.published_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        )
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(Post.title.like(like), Post.summary.like(like)))

    total = query.count()
    items = (
        query.order_by(Post.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(Page[PostListItem](
        items=[PostListItem.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    ))


@router.get("/archive", response_model=dict)
def archive(db: Session = Depends(get_db)):
    """归档: 按 年-月 分组展示所有已发布文章。"""
    posts = (
        db.query(Post)
        .filter(Post.status == 2)
        .order_by(Post.published_at.desc())
        .all()
    )
    groups: dict[tuple[int, int], list[Post]] = {}
    for post in posts:
        published_at = post.published_at or post.created_at
        key = (published_at.year, published_at.month)
        groups.setdefault(key, []).append(post)
    result = [
        ArchiveGroup(
            year=key[0],
            month=key[1],
            count=len(items),
            posts=[PostListItem.model_validate(p) for p in items],
        )
        for key, items in sorted(groups.items(), reverse=True)
    ]
    return ok(result)


@router.get("/admin", response_model=dict)
def admin_list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: int | None = Query(None, description="0草稿 1审核中 2已发布 3私密 4回收站"),
    keyword: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """后台文章管理列表(管理员看全部, 作者只看自己)。"""
    query = db.query(Post)
    if Perm.POST_MANAGE not in user.permission_codes:
        query = query.filter(Post.author_id == user.id)
    if status is not None:
        query = query.filter(Post.status == status)
    if keyword:
        query = query.filter(Post.title.like(f"%{keyword}%"))
    total = query.count()
    items = (
        query.order_by(Post.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(Page[PostListItem](
        items=[PostListItem.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    ))


def _post_to_markdown(post: Post) -> str:
    """将文章序列化为带 YAML frontmatter 的 Markdown 文本。"""
    lines = ["---"]
    lines.append(f"title: {json.dumps(post.title, ensure_ascii=False)}")
    lines.append(f"slug: {json.dumps(post.slug, ensure_ascii=False)}")
    lines.append(f"status: {post.status}")
    if post.published_at:
        lines.append(f"date: {json.dumps(post.published_at.strftime('%Y-%m-%d %H:%M:%S'), ensure_ascii=False)}")
    if post.summary:
        lines.append(f"summary: {json.dumps(post.summary, ensure_ascii=False)}")
    if post.cover_image:
        lines.append(f"cover_image: {json.dumps(post.cover_image, ensure_ascii=False)}")
    if post.category:
        lines.append(f"category: {json.dumps(post.category.name, ensure_ascii=False)}")
    if post.tags:
        lines.append("tags: " + json.dumps([t.name for t in post.tags], ensure_ascii=False))
    lines.append("---")
    lines.append("")
    lines.append(post.content_md)
    return "\n".join(lines)


def _parse_frontmatter(content: str) -> tuple[dict, str]:
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


def _unique_slug(db: Session, model, slug: str) -> str:
    """保证 slug 唯一(重名时追加 -1, -2 ...)。"""
    base = slug
    index = 1
    while db.query(model).filter(model.slug == slug).first():
        slug = f"{base}-{index}"
        index += 1
    return slug


_IMAGE_URL_RE = re.compile(
    r"/assets/[^\s)\"']+\.(?:png|jpe?g|gif|webp|svg|bmp|avif)", re.IGNORECASE
)
_IMPORT_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif"}


def _collect_uploaded_images(text: str) -> list[str]:
    """提取文本中 /assets/... 图片 URL。"""
    urls: list[str] = []
    for match in _IMAGE_URL_RE.finditer(text or ""):
        url = match.group(0)
        if url not in urls:
            urls.append(url)
    return urls


def _image_url_to_path(url: str) -> Path | None:
    """将 /assets/... URL 映射为服务器上的图片文件路径。"""
    assets_root = (PROJECT_ROOT / "assets").resolve()
    candidate = (PROJECT_ROOT / url.lstrip("/")).resolve()
    if candidate.is_file() and assets_root in candidate.parents:
        return candidate
    return None


def _normalize_rel(path: str) -> str:
    """归一化相对路径: 统一斜杠、去掉 ./ 与开头斜杠。"""
    return path.replace("\\", "/").lstrip("./").strip()


def _rewrite_import_images(text: str, image_map: dict[str, str]) -> str:
    """把导入文本中的相对图片路径改写为服务器 URL。"""
    if not image_map or not text:
        return text

    def lookup(norm: str) -> str | None:
        target = image_map.get(norm)
        if target is None:
            target = image_map.get(norm.rsplit("/", 1)[-1])
        return target

    def repl_md(match: re.Match) -> str:
        alt, url = match.group(1), match.group(2)
        target = lookup(_normalize_rel(url))
        return f"![{alt}]({target})" if target else match.group(0)

    def repl_html(match: re.Match) -> str:
        url = match.group(2)
        target = lookup(_normalize_rel(url))
        return f'{match.group(1)}{target}{match.group(3)}' if target else match.group(0)

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl_md, text)
    text = re.sub(r'(<img[^>]*\bsrc=")([^"]+)(")', repl_html, text)
    return text


def _rewrite_cover_image(cover: str | None, image_map: dict[str, str]) -> str | None:
    """改写 frontmatter 中的封面图片路径。"""
    if not cover:
        return cover
    norm = _normalize_rel(cover)
    target = image_map.get(norm) or image_map.get(norm.rsplit("/", 1)[-1])
    return target or cover


def _save_import_images(entries: list[tuple[str, bytes]], date_dir: str) -> dict[str, str]:
    """把压缩包中的图片保存到 uploads/import/<date>/, 返回 相对路径 -> URL 映射。"""
    image_map: dict[str, str] = {}
    uploads_root = (Path(settings.upload_dir) / "import" / date_dir).resolve()
    for name, data in entries:
        if Path(name).suffix.lower() not in _IMPORT_IMAGE_EXTS:
            continue
        norm = _normalize_rel(name)
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


def _import_markdown(
    db: Session,
    user: User,
    filename: str,
    content: str,
    image_map: dict[str, str] | None = None,
) -> tuple[bool, str | None]:
    """解析并创建一篇文章(默认草稿)。返回 (是否导入, 错误信息)。"""
    meta, body = _parse_frontmatter(content)
    image_map = image_map or {}
    title = str(meta.get("title") or "").strip()
    if not title:
        for line in body.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
    if not title:
        stem = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        title = stem[:-3] if stem.lower().endswith(".md") else stem
    if not title:
        return False, f"{filename}: 无法识别标题"

    slug = str(meta.get("slug") or "").strip() or f"post-{uuid.uuid4().hex[:8]}"
    slug = _unique_slug(db, Post, slug)

    status = 0
    try:
        raw_status = int(str(meta.get("status") or "0"))
    except (TypeError, ValueError):
        raw_status = 0
    if raw_status == 2 and Perm.POST_PUBLISH in user.permission_codes:
        status = 2
    elif raw_status == 3 and Perm.POST_MANAGE in user.permission_codes:
        status = 3
    elif raw_status in (0, 1):
        status = raw_status

    category = None
    category_name = str(meta.get("category") or "").strip()
    if category_name:
        category = (
            db.query(Category)
            .filter(func.lower(Category.name) == category_name.lower())
            .first()
        )
        if category is None:
            category = Category(
                name=category_name[:50],
                slug=_unique_slug(db, Category, category_name[:80]),
            )
            db.add(category)
            db.flush()

    raw_tags = meta.get("tags") or []
    if isinstance(raw_tags, str):
        raw_tags = [t.strip() for t in raw_tags.strip("[]").split(",") if t.strip()]
    tags: list[Tag] = []
    for tag_name in raw_tags:
        tag_name = str(tag_name).strip()
        if not tag_name:
            continue
        tag = db.query(Tag).filter(func.lower(Tag.name) == tag_name.lower()).first()
        if tag is None:
            tag = Tag(
                name=tag_name[:50],
                slug=_unique_slug(db, Tag, tag_name[:80]),
            )
            db.add(tag)
            db.flush()
        tags.append(tag)

    summary = str(meta.get("summary") or "").strip() or None
    cover_image = str(meta.get("cover_image") or "").strip() or None
    body = _rewrite_import_images(body, image_map)
    cover_image = _rewrite_cover_image(cover_image, image_map)
    post = Post(
        author_id=user.id,
        title=title[:200],
        slug=slug,
        summary=summary[:500] if summary else None,
        content_md=body,
        cover_image=cover_image[:255] if cover_image else None,
        category_id=category.id if category else None,
        status=status,
    )
    if status == 2:
        date_str = str(meta.get("date") or "").strip()
        try:
            post.published_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            try:
                post.published_at = datetime.strptime(date_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                post.published_at = datetime.now()
    post.tags = tags
    db.add(post)
    db.flush()
    return True, None


@router.get("/export", response_model=None)
def export_posts(
    ids: str | None = Query(None, description="逗号分隔的文章ID, 不传则导出全部(作者本人/管理员)"),
    fmt: str = Query("markdown", pattern="^(markdown|html)$", description="导出格式: markdown / html"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导出文章压缩包(markdown/html, 图片一并打包; 仅作者本人/管理员可导)。"""
    query = db.query(Post)
    if Perm.POST_MANAGE not in user.permission_codes:
        query = query.filter(Post.author_id == user.id)
    if ids:
        id_list = [int(i) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Post.id.in_(id_list))
    posts = query.order_by(Post.created_at.desc()).all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for post in posts:
            slug = post.slug or str(post.id)
            if fmt == "html":
                content = post.content_html or render_markdown(post.content_md)
                body = (
                    "<!DOCTYPE html>\n<html lang='zh-CN'>\n<head>\n<meta charset='utf-8'>\n"
                    f"<title>{post.title}</title>\n</head>\n<body>\n{content}\n</body>\n</html>"
                )
                filename = f"{slug}.html"
                text_for_images = f"{content} {post.cover_image or ''}"
            else:
                body = _post_to_markdown(post)
                filename = f"{slug}.md"
                text_for_images = body
            for url in _collect_uploaded_images(text_for_images):
                path = _image_url_to_path(url)
                if path is None:
                    continue
                rel = path.relative_to(PROJECT_ROOT / "assets")
                zpath = f"images/{slug}/{rel.as_posix()}"
                if zpath not in zf.namelist():
                    zf.write(str(path), zpath)
                body = body.replace(url, zpath)
            zf.writestr(filename, body)
    buf.seek(0)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return Response(
        buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="phxxblog-posts-{stamp}.zip"'},
    )


@router.post("/import", response_model=dict)
def import_posts(
    request: Request,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导入文章: 支持 .md 文件或包含 .md 的 zip 压缩包。"""
    if Perm.POST_CREATE not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:create")
    imported = 0
    skipped = 0
    errors: list[str] = []
    for upload in files:
        name = upload.filename or "untitled"
        raw = upload.file.read()
        md_files: list[tuple[str, str]] = []
        image_map: dict[str, str] = {}
        if name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    entries = [
                        (info.filename, zf.read(info))
                        for info in zf.infolist()
                        if not info.is_dir()
                    ]
            except zipfile.BadZipFile:
                errors.append(f"{name}: 不是有效的 zip 压缩包")
                continue
            date_dir = datetime.now().strftime("%Y/%m")
            image_map = _save_import_images(entries, date_dir)
            for fname, data in entries:
                if not fname.lower().endswith(".md"):
                    continue
                md_files.append((fname, data.decode("utf-8", errors="replace")))
        elif name.lower().endswith(".md"):
            md_files.append((name, raw.decode("utf-8", errors="replace")))
        else:
            errors.append(f"{name}: 仅支持 .md 或 .zip 文件")
            continue
        for fname, content in md_files:
            ok_imported, err = _import_markdown(db, user, fname, content, image_map)
            if ok_imported:
                imported += 1
            elif err:
                errors.append(err)
            else:
                skipped += 1
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="import",
        detail={"imported": imported, "skipped": skipped, "errors": len(errors)},
    )
    return ok({"imported": imported, "skipped": skipped, "errors": errors[:20]}, "导入完成")


@router.get("/{post_id}", response_model=dict)
def get_post(
    post_id: int,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """文章详情(已发布公开, 非公开仅作者/管理员可见)。"""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if post.status != 2:
        if user is None or not _can_manage(user, post):
            raise HTTPException(status_code=404, detail="文章不存在")
    if post.status == 2:
        record_visit(db, request=request, post=post)
    return ok(PostDetail.model_validate(post))


@router.post("", response_model=dict)
def create_post(
    data: PostCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新增文章(默认草稿, 可提交审核)。"""
    if Perm.POST_CREATE not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:create")
    post = Post(author_id=user.id)
    _apply_payload(db, post, data, user, request)
    db.add(post)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="create",
        target_type="post", target_id=post.id, detail={"title": post.title},
    )
    return ok(PostDetail.model_validate(post), "已保存")


@router.put("/{post_id}", response_model=dict)
def update_post(
    post_id: int,
    data: PostUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑文章。"""
    if Perm.POST_EDIT not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:edit")
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not _can_manage(user, post):
        raise HTTPException(status_code=403, detail="只能编辑自己的文章")
    _apply_payload(db, post, data, user, request)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="update",
        target_type="post", target_id=post.id, detail={"title": post.title},
    )
    return ok(PostDetail.model_validate(post), "保存成功")


@router.delete("/{post_id}", response_model=dict)
def trash_post(
    post_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除文章(移入回收站)。"""
    if Perm.POST_DELETE not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:delete")
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not _can_manage(user, post):
        raise HTTPException(status_code=403, detail="只能删除自己的文章")
    post.status = 4
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="trash",
        target_type="post", target_id=post_id,
    )
    return ok(message="已移入回收站")


@router.delete("/{post_id}/force", response_model=dict)
def force_delete_post(
    post_id: int,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_MANAGE)),
    db: Session = Depends(get_db),
):
    """彻底删除文章。"""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    title = post.title
    db.delete(post)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="force_delete",
        target_type="post", target_id=post_id, detail={"title": title},
    )
    return ok(message="已彻底删除")


@router.post("/{post_id}/restore", response_model=dict)
def restore_post(
    post_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从回收站恢复(恢复为草稿)。"""
    post = db.get(Post, post_id)
    if post is None or post.status != 4:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not _can_manage(user, post):
        raise HTTPException(status_code=403, detail="无权限")
    post.status = 0
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="restore",
        target_type="post", target_id=post_id,
    )
    return ok(message="已恢复为草稿")


@router.post("/{post_id}/publish", response_model=dict)
def change_post_status(
    post_id: int,
    data: PostStatusIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """状态流转: 0草稿 1审核中(提交审核) 2发布 3私密。"""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not _can_manage(user, post):
        raise HTTPException(status_code=403, detail="只能操作自己的文章")

    target = data.status
    if target == 2:
        if Perm.POST_PUBLISH not in user.permission_codes:
            raise HTTPException(status_code=403, detail="缺少权限: post:publish")
        post.published_at = datetime.now()
    elif target == 3 and Perm.POST_MANAGE not in user.permission_codes:
        raise HTTPException(status_code=403, detail="缺少权限: post:manage")
    post.status = target
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action=f"status:{target}",
        target_type="post", target_id=post_id,
    )
    status_names = {0: "草稿", 1: "审核中", 2: "已发布", 3: "私密", 4: "回收站"}
    return ok(message=f"已切换为{status_names.get(target, target)}")


@router.post("/{post_id}/like", response_model=dict)
def like_post(
    post_id: int,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """点赞/取消点赞(游客按 IP 去重, 登录用户按账号去重)。"""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    ip = get_client_ip(request)

    query = db.query(PostLike).filter(PostLike.post_id == post_id)
    existing = (
        query.filter(PostLike.user_id == user.id).first()
        if user
        else query.filter(PostLike.ip == ip).first()
    )

    if existing:
        db.delete(existing)
        post.likes_count = max(0, post.likes_count - 1)
        liked = False
    else:
        db.add(PostLike(post_id=post_id, user_id=user.id if user else None, ip=ip))
        post.likes_count += 1
        liked = True
        today_stat = db.query(DailyStat).filter(DailyStat.stat_date == datetime.now().date()).first()
        if today_stat is None:
            today_stat = DailyStat(stat_date=datetime.now().date())
            db.add(today_stat)
        today_stat.likes = (today_stat.likes or 0) + 1

    db.commit()
    return ok(LikeResult(liked=liked, likes_count=post.likes_count))
