"""尝试从 Wayback Machine 归档恢复 WordPress 缺失的附件。

部分附件在旧站已返回 404, 本脚本查询 web.archive.org
的 CDX 索引, 若存在归档快照则下载到 assets/uploads/wordpress/,
登记到媒体库并改写文章正文中的旧站链接。

用法:
    python scripts/restore_attachments.py [--xml 所有内容.xml]
"""
import argparse
import glob
import mimetypes
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.media import Media  # noqa: E402
from app.models.post import Post  # noqa: E402

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def text(elem, tag):
    node = elem.find(tag, NS)
    return (node.text or "").strip() if node is not None and node.text else ""


def cdx_lookup(url: str) -> str | None:
    """返回最早可用的 200 归档快照 URL, 无则返回 None。"""
    cdx = "https://web.archive.org/cdx/search/cdx"
    params = {
        "url": url,
        "output": "json",
        "limit": "5",
        "filter": "statuscode:200",
        "collapse": "digest",
    }
    try:
        resp = requests.get(cdx, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
        if len(rows) > 1:
            # 优先选择图片 mime
            rows = sorted(rows[1:], key=lambda r: 0 if (r[3] or "").startswith("image/") else 1)
            ts, original = rows[0][1], rows[0][2]
            return f"https://web.archive.org/web/{ts}id_/{original}"
    except Exception as exc:
        print(f"  [CDX失败] {url}: {exc}")
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", default="")
    args = parser.parse_args()

    if args.xml:
        xml_path = Path(args.xml)
    else:
        candidates = sorted(
            glob.glob(str(PROJECT_ROOT / "assets" / "wordpress" / "*.xml")),
            key=lambda p: Path(p).stat().st_size,
        )
        if not candidates:
            print("未找到 WXR XML")
            return
        xml_path = Path(candidates[-1])

    engine.echo = False
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    upload_root = PROJECT_ROOT / "assets" / "uploads" / "wordpress"
    restored = 0
    missing = 0
    try:
        channel = ET.parse(str(xml_path)).getroot().find("channel")
        for item in channel.findall("item"):
            if text(item, "wp:post_type") != "attachment":
                continue
            remote = text(item, "wp:attachment_url")
            match = re.search(r"/wp-content/uploads/(.+)$", remote)
            if not match:
                continue
            rel = match.group(1).replace("\\", "/")
            local_url = f"/assets/uploads/wordpress/{rel}"
            target = upload_root / rel
            if target.exists() or db.query(Media).filter(Media.url == local_url).first():
                continue  # 已有
            print(f"尝试恢复: {remote}")
            snapshot = cdx_lookup(remote)
            if snapshot is None:
                missing += 1
                print(f"  [无归档] {remote}")
                time.sleep(0.3)
                continue
            try:
                resp = requests.get(snapshot, timeout=60)
                resp.raise_for_status()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(resp.content)
            except Exception as exc:
                missing += 1
                print(f"  [下载失败] {snapshot}: {exc}")
                time.sleep(0.3)
                continue
            db.add(Media(
                uploader_id=1,
                original_name=target.name,
                filename=target.name,
                path=str(target).replace("\\", "/"),
                url=local_url,
                mime_type=mimetypes.guess_type(target.name)[0],
                size=target.stat().st_size,
                type="image" if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"} else "file",
            ))
            # 改写文章正文中的旧站链接
            posts = db.query(Post).all()
            for post in posts:
                if remote in (post.content_md or ""):
                    post.content_md = post.content_md.replace(remote, local_url)
                if remote in (post.content_html or ""):
                    post.content_html = post.content_html.replace(remote, local_url)
            db.commit()
            restored += 1
            print(f"  [恢复成功] {rel}")
            time.sleep(0.3)
        print(f"\n完成: 恢复 {restored} 个, 仍缺失 {missing} 个")
    finally:
        db.close()


if __name__ == "__main__":
    main()
