"""导入用户提供的缺失图片(从 assets/wordpress/images/ 补全文章图片)。

用法:
    1. 将缺失的原图按文件名放入 assets/wordpress/images/
       (清单见 assets/wordpress/missing-images.md)
    2. python scripts/import_local_images.py
脚本会把图片复制到 assets/uploads/wordpress/<原相对路径>, 登记到媒体库,
并把文章正文中对应的旧站链接改写为本地地址。
"""
import glob
import mimetypes
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

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


def main() -> None:
    source_dir = PROJECT_ROOT / "assets" / "wordpress" / "images"
    if not source_dir.exists():
        print(f"请先创建目录并放入原图: {source_dir}")
        return

    xml_candidates = sorted(
        glob.glob(str(PROJECT_ROOT / "assets" / "wordpress" / "*.xml")),
        key=lambda p: Path(p).stat().st_size,
    )
    if not xml_candidates:
        print("未找到 WXR XML")
        return

    engine.echo = False
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    upload_root = PROJECT_ROOT / "assets" / "uploads" / "wordpress"
    imported = 0
    try:
        channel = ET.parse(xml_candidates[-1]).getroot().find("channel")
        for item in channel.findall("item"):
            if text(item, "wp:post_type") != "attachment":
                continue
            remote = text(item, "wp:attachment_url")
            match = re.search(r"/wp-content/uploads/(.+)$", remote)
            if not match:
                continue
            rel = match.group(1).replace("\\", "/")
            fname = rel.split("/")[-1]
            source = source_dir / fname
            if not source.exists():
                continue
            local_url = f"/assets/uploads/wordpress/{rel}"
            target = upload_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(source.read_bytes())
            if db.query(Media).filter(Media.url == local_url).first() is None:
                db.add(Media(
                    uploader_id=1,
                    original_name=fname,
                    filename=fname,
                    path=str(target).replace("\\", "/"),
                    url=local_url,
                    mime_type=mimetypes.guess_type(fname)[0],
                    size=target.stat().st_size,
                    type="image" if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"} else "file",
                ))
            for post in db.query(Post).all():
                if remote in (post.content_md or ""):
                    post.content_md = post.content_md.replace(remote, local_url)
                if remote in (post.content_html or ""):
                    post.content_html = post.content_html.replace(remote, local_url)
            db.commit()
            imported += 1
            print(f"[导入] {fname} -> {local_url}")
        print(f"\n完成: 导入 {imported} 个图片")
    finally:
        db.close()


if __name__ == "__main__":
    main()
