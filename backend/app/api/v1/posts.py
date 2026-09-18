"""文章接口: 前台浏览、后台管理、发布流程、点赞、归档。"""

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
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
from app.models.post import Post, PostLike
from app.models.user import User
from app.schemas.common import Page
from app.schemas.post import (
    ArchiveGroup,
    LikeResult,
    PostCreate,
    PostDetail,
    PostDetailAdmin,
    PostListItem,
    PostStatusIn,
    PostUpdate,
)
from app.services import post_archive, post_query
from app.services.archive import title_key
from app.services.import_pipeline import run_import
from app.services.log import write_operation_log
from app.services.post_write import (
    STATUS_NAMES,
    STATUS_PUBLISHED,
    apply_payload,
    can_manage as _can_manage,
    require_status_transition,
)
from app.services.stats import record_visit

router = APIRouter(prefix="/posts", tags=["文章"])


def _page_out(items: list[Post], total: int, page: int, page_size: int) -> Page[PostListItem]:
    """把查询结果组装成统一的分页响应(列表接口的出参结构只在这里定义一次)。"""
    return Page[PostListItem](
        items=[PostListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


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
    items, total = post_query.public_list(
        db,
        page=page,
        page_size=page_size,
        category=category,
        tag=tag,
        year=year,
        month=month,
        start_date=start_date,
        end_date=end_date,
        keyword=keyword,
    )
    return ok(_page_out(items, total, page, page_size))


@router.get("/archive", response_model=dict)
def archive(db: Session = Depends(get_db)):
    """归档: 按 年-月 分组展示所有已发布文章。"""
    result = [
        ArchiveGroup(
            year=year,
            month=month,
            count=len(items),
            posts=[PostListItem.model_validate(p) for p in items],
        )
        for year, month, items in post_query.month_groups(db)
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
    items, total = post_query.admin_list(
        db,
        user=user,
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
    )
    return ok(_page_out(items, total, page, page_size))


@router.get("/export", response_model=None)
def export_posts(
    ids: str | None = Query(None, description="逗号分隔的文章ID, 不传则导出全部(作者本人/管理员)"),
    fmt: str = Query(
        "markdown", pattern="^(markdown|html)$", description="导出格式: markdown / html"
    ),
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

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return Response(
        post_archive.build_zip(posts, fmt),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="phxxblog-posts-{stamp}.zip"'},
    )


@router.post("/import", response_model=dict)
def import_posts(
    request: Request,
    files: list[UploadFile] = File(...),
    mode: str = Query(
        "import", pattern="^(check|import)$", description="check=只查重不写入, import=执行导入"
    ),
    on_duplicate: str = Query(
        "skip", pattern="^(skip|all)$", description="重复时: skip=仅导入不重复, all=一并导入"
    ),
    user: User = Depends(require_permission(Perm.POST_CREATE)),
    db: Session = Depends(get_db),
):
    """导入文章: 支持 .md 文件或包含 .md 的 zip 压缩包; mode=check 只返回查重结果。"""
    payload, message = run_import(
        db=db,
        user=user,
        request=request,
        files=files,
        mode=mode,
        on_duplicate=on_duplicate,
        module="post",
        parse=post_archive.parse_import,
        invalid_message=lambda fname: f"{fname}: 无法识别标题",
        existing_keys=lambda: post_archive.existing_title_keys(db),
        dedup_key=lambda plan: title_key(plan["title"]),
        label=lambda plan: plan["title"],
        create=lambda plan, image_map: post_archive.create_from_plan(db, user, plan, image_map),
    )
    return ok(payload, message)


@router.get("/hot", response_model=dict)
def hot_posts(
    limit: int = Query(7, ge=1, le=20, description="返回条数"),
    db: Session = Depends(get_db),
):
    """热门文章(按浏览量倒序, 仅已发布)。"""
    return ok([PostListItem.model_validate(p) for p in post_query.hot(db, limit)])


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
    prev_post, next_post = post_query.neighbors(db, post)
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
    apply_payload(db, post, data, user, get_client_ip(request))
    db.add(post)
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=user,
        module="post",
        action="create",
        target_type="post",
        target_id=post.id,
        detail={"title": post.title},
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
    apply_payload(db, post, data, user, get_client_ip(request))
    db.commit()
    write_operation_log(
        db,
        request=request,
        user=user,
        module="post",
        action="update",
        target_type="post",
        target_id=post.id,
        detail={"title": post.title},
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
        db,
        request=request,
        user=user,
        module="post",
        action="trash",
        target_type="post",
        target_id=post_id,
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
        db,
        request=request,
        user=user,
        module="post",
        action="force_delete",
        target_type="post",
        target_id=post_id,
        detail={"title": title},
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
        db,
        request=request,
        user=user,
        module="post",
        action="restore",
        target_type="post",
        target_id=post_id,
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
        db,
        request=request,
        user=user,
        module="post",
        action=f"status:{target}",
        target_type="post",
        target_id=post_id,
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
        today_stat = (
            db.query(DailyStat).filter(DailyStat.stat_date == datetime.now().date()).first()
        )
        if today_stat is None:
            today_stat = DailyStat(stat_date=datetime.now().date())
            db.add(today_stat)
        today_stat.likes = (today_stat.likes or 0) + 1

    db.commit()
    return ok(LikeResult(liked=liked, likes_count=post.likes_count))
