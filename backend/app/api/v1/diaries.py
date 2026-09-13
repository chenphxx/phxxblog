"""日记接口(仅管理员)。"""
import io
import re
import zipfile
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.pagination import paginate
from app.core.response import ok
from app.models.diary import DiaryEntry
from app.models.user import User
from app.schemas.diary import DiaryIn, DiaryOut
from app.services.archive import (
    frontmatter_lines,
    normalize_content,
    pack_images,
    parse_frontmatter,
    rewrite_import_images,
    save_import_images,
    split_import_archive,
)
from app.services.log import write_operation_log
from app.services.markdown import render_markdown

router = APIRouter(prefix="/diaries", tags=["日记"])

# 文件名中的日期前缀(导出后可直接再导入)
_DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")



def _diary_to_markdown(entry: DiaryEntry) -> str:
    """将日记序列化为带 YAML frontmatter 的 Markdown 文本。"""
    lines = frontmatter_lines([
        ("date", entry.entry_date.strftime("%Y-%m-%d")),
        ("created_at", entry.created_at.strftime("%Y-%m-%d %H:%M:%S")),
    ])
    lines.append("")
    lines.append(entry.content_md)
    return "\n".join(lines)


def _diary_to_html(entry: DiaryEntry) -> str:
    """将日记序列化为完整 HTML 文档。"""
    content = entry.content_html or render_markdown(entry.content_md)
    return (
        "<!DOCTYPE html>\n<html lang='zh-CN'>\n<head>\n<meta charset='utf-8'>\n"
        f"<title>{entry.entry_date.strftime('%Y-%m-%d')} 日记</title>\n</head>\n<body>\n{content}\n</body>\n</html>"
    )


def _parse_diary_date(value: object) -> date | None:
    """解析日期, 支持 YYYY-MM-DD 与 YYYY-MM-DD HH:MM:SS。"""
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_diary_datetime(value: object) -> datetime | None:
    """解析 created_at(YYYY-MM-DD HH:MM:SS), 解析失败返回 None。"""
    text = str(value or "").strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _parse_diary_import(filename: str, content: str) -> dict | None:
    """解析导入内容, 返回 {body, entry_date, created_at}; 正文为空返回 None。"""
    meta, body = parse_frontmatter(content)
    body = body.strip()
    if not body:
        return None
    entry_date = _parse_diary_date(meta.get("date"))
    if entry_date is None:
        match = _DATE_PREFIX_RE.match(filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
        entry_date = _parse_diary_date(match.group(1)) if match else None
    return {
        "body": body,
        "entry_date": entry_date or date.today(),
        "created_at": _parse_diary_datetime(meta.get("created_at")),
    }


def _create_diary(
    db: Session,
    user: User,
    plan: dict,
    image_map: dict[str, str] | None = None,
) -> DiaryEntry:
    """按解析结果创建一条日记, 并把正文中的图片相对路径改写为可访问地址。"""
    body = rewrite_import_images(plan["body"], image_map or {}).strip()
    entry = DiaryEntry(
        user_id=user.id,
        content_md=body,
        content_html=render_markdown(body),
        entry_date=plan["entry_date"],
    )
    if plan["created_at"] is not None:
        entry.created_at = plan["created_at"]
    db.add(entry)
    db.flush()
    return entry


def _existing_diary_keys(db: Session) -> set[str]:
    """已有日记正文的查重键。"""
    rows = db.query(DiaryEntry.content_md).all()
    return {normalize_content(str(content)) for (content,) in rows if content}


def _diary_import_label(plan: dict) -> str:
    """重复提示用的日记摘要: 日期 + 正文前 20 个字。"""
    preview = re.sub(r"\s+", " ", plan["body"]).strip()[:20]
    return f"{plan['entry_date']} · {preview}"


@router.get("", response_model=dict)
def list_diaries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(require_permission(Perm.DIARY_MANAGE)),
    db: Session = Depends(get_db),
):
    """日记列表(按日期倒序)。"""
    query = db.query(DiaryEntry).order_by(
        DiaryEntry.entry_date.desc(), DiaryEntry.created_at.desc()
    )
    return ok(paginate(query, page, page_size, DiaryOut))


@router.get("/export", response_model=None)
def export_diaries(
    ids: str | None = Query(None, description="逗号分隔的日记ID, 不传则导出全部"),
    fmt: str = Query("markdown", pattern="^(markdown|html)$", description="导出格式: markdown / html"),
    user: User = Depends(require_permission(Perm.DIARY_MANAGE)),
    db: Session = Depends(get_db),
):
    """导出日记压缩包(markdown/html, 正文引用的图片一并打包; 仅管理员)。"""
    query = db.query(DiaryEntry)
    if ids:
        id_list = [int(i) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(DiaryEntry.id.in_(id_list))
    entries = query.order_by(DiaryEntry.entry_date.asc(), DiaryEntry.created_at.asc()).all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        used: set[str] = set()
        for entry in entries:
            stem = entry.entry_date.strftime("%Y-%m-%d")
            name = stem
            index = 2
            while name in used:
                # 同一天写多条日记时追加序号, 避免同名覆盖
                name = f"{stem}-{index}"
                index += 1
            used.add(name)
            if fmt == "html":
                body = _diary_to_html(entry)
                filename = f"{name}.html"
            else:
                body = _diary_to_markdown(entry)
                filename = f"{name}.md"
            body = pack_images(zf, body, body, f"images/{name}")
            zf.writestr(filename, body)
    buf.seek(0)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return Response(
        buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="phxxblog-diaries-{stamp}.zip"'},
    )


@router.post("/import", response_model=dict)
def import_diaries(
    request: Request,
    files: list[UploadFile] = File(...),
    mode: str = Query("import", pattern="^(check|import)$", description="check=只查重不写入, import=执行导入"),
    on_duplicate: str = Query("skip", pattern="^(skip|all)$", description="重复时: skip=仅导入不重复, all=一并导入"),
    user: User = Depends(require_permission(Perm.DIARY_MANAGE)),
    db: Session = Depends(get_db),
):
    """导入日记: 支持 .md 文件或包含 .md 的 zip 压缩包; mode=check 只返回查重结果。"""
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

    # 先整体解析一遍: 与库中已有正文、本批已出现的正文比对, 得出重复情况
    known_keys = _existing_diary_keys(db)
    plans: list[dict] = []
    for group_index, (_entries, md_files) in enumerate(groups):
        for fname, content in md_files:
            parsed = _parse_diary_import(fname, content)
            if parsed is None:
                errors.append(f"{fname}: 内容为空, 已跳过")
                continue
            key = normalize_content(parsed["body"])
            duplicated = key in known_keys
            known_keys.add(key)
            plans.append({
                "group": group_index,
                "filename": fname,
                "duplicated": duplicated,
                **parsed,
            })

    duplicates = [_diary_import_label(plan) for plan in plans if plan["duplicated"]]
    if mode == "check":
        return ok({
            "total": len(plans),
            "duplicates_count": len(duplicates),
            "duplicates": duplicates[:50],
        }, "查重完成")

    image_maps: dict[int, dict[str, str]] = {}

    def image_map_of(group_index: int) -> dict[str, str]:
        """同一份压缩包内的多条日记共用一次图片落盘结果。"""
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
        _create_diary(db, user, plan, image_map_of(plan["group"]))
        imported += 1
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="diary", action="import",
        detail={"imported": imported, "skipped": skipped, "duplicates": len(duplicates)},
    )
    return ok({
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:20],
        "duplicates_count": len(duplicates),
    }, "导入完成")


@router.post("", response_model=dict)
def create_diary(
    data: DiaryIn,
    request: Request,
    user: User = Depends(require_permission(Perm.DIARY_MANAGE)),
    db: Session = Depends(get_db),
):
    """新增日记。"""
    entry = DiaryEntry(
        user_id=user.id,
        content_md=data.content_md,
        content_html=render_markdown(data.content_md),
        entry_date=data.entry_date or date.today(),
    )
    db.add(entry)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="diary", action="create",
        target_type="diary", target_id=entry.id,
    )
    return ok(DiaryOut.model_validate(entry), "日记已保存")


@router.put("/{diary_id}", response_model=dict)
def update_diary(
    diary_id: int,
    data: DiaryIn,
    request: Request,
    user: User = Depends(require_permission(Perm.DIARY_MANAGE)),
    db: Session = Depends(get_db),
):
    """编辑日记。"""
    entry = db.get(DiaryEntry, diary_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="日记不存在")
    entry.content_md = data.content_md
    entry.content_html = render_markdown(data.content_md)
    if data.entry_date:
        entry.entry_date = data.entry_date
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="diary", action="update",
        target_type="diary", target_id=diary_id,
    )
    return ok(DiaryOut.model_validate(entry), "保存成功")


@router.delete("/{diary_id}", response_model=dict)
def delete_diary(
    diary_id: int,
    request: Request,
    user: User = Depends(require_permission(Perm.DIARY_MANAGE)),
    db: Session = Depends(get_db),
):
    """删除日记。"""
    entry = db.get(DiaryEntry, diary_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="日记不存在")
    db.delete(entry)
    db.commit()
    write_operation_log(
        db, request=request, user=user, module="diary", action="delete",
        target_type="diary", target_id=diary_id,
    )
    return ok(message="删除成功")
