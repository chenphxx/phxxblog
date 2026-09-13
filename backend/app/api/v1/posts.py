"""文章接口: 前台浏览、后台管理、发布流程、点赞、归档。"""
import io
import uuid
import zipfile
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

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
    PostDetailAdmin,
    PostListItem,
    PostStatusIn,
    PostUpdate,
    TagOut,
)
from app.services.archive import (
    frontmatter_lines,
    lookup_image,
    pack_images,
    parse_frontmatter,
    rewrite_import_images,
    save_import_images,
    split_import_archive,
    title_key,
    unique_slug,
)
from app.services.log import write_operation_log
from app.services.markdown import render_markdown
from app.services.geo import resolve_location
from app.services.stats import record_visit
from app.services.post_write import (
    STATUS_NAMES,
    STATUS_PUBLISHED,
    can_manage as _can_manage,
    require_status_transition,
    resolve_submitted_status,
)

router = APIRouter(prefix="/posts", tags=["文章"])


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
    """将请求字段应用到文章(含状态规则、标签、HTML 渲染)。

    状态规则统一走 services/post_write.resolve_submitted_status, 不再就地判断权限码。
    """
    target_status = resolve_submitted_status(data.status, user)

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

    if target_status == STATUS_PUBLISHED and post.published_at is None:
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
    pairs: list[tuple[str, object]] = [
        ("title", post.title),
        ("slug", post.slug),
        ("status", post.status),
    ]
    if post.published_at:
        pairs.append(("date", post.published_at.strftime("%Y-%m-%d %H:%M:%S")))
    if post.summary:
        pairs.append(("summary", post.summary))
    if post.cover_image:
        pairs.append(("cover_image", post.cover_image))
    if post.category:
        pairs.append(("category", post.category.name))
    if post.tags:
        pairs.append(("tags", [t.name for t in post.tags]))
    lines = frontmatter_lines(pairs)
    lines.append("")
    lines.append(post.content_md)
    return "\n".join(lines)


def _rewrite_cover_image(cover: str | None, image_map: dict[str, str]) -> str | None:
    """改写 frontmatter 中的封面图片路径。"""
    if not cover:
        return cover
    return lookup_image(image_map, cover) or cover


def _import_title(meta: dict, body: str, filename: str) -> str:
    """推断文章标题: frontmatter -> 首个一级标题 -> 文件名。"""
    title = str(meta.get("title") or "").strip()
    if not title:
        for line in body.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
    if not title:
        stem = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        title = stem[:-3] if stem.lower().endswith(".md") else stem
    return title


def _existing_titles(db: Session) -> set[str]:
    """已有文章标题的查重键(回收站中的文章不算重复)。"""
    rows = db.query(Post.title).filter(Post.status != 4).all()
    return {title_key(str(title)) for (title,) in rows if str(title).strip()}


def _import_markdown(
    db: Session,
    user: User,
    filename: str,
    content: str,
    image_map: dict[str, str] | None = None,
) -> tuple[bool, str | None]:
    """解析并创建一篇文章(默认草稿)。返回 (是否导入, 错误信息)。"""
    meta, body = parse_frontmatter(content)
    image_map = image_map or {}
    title = _import_title(meta, body, filename)
    if not title:
        return False, f"{filename}: 无法识别标题"

    slug = str(meta.get("slug") or "").strip() or f"post-{uuid.uuid4().hex[:8]}"
    slug = unique_slug(db, Post, slug)

    status = 0
    try:
        raw_status = int(str(meta.get("status") or "0"))
    except (TypeError, ValueError):
        raw_status = 0
    # 与新增/修改共用同一条状态规则(见 services/post_write), 差别只在
    # 越权时的降级目标: 批量导入落"草稿"而不是"审核中"(不宜把导入内容塞进审核队列)。
    resolved = resolve_submitted_status(raw_status, user)
    if raw_status in (0, 1):
        # 草稿/审核中不需要任何权限, 原样保留
        status = raw_status
    elif resolved != raw_status:
        status = 0
    else:
        status = resolved

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
                slug=unique_slug(db, Category, category_name[:80]),
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
                slug=unique_slug(db, Tag, tag_name[:80]),
            )
            db.add(tag)
            db.flush()
        tags.append(tag)

    summary = str(meta.get("summary") or "").strip() or None
    cover_image = str(meta.get("cover_image") or "").strip() or None
    body = rewrite_import_images(body, image_map)
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
            body = pack_images(zf, body, text_for_images, f"images/{slug}")
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
    mode: str = Query("import", pattern="^(check|import)$", description="check=只查重不写入, import=执行导入"),
    on_duplicate: str = Query("skip", pattern="^(skip|all)$", description="重复时: skip=仅导入不重复, all=一并导入"),
    user: User = Depends(require_permission(Perm.POST_CREATE)),
    db: Session = Depends(get_db),
):
    """导入文章: 支持 .md 文件或包含 .md 的 zip 压缩包; mode=check 只返回查重结果。"""
    errors: list[str] = []
    # 每个上传文件拆成 (压缩包内的原始条目, 其中的 md 文件), 便于后续按包共用图片落盘结果
    groups: list[tuple[list[tuple[str, bytes]], list[tuple[str, str]]]] = []
    for upload in files:
        name = upload.filename or "untitled"
        md_files, entries, err = split_import_archive(name, upload.file.read())
        if err:
            errors.append(err)
            continue
        groups.append((entries, md_files))

    # 先整体解析一遍: 与库中已有标题、本批已出现的标题比对, 得出重复情况
    known_titles = _existing_titles(db)
    plans: list[dict] = []
    for group_index, (_entries, md_files) in enumerate(groups):
        for fname, content in md_files:
            meta, body = parse_frontmatter(content)
            title = _import_title(meta, body, fname)
            if not title:
                errors.append(f"{fname}: 无法识别标题")
                continue
            key = title_key(title)
            duplicated = key in known_titles
            known_titles.add(key)
            plans.append({
                "group": group_index,
                "filename": fname,
                "content": content,
                "title": title,
                "duplicated": duplicated,
            })

    duplicates = [plan["title"] for plan in plans if plan["duplicated"]]
    if mode == "check":
        return ok({
            "total": len(plans),
            "duplicates_count": len(duplicates),
            "duplicates": duplicates[:50],
        }, "查重完成")

    image_maps: dict[int, dict[str, str]] = {}

    def image_map_of(group_index: int) -> dict[str, str]:
        """同一份压缩包内的多篇文章共用一次图片落盘结果。"""
        if group_index not in image_maps:
            entries = groups[group_index][0]
            image_maps[group_index] = (
                save_import_images(entries, datetime.now().strftime("%Y/%m")) if entries else {}
            )
        return image_maps[group_index]

    imported = 0
    skipped = 0
    for plan in plans:
        if plan["duplicated"] and on_duplicate == "skip":
            skipped += 1
            continue
        ok_imported, err = _import_markdown(
            db, user, plan["filename"], plan["content"], image_map_of(plan["group"])
        )
        if ok_imported:
            imported += 1
        elif err:
            errors.append(err)
        else:
            skipped += 1
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="import",
        detail={"imported": imported, "skipped": skipped, "duplicates": len(duplicates)},
    )
    return ok({
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:20],
        "duplicates_count": len(duplicates),
    }, "导入完成")


@router.get("/hot", response_model=dict)
def hot_posts(
    limit: int = Query(7, ge=1, le=20, description="返回条数"),
    db: Session = Depends(get_db),
):
    """热门文章(按浏览量倒序, 仅已发布)。"""
    items = (
        db.query(Post)
        .filter(Post.status == 2)
        .order_by(Post.views.desc(), Post.id.desc())
        .limit(limit)
        .all()
    )
    return ok([PostListItem.model_validate(p) for p in items])


def _post_neighbors(db: Session, post: Post) -> tuple[Post | None, Post | None]:
    """查询同一发布序列中紧邻的上一篇(更早)与下一篇(更晚)。

    只在已发布文章之间取邻居, 非已发布文章(草稿预览等)没有"上一篇/下一篇"的语义。

    @param db 数据库会话
    @param post 当前文章
    @return (上一篇, 下一篇), 不存在时对应项为 None
    """
    if post.status != 2 or post.published_at is None:
        return None, None
    published = db.query(Post).filter(Post.status == 2)
    prev_post = (
        published.filter(Post.published_at < post.published_at)
        .order_by(Post.published_at.desc(), Post.id.desc())
        .first()
    )
    next_post = (
        published.filter(Post.published_at > post.published_at)
        .order_by(Post.published_at.asc(), Post.id.asc())
        .first()
    )
    return prev_post, next_post


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
    detail = PostDetail.model_validate(post)
    prev_post, next_post = _post_neighbors(db, post)
    if prev_post is not None:
        detail.prev_post = PostListItem.model_validate(prev_post)
    if next_post is not None:
        detail.next_post = PostListItem.model_validate(next_post)
    return ok(detail)


@router.post("", response_model=dict)
def create_post(
    data: PostCreate,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_CREATE)),
    db: Session = Depends(get_db),
):
    """新增文章(默认草稿, 可提交审核)。"""
    post = Post(author_id=user.id)
    _apply_payload(db, post, data, user, request)
    db.add(post)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action="create",
        target_type="post", target_id=post.id, detail={"title": post.title},
    )
    return ok(PostDetailAdmin.model_validate(post), "已保存")

@router.put("/{post_id}", response_model=dict)
def update_post(
    post_id: int,
    data: PostUpdate,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_EDIT)),
    db: Session = Depends(get_db),
):
    """编辑文章。"""
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
    return ok(PostDetailAdmin.model_validate(post), "保存成功")


@router.delete("/{post_id}", response_model=dict)
def trash_post(
    post_id: int,
    request: Request,
    user: User = Depends(require_permission(Perm.POST_DELETE)),
    db: Session = Depends(get_db),
):
    """删除文章(移入回收站)。"""
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
    # 规则与新增/修改共用(见 services/post_write); 这里越权**报错**而不是降级
    require_status_transition(target, user)
    if target == STATUS_PUBLISHED:
        post.published_at = datetime.now()
    post.status = target
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="post", action=f"status:{target}",
        target_type="post", target_id=post_id,
    )
    return ok(message=f"已切换为{STATUS_NAMES.get(target, target)}")


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
