"""User-Agent 解析(轻量正则实现)。"""
import re


def parse_user_agent(user_agent: str | None) -> dict:
    """从 UA 字符串解析浏览器/操作系统/设备类型。"""
    ua = user_agent or ""
    ua_lower = ua.lower()

    # 设备
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        device = "mobile"
    elif "ipad" in ua_lower or "tablet" in ua_lower:
        device = "tablet"
    else:
        device = "desktop"

    # 操作系统
    if "windows" in ua_lower:
        os_name = "Windows"
    elif "mac os" in ua_lower or "macintosh" in ua_lower:
        os_name = "macOS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower or "ios" in ua_lower:
        os_name = "iOS"
    elif "linux" in ua_lower:
        os_name = "Linux"
    else:
        os_name = "Unknown"

    # 浏览器
    browser = "Unknown"
    patterns = [
        (r"edg(?:e|a)?/([\d.]+)", "Edge"),
        (r"opr/([\d.]+)", "Opera"),
        (r"chrome/([\d.]+)", "Chrome"),
        (r"firefox/([\d.]+)", "Firefox"),
        (r"version/([\d.]+).*safari", "Safari"),
    ]
    for pattern, name in patterns:
        match = re.search(pattern, ua_lower)
        if match:
            browser = name
            break

    return {"browser": browser, "os": os_name, "device": device}
