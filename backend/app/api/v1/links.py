"""链接预览接口(嵌入链接时预览网页内容)。"""
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query

from app.core.response import ok
from app.services.link_preview import fetch_link_preview

router = APIRouter(prefix="/links", tags=["链接预览"])


@router.get("/preview", response_model=dict)
def link_preview(url: str = Query(..., description="要预览的网页地址")):
    """抓取网页 og 信息用于链接卡片预览。"""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="仅支持 http/https 链接")
    return ok(fetch_link_preview(url))
