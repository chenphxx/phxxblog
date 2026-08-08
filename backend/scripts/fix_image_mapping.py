"""按上传日期与 zip 文件修改时间重新配对还原图片(修复错位)。

媒体库导出 zip 中重名文件(image.png / image-1.png ...)被导出工具改名,
文件自身的修改时间保留了上传月份, 用它和 WXR 附件上传日期匹配即可得到正确对应关系。
"""
import glob
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.media import Media  # noqa: E402

NS = {"wp": "http://wordpress.org/export/1.2/"}


def text(elem, tag):
    node = elem.find(tag, NS)
    return (node.text or "").strip() if node is not None and node.text else ""


def candidate_name(base: str, occurrence: int) -> str | None:
    if occurrence == 0:
        return base
    if base == "image.png":
        return f"image{occurrence - 1}.png"
    match = re.match(r"^(image-\d+)(\.[a-zA-Z0-9]+)$", base)
    if match:
        return f"{match.group(1)}{occurrence - 1}{match.group(2)}"
    return None


def main() -> None:
    zips = glob.glob(str(PROJECT_ROOT / "assets" / "wordpress" / "media_library_export-*.zip"))
    xmls = sorted(
        glob.glob(str(PROJECT_ROOT / "assets" / "wordpress" / "*.xml")),
        key=lambda p: Path(p).stat().st_size,
    )
    if not zips or not xmls:
        print("缺少 zip 或 XML")
        return

    archive = zipfile.ZipFile(zips[0])
    mtime_by_name = {}
    for info in archive.infolist():
        if not info.filename.endswith("/"):
            mtime_by_name[Path(info.filename).name] = (
                f"{info.date_time[0]:04d}-{info.date_time[1]:02d}"
            )

    engine.echo = False
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    upload_root = PROJECT_ROOT / "assets" / "uploads" / "wordpress"
    changed = 0
    try:
        channel = ET.parse(str(xmls[-1])).getroot().find("channel")
        attachments = []
        for item in channel.findall("item"):
            if text(item, "wp:post_type") != "attachment":
                continue
            remote = text(item, "wp:attachment_url")
            match = re.search(r"/wp-content/uploads/(.+)$", remote)
            if match:
                rel = unquote(match.group(1)).replace("\\", "/")
                attachments.append({
                    "rel": rel,
                    "date": (text(item, "wp:post_date") or "")[:7],
                })

        # 分组: 同名多次出现才需要重配对
        from collections import defaultdict

        groups: dict[str, list[dict]] = defaultdict(list)
        for att in attachments:
            groups[att["rel"].split("/")[-1]].append(att)

        for base, items in groups.items():
            if len(items) <= 1:
                continue
            candidates = []
            for idx in range(len(items)):
                name = candidate_name(base, idx)
                if name and name in mtime_by_name:
                    candidates.append({"name": name, "mtime": mtime_by_name[name]})
            if not candidates:
                continue
            for att in items:
                # 优先: 修改时间月份 == 上传月份
                pick = next((c for c in candidates if c["mtime"] == att["date"]), None)
                if pick is None:
                    # 退而求其次: 月份差最小
                    if not candidates:
                        print(f"  [跳过] 无候选可配: {att['rel']} (上传 {att['date']})")
                        continue
                    pick = min(
                        candidates,
                        key=lambda c: abs(
                            (int(c["mtime"][:4]) * 12 + int(c["mtime"][5:7]))
                            - (int(att["date"][:4]) * 12 + int(att["date"][5:7]))
                        ),
                    )
                candidates.remove(pick)
                target = upload_root / att["rel"]
                new_bytes = archive.read(f"{Path(zips[0]).stem}/{pick['name']}")
                if target.exists() and target.read_bytes() == new_bytes:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(new_bytes)
                media = db.query(Media).filter(Media.url == f"/assets/uploads/wordpress/{att['rel']}").first()
                if media:
                    media.size = target.stat().st_size
                changed += 1
                print(f"修正: {att['rel']} <- {pick['name']} (mtime {pick['mtime']}, 上传 {att['date']})")
        db.commit()
        print(f"\n完成: 修正 {changed} 个文件")
    finally:
        db.close()


if __name__ == "__main__":
    main()
