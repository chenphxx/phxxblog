"""IP 归属地查询服务(离线 ip2region)。

数据文件: backend/data/ip2region_v4.xdb, 可用
`python scripts/download_ip2region.py` 下载; 缺失时优雅降级为空字符串。
"""
from functools import lru_cache
from pathlib import Path

from app.core.config import settings

_searcher = None


def _get_searcher():
    """懒加载 xdb 检索器(整库载入内存, 查询最快)。"""
    global _searcher
    if _searcher is not None:
        return _searcher
    db = Path(settings.geo_db_path)
    if not db.exists():
        return None
    import io

    from app.services.ip2region import searcher as xdb
    from app.services.ip2region import util

    handle = io.open(db, "rb")
    try:
        util.verify(handle)
        version = util.version_from_header(util.load_header(handle))
        if version is None:
            return None
        _searcher = xdb.new_with_buffer(version, util.load_content(handle))
    finally:
        handle.close()
    return _searcher


def format_region(region: str) -> str:
    """把 ip2region 返回的原始串格式化为 省市区 文案。

    原始格式: 国家|省份|城市|ISP|国家代码, 如:
      "中国|江苏省|南京市|0|CN"      -> "江苏省南京市"
      "中国|北京|北京市|腾讯|CN"      -> "北京市"
      "United States|California|0|Google LLC|US" -> "美国加利福尼亚"
      "Reserved|Reserved|Reserved|0|0" -> "内网IP"
    """
    if not region:
        return ""
    parts = region.split("|")
    if len(parts) < 3:
        return region
    country, province, city = parts[0], parts[1], parts[2]

    def clean(value: str) -> str:
        return "" if value in ("0", "Reserved", "") else value

    # 内网/保留地址
    if country in ("Reserved", "0", "内网IP") and clean(province) == "":
        return "内网IP"

    if country == "中国":
        p, c = clean(province), clean(city)
        if not p and not c:
            return "中国"
        if not c:
            return p
        if not p:
            return c
        # 直辖市: "北京|北京市" 归一为 "北京市"
        if c == p + "市" or c == p:
            return c
        return p + c

    # 国外: 拼接国家/省/市, 跳过缺失段
    segments = [clean(country), clean(province), clean(city)]
    segments = [s for s in segments if s]
    if segments and segments[0].isascii():
        # 英文国家名之间用空格分隔, 中文/日文等直接拼接
        return " ".join(segments)
    return "".join(segments) if segments else "未知地区"


@lru_cache(maxsize=4096)
def resolve_location(ip: str) -> str:
    """根据 IP 查询归属地, 返回省市区文案(失败返回空串)。"""
    if not ip:
        return ""
    searcher = _get_searcher()
    if searcher is None:
        return ""
    try:
        from app.services.ip2region import util

        region = searcher.search(util.parse_ip(ip))
    except Exception:
        return ""
    return format_region(region)
