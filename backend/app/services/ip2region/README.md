# ip2region 绑定（vendored）

本目录下的 `searcher.py`、`util.py`、`__init__.py` 是 **ip2region 官方 Python 绑定的原样拷贝**，
不是本项目自研代码。

## 为什么用拷贝而不是 pip 依赖

ip2region 官方推荐的使用方式就是拷贝 `binding/python/xdb` 目录：该项目**没有发布维护良好的
PyPI 包**（PyPI 上的同名包是第三方重新打包、API 不兼容且长期未更新）。因此 vendoring 是正解，
不要改成 `pip install ip2region`。

## 来源与版本

| 项 | 值 |
| --- | --- |
| 上游仓库 | https://github.com/lionsoul2014/ip2region |
| 绑定目录 | `binding/python/xdb` |
| 文件内标注的日期 | searcher `# xdb searcher on 2025/10/30`、util `# xdb utils on 2025/10/29` |
| 拷贝时间 | 2026-09（随本项目一起 vendored） |
| 许可 | Apache-2.0，全文见同目录 `LICENSE` |

## 数据文件

`searcher.py` / `util.py` 只负责读取 xdb 数据；数据文件**不在仓库里**
（`backend/data/ip2region_v4.xdb`，约 11 MB，已被 `.gitignore` 排除），
由 `backend/scripts/download_ip2region.py` 下载。

## 维护提示

- 上游更新后，直接覆盖这三个 .py 文件即可；注意上游偶尔会调整 xdb 格式，
  覆盖后请跑一次 `python -c "from app.services.geo import lookup; print(lookup('1.1.1.1'))"` 验证。
- `scripts/download_ip2region.py` 目前从 `master` 分支 raw 链接下载数据文件，
  若上游改动目录结构会静默失效；建议固定到一个 tag。
