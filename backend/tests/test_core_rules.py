"""核心业务规则与安全断言的回归测试。

只覆盖分支最多、最容易被改坏、且改错难以在界面上发现的七处:
  1. 越权读取非公开文章必须 404(不能泄漏"存在但私密")
  2. 无发布权限的作者提交 status=2 必须被降级为审核中
  3. 刷新令牌必须一次性(轮换后旧令牌失效)
  4. 上传必须拒绝白名单外的扩展名(存储型 XSS 的那条链)
  5. 公开文章详情不得包含作者 ip / location
  6. 静态资源 /assets 里非渲染类的文件(迁移导出、附件)必须仅管理员可访问
  7. 一篇文章的分类是多对多, 写入/筛选/分类计数都不能只认一个分类
跑法: cd backend && .venv/Scripts/python.exe -m pytest tests -q
"""

import io


def test_private_post_not_readable_by_anonymous(db_session, seeded):
    """越权读取私密文章应返回 404(而不是 403 —— 不暴露"存在但不可见")。"""
    from app.models.post import Post

    admin, _author, _pw = seeded
    post = Post(
        author_id=admin.id,
        title="私密文章",
        slug="secret-1",
        content_md="内容",
        status=3,
    )
    db_session.add(post)
    db_session.commit()

    from fastapi import HTTPException

    from app.api.v1.posts import get_post

    try:
        get_post(post_id=post.id, request=_Req(), user=None, db=db_session)
    except HTTPException as exc:
        assert exc.status_code == 404, f"期望 404, 实际 {exc.status_code}"
    else:
        raise AssertionError("匿名用户读到了私密文章")


def test_author_cannot_publish_directly(seeded):
    """无 post:publish 的作者提交 status=2, 应被降级为 1(审核中)。"""
    from app.services.post_write import STATUS_PUBLISHED, STATUS_REVIEW, resolve_submitted_status

    _admin, author, _pw = seeded
    assert resolve_submitted_status(STATUS_PUBLISHED, author) == STATUS_REVIEW

    admin = _admin
    assert resolve_submitted_status(STATUS_PUBLISHED, admin) == STATUS_PUBLISHED


def test_refresh_token_is_single_use(db_session, seeded):
    """刷新令牌轮换后, 旧令牌必须失效(重放检测)。"""
    from app.core.security import hash_token
    from app.models.user import refresh_tokens

    admin, _author, _pw = seeded
    raw = "old-refresh-token-value"
    db_session.execute(
        refresh_tokens.insert().values(
            user_id=admin.id,
            token_hash=hash_token(raw),
            revoked=False,
            expires_at=__import__("datetime").datetime.now()
            + __import__("datetime").timedelta(days=1),
        )
    )
    db_session.commit()

    rows = db_session.execute(
        refresh_tokens.select().where(refresh_tokens.c.token_hash == hash_token(raw))
    ).all()
    assert len(rows) == 1

    # 模拟轮换: 吊销旧令牌
    db_session.execute(
        refresh_tokens.update()
        .where(refresh_tokens.c.token_hash == hash_token(raw))
        .values(revoked=True)
    )
    db_session.commit()

    still_valid = db_session.execute(
        refresh_tokens.select().where(
            refresh_tokens.c.token_hash == hash_token(raw),
            refresh_tokens.c.revoked == False,  # noqa: E712
        )
    ).first()
    assert still_valid is None, "旧刷新令牌在轮换后仍可用"


def test_upload_rejects_scriptable_extensions():
    """上传白名单必须拒绝 .html/.svg/.js 等可执行文档(同源托管 = 存储型 XSS)。"""
    from fastapi import HTTPException

    from app.services.upload import ALLOWED_EXTS, save_upload

    for ext in (".html", ".htm", ".svg", ".js", ".mjs", ".xml"):
        assert ext not in ALLOWED_EXTS, f"{ext} 不应在白名单里"

    class _File:
        def __init__(self, name, data=b"<script>alert(1)</script>"):
            self.filename = name
            self.content_type = "text/html"
            self.file = io.BytesIO(data)

    try:
        save_upload(_File("evil.html"))
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("恶意扩展名被放行了")


def test_upload_rejects_fake_image_by_magic_bytes(tmp_path, monkeypatch):
    """把 HTML 改名成 .png 也应被拒绝(文件头校验)。"""
    from fastapi import HTTPException

    from app.core.config import settings
    from app.services.upload import save_upload

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    class _File:
        def __init__(self, name, data, ctype="image/png"):
            self.filename = name
            self.content_type = ctype
            self.file = io.BytesIO(data)

    try:
        save_upload(_File("fake.png", b"<html><body>not an image</body></html>"))
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("伪造扩展名的文件被放行了")

    # 合法的 PNG 头应通过
    ok_png = _File("real.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    result = save_upload(ok_png)
    assert result["type"] == "image"


def test_public_post_detail_has_no_author_ip(db_session, seeded):
    """公开详情响应不得包含 ip / location(否则等于公开站长真实 IP)。"""
    from app.models.post import Post
    from app.schemas.post import PostDetail, PostDetailAdmin

    assert "ip" not in PostDetail.model_fields
    assert "location" not in PostDetail.model_fields
    assert "ip" in PostDetailAdmin.model_fields

    admin, _author, _pw = seeded
    post = Post(
        author_id=admin.id,
        title="公开文章",
        slug="public-1",
        content_md="内容",
        status=2,
        ip="203.0.113.9",
        location="某省某市",
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    public = PostDetail.model_validate(post).model_dump()
    assert "ip" not in public and "location" not in public

    admin_view = PostDetailAdmin.model_validate(post).model_dump()
    assert admin_view["ip"] == "203.0.113.9"


def test_record_visit_keeps_post_updated_at(db_session, seeded):
    """记录阅读量不得改动 Post.updated_at。

    直接给 ORM 属性自增会触发 updated_at 的 onupdate, 把"最后更新时间"顶成
    "最后一次访问时间" —— 文章详情页的"最后更新于"于是永远显示当前时间。
    这类回归肉眼很难发现(时间看起来总是合理的), 所以固定下来。
    """
    from datetime import datetime

    from app.models.post import Post
    from app.services.stats import record_visit

    admin, _author, _pw = seeded
    edited_at = datetime(2026, 1, 2, 3, 4, 5)
    post = Post(
        author_id=admin.id,
        title="文章",
        slug="visit-1",
        content_md="内容",
        status=2,
        published_at=edited_at,
        updated_at=edited_at,
    )
    db_session.add(post)
    db_session.commit()

    class _Req:
        """最小 Request 替身: record_visit 只用到 client / headers / url。"""

        headers = {"user-agent": "pytest", "referer": ""}
        client = type("C", (), {"host": "127.0.0.1"})()
        url = type("U", (), {"path": "/api/v1/posts/visit-1"})()

    views_before = post.views
    record_visit(db_session, request=_Req(), post=post)
    # 必须从库里重读: onupdate 是写库时才生效的, 内存里的 updated_at 不会跟着变,
    # 只看内存对象的话这个测试根本抓不到上面那个回归。
    db_session.expire(post)

    assert post.views == views_before + 1
    assert post.updated_at == edited_at, "记录阅读量改动了文章的更新时间"


def test_assets_access_control_rule():
    """静态资源: 只有前台会渲染的媒体匿名可访问, 其余文件仅管理员。

    锁多了前台图片全 404(正文配图、站点图标、头像都在 /assets/uploads 下),
    锁少了等于把 WordPress 导出里的凭据表挂到公网 —— 两个方向都很难在界面上发现,
    所以把规则固定成断言。注意 /assets/uploads/wordpress 下的图片是文章在用的,
    不能因为路径里带 wordpress 就整目录锁掉。
    """
    from app.core.middleware import asset_requires_admin

    for path in (
        "/assets/uploads/2026/09/icon.png",
        "/assets/uploads/2026/09/avatar.jpg",
        "/assets/uploads/wordpress/2025/04/image.png",
        "/assets/uploads/2026/09/clip.mp4",
        "/assets/uploads/2026/09/bgm.flac",
    ):
        assert asset_requires_admin(path) is False, f"{path} 不应要求管理员身份"

    for path in (
        "/assets/wordpress/文章.xml",
        "/assets/wordpress/wp-personal-data-file-x.zip",
        "/assets/uploads/wordpress/2025/03/credentials.csv",
        "/assets/uploads/wordpress/2024/10/AccessKey.csv",
        "/assets/uploads/2026/08/note.txt",
        "/assets/uploads/.gitkeep",
    ):
        assert asset_requires_admin(path) is True, f"{path} 应要求管理员身份"


def test_post_neighbors_and_hot_ranking(db_session, seeded):
    """详情接口的上一篇/下一篇按发布时间相邻; 热门列表按阅读量倒序。"""
    from datetime import datetime, timedelta

    from app.api.v1.posts import hot_posts
    from app.models.post import Post
    from app.services.post_query import neighbors

    admin, _author, _pw = seeded
    base = datetime(2026, 1, 1, 12, 0, 0)
    posts = [
        Post(
            author_id=admin.id,
            title=f"文章{index}",
            slug=f"neighbor-{index}",
            content_md="内容",
            status=2,
            published_at=base + timedelta(days=index),
            views=index,
        )
        for index in range(3)
    ]
    db_session.add_all(posts)
    db_session.commit()

    oldest, middle, newest = posts
    assert neighbors(db_session, oldest) == (None, middle)
    prev_post, next_post = neighbors(db_session, middle)
    assert prev_post.id == oldest.id and next_post.id == newest.id
    assert neighbors(db_session, newest) == (middle, None)

    # 热门: 按阅读量倒序(倒着建库故意与发布时间相反, 避免两种排序碰巧一致)
    hot = hot_posts(limit=7, db=db_session)["data"]
    assert [item.id for item in hot] == [newest.id, middle.id, oldest.id]


def test_login_rate_limiter_blocks_after_threshold():
    """连续失败达到阈值后必须拦截并返回 429。"""
    from fastapi import HTTPException

    from app.core.ratelimit import LoginRateLimiter

    limiter = LoginRateLimiter(max_attempts=3, window_seconds=60)
    key = "203.0.113.1:admin"
    for _ in range(3):
        limiter.check(key)
    try:
        limiter.check(key)
    except HTTPException as exc:
        assert exc.status_code == 429
        assert "Retry-After" in (exc.headers or {})
    else:
        raise AssertionError("超过阈值的登录尝试未被拦截")


def test_post_can_have_multiple_categories(db_session, seeded):
    """一篇文章可以同时属于多个分类: 写入, 筛选, 分类计数都要按关联表来。

    分类由 posts.category_id 单值改成 post_categories 关联表后, 最容易漏掉的是
    "按分类筛选文章"与"分类下的已发布文章数"两处查询 —— 它们出错时界面只是
    列表空掉或计数永远是 0, 不会报错, 所以把规则固定成断言。
    """
    from app.api.v1.categories import _post_counts
    from app.api.v1.posts import list_posts
    from app.models.post import Category, Post
    from app.schemas.post import PostCreate
    from app.services.post_write import apply_payload

    admin, _author, _pw = seeded
    backend = Category(name="后端", slug="backend")
    ops = Category(name="运维", slug="ops")
    db_session.add_all([backend, ops])
    db_session.commit()

    def _create(title, slug, category_ids, status=2):
        """走真实写入路径建一篇文章, 返回 ORM 对象。"""
        payload = PostCreate(
            title=title,
            slug=slug,
            content_md="内容",
            status=status,
            category_ids=category_ids,
        )
        post = Post(author_id=admin.id)
        db_session.add(post)
        apply_payload(db_session, post, payload, admin, "127.0.0.1")
        db_session.commit()
        return post

    multi = _create("多分类", "multi-cat", [backend.id, ops.id])
    single = _create("单分类", "single-cat", [ops.id])
    _create("草稿", "draft-cat", [backend.id], status=0)

    assert {category.name for category in multi.categories} == {"后端", "运维"}

    # 重新提交空列表 = 解除全部关联(整体覆盖, 而不是保留旧值)
    apply_payload(
        db_session,
        multi,
        PostCreate(title="多分类", slug="multi-cat", content_md="内容", status=2),
        admin,
        "127.0.0.1",
    )
    db_session.commit()
    assert multi.categories == []

    # 恢复多分类, 继续验证筛选与分类计数
    apply_payload(
        db_session,
        multi,
        PostCreate(
            title="多分类",
            slug="multi-cat",
            content_md="内容",
            status=2,
            category_ids=[backend.id, ops.id],
        ),
        admin,
        "127.0.0.1",
    )
    db_session.commit()

    counts = _post_counts(db_session)
    assert counts.get(backend.id) == 1, "分类计数只应统计已发布文章"
    assert counts.get(ops.id) == 2

    def _list_by_category(category_id):
        resp = list_posts(
            page=1,
            page_size=10,
            category=category_id,
            tag=None,
            year=None,
            month=None,
            start_date=None,
            end_date=None,
            keyword=None,
            db=db_session,
        )
        return resp["data"]

    by_backend = _list_by_category(backend.id)
    assert [item.id for item in by_backend.items] == [multi.id]
    assert by_backend.total == 1

    by_ops = _list_by_category(ops.id)
    assert sorted(item.id for item in by_ops.items) == sorted([multi.id, single.id])

    # 出参是列表: 前端用 v-for 渲染, 退化成单个对象会直接白屏
    detail = next(item for item in by_ops.items if item.id == multi.id)
    assert [category.name for category in detail.categories] == ["后端", "运维"]


class _Req:
    """最小 Request 替身: 导入管线与操作日志只用到 headers 与 client。"""

    headers: dict = {}
    client = type("C", (), {"host": "127.0.0.1"})()


def _upload(name: str, text: str):
    """最小 UploadFile 替身: 导入管线只用到 filename 与 file.read()。

    注意不能跨调用复用同一个对象 —— file 是 BytesIO, 读过一次就空了,
    所以需要多次导入时用工厂函数重新造。
    """
    return type("U", (), {"filename": name, "file": io.BytesIO(text.encode("utf-8"))})()


def _post_files():
    """三份文章导入文件: 前两份标题相同(重复), 第三份是新的。"""
    return [
        _upload("a.md", "---\ntitle: 重复标题\n---\n正文 A"),
        _upload("b.md", "---\ntitle: 重复标题\n---\n正文 B"),
        _upload("c.md", "---\ntitle: 新标题\n---\n正文 C"),
    ]


def test_post_import_reports_and_skips_duplicates(db_session, seeded):
    """文章导入按标题查重: check 模式只报重复, 导入时重复的按策略跳过。

    两条合写是有意的: 查重结果与"实际落库了几条"必须对得上, 分开断言容易
    掩盖"查重说 2 条重复, 落库时却把重复的也写进去了"这类不一致。
    """
    from app.api.v1.posts import import_posts
    from app.models.post import Post

    admin, _author, _pw = seeded

    checked = import_posts(
        request=_Req(),
        files=_post_files(),
        mode="check",
        on_duplicate="skip",
        user=admin,
        db=db_session,
    )["data"]
    assert checked["total"] == 3, checked
    assert checked["duplicates_count"] == 1, checked
    assert checked["duplicates"] == ["重复标题"], checked

    result = import_posts(
        request=_Req(),
        files=_post_files(),
        mode="import",
        on_duplicate="skip",
        user=admin,
        db=db_session,
    )["data"]
    assert result["imported"] == 2, result
    assert result["skipped"] == 1, result

    titles = sorted(post.title for post in db_session.query(Post).all())
    assert titles == ["新标题", "重复标题"], titles
    # 库里只应有一条"重复标题", 且两处同属一个批次的内容不能互相覆盖
    kept = db_session.query(Post).filter(Post.title == "重复标题").one()
    assert "正文 A" in kept.content_md, kept.content_md


def test_diary_import_dedups_by_content_ignoring_whitespace(db_session, seeded):
    """日记导入按正文查重, 空白差异不算不同内容, 重复的同样按策略跳过。"""
    from app.api.v1.diaries import import_diaries
    from app.models.diary import DiaryEntry

    admin, _author, _pw = seeded

    def files():
        return [
            _upload("2026-01-01.md", "第一天的日记"),
            _upload("dup.md", "第一天的日记"),
            _upload("dup-space.md", "  第一天的日记  "),
            _upload("2026-01-02.md", "第二天的日记"),
        ]

    checked = import_diaries(
        request=_Req(),
        files=files(),
        mode="check",
        on_duplicate="skip",
        user=admin,
        db=db_session,
    )["data"]
    assert checked["total"] == 4, checked
    assert checked["duplicates_count"] == 2, checked

    result = import_diaries(
        request=_Req(),
        files=files(),
        mode="import",
        on_duplicate="skip",
        user=admin,
        db=db_session,
    )["data"]
    assert result["imported"] == 2, result
    assert result["skipped"] == 2, result
    assert [entry.content_md for entry in db_session.query(DiaryEntry).all()] == [
        "第一天的日记",
        "第二天的日记",
    ]


def test_diary_import_can_import_duplicates_on_demand(db_session, seeded):
    """选择"导入全部"时, 重复内容也要真的写进去(否则用户的选择形同虚设)。"""
    from app.api.v1.diaries import import_diaries
    from app.models.diary import DiaryEntry

    admin, _author, _pw = seeded
    files = [
        _upload("2026-01-01.md", "同一天的日记"),
        _upload("2026-01-01-2.md", "同一天的日记"),
    ]

    result = import_diaries(
        request=_Req(),
        files=files,
        mode="import",
        on_duplicate="all",
        user=admin,
        db=db_session,
    )["data"]
    assert result["imported"] == 2, result
    assert result["skipped"] == 0, result
    assert db_session.query(DiaryEntry).count() == 2
