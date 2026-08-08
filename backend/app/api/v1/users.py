"""用户/角色/权限管理接口。"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.core.security import hash_password
from app.models.user import Permission, Role, User
from app.schemas.common import Page
from app.schemas.user import PermissionOut, RoleIn, RoleOut, UserCreate, UserOut, UserUpdate
from app.services.log import write_operation_log

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=dict)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, description="按用户名/昵称/邮箱搜索"),
    _: User = Depends(require_permission(Perm.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    """用户列表(管理端)。"""
    query = db.query(User)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(User.username.like(like), User.nickname.like(like), User.email.like(like))
        )
    total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ok(Page[UserOut](items=[UserOut.model_validate(u) for u in items], total=total, page=page, page_size=page_size))


@router.post("", response_model=dict)
def create_user(
    data: UserCreate,
    request: Request,
    _: User = Depends(require_permission(Perm.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    """创建用户。"""
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    user = User(
        username=data.username,
        email=str(data.email),
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.username,
    )
    if data.roles:
        roles = db.query(Role).filter(Role.code.in_(data.roles)).all()
        user.roles = roles
    db.add(user)
    db.commit()
    write_operation_log(
        db, request=request, user=_, module="user", action="create",
        target_type="user", target_id=user.id, detail={"username": user.username},
    )
    return ok(UserOut.model_validate(user), "创建成功")


@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    admin: User = Depends(require_permission(Perm.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    """编辑用户。"""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    changes = data.model_dump(exclude_unset=True)
    roles = changes.pop("roles", None)
    for field, value in changes.items():
        setattr(user, field, value)
    if roles is not None:
        user.roles = db.query(Role).filter(Role.code.in_(roles)).all()
    db.commit()
    write_operation_log(
        db, request=request, user=admin, module="user", action="update",
        target_type="user", target_id=user.id, detail=changes,
    )
    return ok(UserOut.model_validate(user), "保存成功")


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    request: Request,
    admin: User = Depends(require_permission(Perm.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除用户(不允许删除自己)。"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    write_operation_log(
        db, request=request, user=admin, module="user", action="delete",
        target_type="user", target_id=user_id, detail={"username": user.username},
    )
    return ok(message="删除成功")


# ---------- 角色 ----------


@router.get("/roles", response_model=dict)
def list_roles(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """角色列表(含权限码)。"""
    roles = db.query(Role).all()
    return ok([
        RoleOut(
            id=r.id, name=r.name, code=r.code, description=r.description,
            permission_codes=[p.code for p in r.permissions],
        )
        for r in roles
    ])


@router.post("/roles", response_model=dict)
def create_role(
    data: RoleIn,
    request: Request,
    admin: User = Depends(require_permission(Perm.ROLE_MANAGE)),
    db: Session = Depends(get_db),
):
    """创建角色。"""
    if db.query(Role).filter(Role.code == data.code).first():
        raise HTTPException(status_code=400, detail="角色代码已存在")
    role = Role(name=data.name, code=data.code, description=data.description)
    role.permissions = db.query(Permission).filter(Permission.code.in_(data.permission_codes)).all()
    db.add(role)
    db.commit()
    write_operation_log(
        db, request=request, user=admin, module="role", action="create",
        target_type="role", target_id=role.id, detail={"code": role.code},
    )
    return ok(message="创建成功")


@router.put("/roles/{role_id}", response_model=dict)
def update_role(
    role_id: int,
    data: RoleIn,
    request: Request,
    admin: User = Depends(require_permission(Perm.ROLE_MANAGE)),
    db: Session = Depends(get_db),
):
    """编辑角色及其权限。"""
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    role.name = data.name
    role.code = data.code
    role.description = data.description
    role.permissions = db.query(Permission).filter(Permission.code.in_(data.permission_codes)).all()
    db.commit()
    write_operation_log(
        db, request=request, user=admin, module="role", action="update",
        target_type="role", target_id=role_id,
    )
    return ok(message="保存成功")


@router.delete("/roles/{role_id}", response_model=dict)
def delete_role(
    role_id: int,
    request: Request,
    admin: User = Depends(require_permission(Perm.ROLE_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除角色。"""
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.code == "admin":
        raise HTTPException(status_code=400, detail="不能删除内置管理员角色")
    db.delete(role)
    db.commit()
    write_operation_log(
        db, request=request, user=admin, module="role", action="delete",
        target_type="role", target_id=role_id,
    )
    return ok(message="删除成功")


@router.get("/permissions", response_model=dict)
def list_permissions(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """权限列表。"""
    perms = db.query(Permission).order_by(Permission.code).all()
    return ok([PermissionOut.model_validate(p) for p in perms])
