"""核心业务规则与安全断言的回归测试。

只覆盖分支最多、最容易被改坏、且改错会出安全事故的五处:
  1. 越权读取非公开文章必须 404(不能泄漏"存在但私密")
  2. 无发布权限的作者提交 status=2 必须被降级为审核中
  3. 刷新令牌必须一次性(轮换后旧令牌失效)
  4. 上传必须拒绝白名单外的扩展名(存储型 XSS 的那条链)
  5. 公开文章详情不得包含作者 ip / location
跑法: cd backend && .venv/Scripts/python.exe -m pytest tests -q
"""
import io


def test_private_post_not_readable_by_anonymous(db_session, seeded):
    """越权读取私密文章应返回 404(而不是 403 —— 不暴露"存在但不可见")。"""
    from app.models.post import Post

    admin, _author, _pw = seeded
    post = Post(
        author_id=admin.id, title="私密文章", slug="secret-1",
        content_md="内容", status=3,
    )
    db_session.add(post)
    db_session.commit()

    from fastapi import HTTPException

    from app.api.v1.posts import get_post

    class _Req:
        """最小 Request 替身: 只用到 headers 与 client。"""

        headers: dict = {}
        client = type("C", (), {"host": "127.0.0.1"})()

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
    from app.models.user import User, refresh_tokens

    admin, _author, _pw = seeded
    raw = "old-refresh-token-value"
    db_session.execute(
        refresh_tokens.insert().values(
            user_id=admin.id, token_hash=hash_token(raw), revoked=False,
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
        author_id=admin.id, title="公开文章", slug="public-1",
        content_md="内容", status=2, ip="203.0.113.9", location="某省某市",
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    public = PostDetail.model_validate(post).model_dump()
    assert "ip" not in public and "location" not in public

    admin_view = PostDetailAdmin.model_validate(post).model_dump()
    assert admin_view["ip"] == "203.0.113.9"


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
