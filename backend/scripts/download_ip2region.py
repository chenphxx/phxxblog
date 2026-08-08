"""下载 ip2region 离线 IP 库(backend/data/ip2region_v4.xdb)。

数据来源: ip2region 官方仓库(lionsoul2014/ip2region)。
"""
from pathlib import Path

import requests

XDB_URL = "https://raw.githubusercontent.com/lionsoul2014/ip2region/master/data/ip2region_v4.xdb"
TARGET = Path(__file__).resolve().parents[1] / "data" / "ip2region_v4.xdb"


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    print(f"下载 {XDB_URL} -> {TARGET}")
    resp = requests.get(XDB_URL, timeout=300)
    resp.raise_for_status()
    TARGET.write_bytes(resp.content)
    print(f"完成, 共 {len(resp.content)} 字节")


if __name__ == "__main__":
    main()
