"""从媒体库导出压缩包还原图片到文章。

旧站媒体库导出(media_library_export-*.zip)包含全部附件文件,
本脚本按 WXR 导出清单将文件还原到 assets/uploads/wordpress/<原相对路径>,
登记到媒体库并改写文章正文中的旧站链接。

用法:
    python scripts/restore_from_zip.py [--zip 压缩包路径]
"""
import argparse
import glob
import mimetypes
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.media import Media  # noqa: E402
from app.models.post import Post  # noqa: E402

NS = {"wp": "http://wordpress.org/export/1.2/"}


def text(elem, tag):
    node = elem.find(tag, NS)
    return (node.text or "").strip() if node is not None and node.text else ""


def candidate_name(basename: str, occurrence: int) -> str | None:
    """媒体库导出会重命名重名文件: image.png -> image0.png; image-1.png -> image-10.png ..."""
    if occurrence == 0:
        return basename
    if basename == "image.png":
        return f"image{occurrence - 1}.png"
    match = re.match(r"^(image-\d+)(\.[a-zA-Z0-9]+)$", basename)
    if match:
        return f"{match.group(1)}{occurrence - 1}{match.group(2)}"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", default="")
    args = parser.parse_args()

    if args.zip:
        zip_path = Path(args.zip)
    else:
        candidates = glob.glob(str(PROJECT_ROOT / "assets" / "wordpress" / "media_library_export-*.zip"))
        if not candidates:
            print("未找到媒体库导出压缩包")
            return
        zip_path = Path(candidates[0])
    print("压缩包:", zip_path.name)

    xml_candidates = sorted(
        glob.glob(str(PROJECT_ROOT / "assets" / "wordpress" / "*.xml")),
        key=lambda p: Path(p).stat().st_size,
    )
    if not xml_candidates:
        print("未找到 WXR XML")
        return

    archive = zipfile.ZipFile(str(zip_path))
    # zip 内文件名(扁平化后的 basename 唯一)
    zip_files = {Path(name).name: name for name in archive.namelist() if not name.endswith("/")}

    engine.echo = False
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    upload_root = PROJECT_ROOT / "assets" / "uploads" / "wordpress"
    restored = 0
    failed = []
    url_map: dict[str, str] = {}
    used_filenames: set[str] = set()
    try:
        channel = ET.parse(str(xml_candidates[-1])).getroot().find("channel")
        attachments = []
        for item in channel.findall("item"):
            if text(item, "wp:post_type") != "attachment":
                continue
            remote = text(item, "wp:attachment_url")
            match = re.search(r"/wp-content/uploads/(.+)$", remote)
            if match:
                attachments.append((remote, unquote(match.group(1)).replace("\\", "/")))

        occurrence: dict[str, int] = defaultdict(int)
        for remote, rel in attachments:
            basename = rel.split("/")[-1]
            target = upload_root / rel
            if db.query(Media).filter(Media.url == f"/assets/uploads/wordpress/{rel}").first():
                continue  # 已还原
            idx = occurrence[basename]
            occurrence[basename] += 1
            entry_name = zip_files.get(candidate_name(basename, idx))
            if entry_name is None:
                failed.append(rel)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(entry_name))
            local_url = f"/assets/uploads/wordpress/{rel}"
            # 媒体库 filename 唯一(同名文件用父目录前缀区分)
            filename = target.name
            if filename in used_filenames or db.query(Media).filter(Media.filename == filename).first():
                filename = rel.replace("/", "_")
            used_filenames.add(filename)
            db.add(Media(
                uploader_id=1,
                original_name=target.name,
                filename=filename,
                path=str(target).replace("\\", "/"),
                url=local_url,
                mime_type=mimetypes.guess_type(target.name)[0],
                size=target.stat().st_size,
                type="image" if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"} else "file",
            ))
            url_map[remote] = local_url
            url_map[unquote(remote)] = local_url
            restored += 1
        db.commit()

        # 改写文章正文(同时替换原始 URL 与解码后的 URL)
        posts = db.query(Post).all()
        rewritten = 0
        for post in posts:
            changed = False
            for remote, local in url_map.items():
                for field in ("content_md", "content_html"):
                    value = getattr(post, field) or ""
                    if remote in value:
                        setattr(post, field, value.replace(remote, local))
                        changed = True
            if changed:
                rewritten += 1
        db.commit()
        print(f"\n完成: 还原图片 {restored} 个, 改写文章 {rewritten} 篇")
        if failed:
            print("未能匹配的附件:")
            for rel in failed:
                print("  ", rel)
    finally:
        db.close()


if __name__ == "__main__":
    main()
