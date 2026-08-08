"""认证接口: 注册/登录/刷新/注销/个人信息/密码/邮箱。"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_client_ip, get_current_user
from app.core.response import ok
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User, refresh_tokens
from app.schemas.auth import (
    EmailChangeIn,
    LoginIn,
    PasswordChangeIn,
    RefreshIn,
    RegisterIn,
    TokenPair,
)
from app.schemas.user import UserOut
from app.services.log import write_operation_log

router = APIRouter(prefix="/auth", tags=["认证"])


def _issue_tokens(db: Session, user: User, request: Request) -> TokenPair:
    """签发访问令牌与刷新令牌, 并将刷新令牌会话写入数据库。"""
    access_token = create_access_token(user.id, extra={"username": user.username})
    refresh_token = generate_refresh_token()
    db.execute(
        refresh_tokens.insert().values(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now() + timedelta(days=settings.refresh_token_expire_days),
            ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent", "")[:500],
        )
    )
    db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=dict)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    """注册账号, 默认赋予 author 角色, 注册成功后直接登录。"""
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        username=data.username,
        email=str(data.email),
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.username,
    )
    db.add(user)
    db.flush()

    # 默认授予 author 角色(由 seed 初始化)
    from app.models.user import Role

    author_role = db.query(Role).filter(Role.code == "author").first()
    if author_role:
        user.roles.append(author_role)

    db.commit()
    db.refresh(user)
    write_operation_log(db, request=request, user=user, module="auth", action="register")
    tokens = _issue_tokens(db, user, request)
    return ok({"user": UserOut.model_validate(user), "tokens": tokens.model_dump()}, "注册成功")


@router.post("/login", response_model=dict)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    """登录, 支持用户名或邮箱。"""
    user = (
        db.query(User)
        .filter(or_(User.username == data.username, User.email == data.username))
        .first()
    )
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if user.status == 0:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    user.last_login_at = datetime.now()
    db.commit()
    write_operation_log(db, request=request, user=user, module="auth", action="login")
    tokens = _issue_tokens(db, user, request)
    return ok({"user": UserOut.model_validate(user), "tokens": tokens.model_dump()}, "登录成功")


@router.post("/refresh", response_model=dict)
def refresh_token(data: RefreshIn, request: Request, db: Session = Depends(get_db)):
    """刷新访问令牌, 同时轮换刷新令牌。"""
    token_hash = hash_token(data.refresh_token)
    row = (
        db.execute(
            refresh_tokens.select().where(
                refresh_tokens.c.token_hash == token_hash,
                refresh_tokens.c.revoked == False,  # noqa: E712
            )
        )
        .mappings()
        .first()
    )
    if row is None or row["expires_at"] < datetime.now():
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

    # 吊销旧令牌并签发新令牌(轮换)
    db.execute(
        refresh_tokens.update()
        .where(refresh_tokens.c.id == row["id"])
        .values(revoked=True)
    )
    user = db.get(User, row["user_id"])
    if user is None or user.status == 0:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    tokens = _issue_tokens(db, user, request)
    return ok(tokens.model_dump())


@router.post("/logout", response_model=dict)
def logout(data: RefreshIn, db: Session = Depends(get_db)):
    """注销登录, 吊销刷新令牌。"""
    db.execute(
        refresh_tokens.update()
        .where(refresh_tokens.c.token_hash == hash_token(data.refresh_token))
        .values(revoked=True)
    )
    db.commit()
    return ok(message="已退出登录")


@router.get("/me", response_model=dict)
def me(user: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return ok(UserOut.model_validate(user))


@router.put("/password", response_model=dict)
def change_password(
    data: PasswordChangeIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """修改密码。"""
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    write_operation_log(db, request=request, user=user, module="auth", action="change_password")
    return ok(message="密码修改成功")


@router.put("/email", response_model=dict)
def change_email(
    data: EmailChangeIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """修改邮箱。"""
    if db.query(User).filter(User.email == str(data.email), User.id != user.id).first():
        raise HTTPException(status_code=400, detail="邮箱已被使用")
    user.email = str(data.email)
    db.commit()
    write_operation_log(db, request=request, user=user, module="auth", action="change_email")
    return ok(message="邮箱修改成功")
