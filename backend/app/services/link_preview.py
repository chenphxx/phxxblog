"""链接预览服务: 抓取网页标题/描述/封面图。"""
import re

import requests


def _extract_meta(html: str, pattern: str) -> str | None:
    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def fetch_link_preview(url: str) -> dict:
    """请求目标页面并提取 og 元信息, 失败时返回基础信息。"""
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text[:500_000]
        title = (
            _extract_meta(html, r'<meta\s+property="og:title"\s+content="([^"]*)"')
            or _extract_meta(html, r"<meta\s+property=\"og:title\"\s+content='([^']*)'")
            or _extract_meta(html, r"<title[^>]*>([^<]+)</title>")
            or ""
        )
        description = (
            _extract_meta(html, r'<meta\s+name="description"\s+content="([^"]*)"')
            or _extract_meta(html, r'<meta\s+property="og:description"\s+content="([^"]*)"')
            or ""
        )
        image = _extract_meta(html, r'<meta\s+property="og:image"\s+content="([^"]*)"')
        return {"url": url, "title": title, "description": description, "image": image}
    except Exception:
        return {"url": url, "title": "", "description": "", "image": None}
