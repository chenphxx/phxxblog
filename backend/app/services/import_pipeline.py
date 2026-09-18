"""导入管线: 文章与日记共用的"上传 -> 解析 -> 查重 -> 落库"流程。

为什么单独抽一个模块:
    文章与日记的导入骨架此前是逐行重复的两份实现, 连"同一份压缩包共用一次图片落盘"
    的闭包与注释都一样, 真正不同的只有三件事: 怎么解析, 拿什么查重, 怎么落库。
    两份实现改一处忘一处是迟早的事, 所以把骨架收敛到这里, 差异由调用方以函数注入。
"""
from datetime import datetime
from typing import Callable

from fastapi import Request, UploadFile
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.archive import save_import_images, split_import_archive
from app.services.log import write_operation_log

# 解析单个 md 文件: 返回计划项(调用方自定义字段), 内容不可用时返回 None
ParseFunc = Callable[[str, str], dict | None]
# 查重键 / 重复项提示文案: 都从计划项里取
PlanFunc = Callable[[dict], str]
# 落库一条计划项: 返回 (是否导入, 错误信息); 两者都是 False/None 表示计入跳过
CreateFunc = Callable[[dict, dict[str, str] | None], tuple[bool, str | None]]


def run_import(
    *,
    db: Session,
    user: User,
    request: Request,
    files: list[UploadFile],
    mode: str,
    on_duplicate: str,
    module: str,
    parse: ParseFunc,
    invalid_message: Callable[[str], str],
    existing_keys: Callable[[], set[str]],
    dedup_key: PlanFunc,
    label: PlanFunc,
    create: CreateFunc,
) -> tuple[dict, str]:
    """执行一次导入请求, 返回 (响应数据, 提示文案)。

    流程: 拆分上传文件 -> 逐个解析 -> 与库中已有内容及本批内容比对查重 ->
    (仅 check 模式到此为止) -> 按去重策略落库 -> 写操作日志。

    @param db 数据库会话
    @param user 发起导入的用户(新建记录的归属人)
    @param request 当前请求(写操作日志用)
    @param files 上传的 .md 或 .zip 文件
    @param mode check=只查重不写入, import=执行导入
    @param on_duplicate skip=重复项跳过, all=重复项一并导入
    @param module 操作日志的模块名(post / diary)
    @param parse (文件名, 内容) -> 计划项; 不可用时返回 None
    @param invalid_message 解析失败时拼错误提示的函数
    @param existing_keys 返回库中已有内容的查重键集合
    @param dedup_key 计划项 -> 查重键
    @param label 计划项 -> 重复提示文案
    @param create (计划项, 图片映射) -> (是否导入, 错误信息)
    @return (响应数据, 提示文案), 提示文案随 mode 变化
    """
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

    # 先整体解析一遍: 与库中已有内容、本批已出现的内容比对, 得出重复情况
    known_keys = existing_keys()
    plans: list[dict] = []
    for group_index, (_entries, md_files) in enumerate(groups):
        for fname, content in md_files:
            parsed = parse(fname, content)
            if parsed is None:
                errors.append(invalid_message(fname))
                continue
            key = dedup_key(parsed)
            duplicated = key in known_keys
            known_keys.add(key)
            plans.append({
                "group": group_index,
                "filename": fname,
                "duplicated": duplicated,
                **parsed,
            })

    duplicates = [label(plan) for plan in plans if plan["duplicated"]]
    if mode == "check":
        return {
            "total": len(plans),
            "duplicates_count": len(duplicates),
            "duplicates": duplicates[:50],
        }, "查重完成"

    image_maps: dict[int, dict[str, str]] = {}

    def image_map_of(group_index: int) -> dict[str, str]:
        """同一份压缩包内的多条内容共用一次图片落盘结果。"""
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
        created, err = create(plan, image_map_of(plan["group"]))
        if created:
            imported += 1
        elif err:
            errors.append(err)
        else:
            skipped += 1
    db.commit()
    write_operation_log(
        db, request=request, user=user, module=module, action="import",
        detail={"imported": imported, "skipped": skipped, "duplicates": len(duplicates)},
    )
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:20],
        "duplicates_count": len(duplicates),
    }, "导入完成"
