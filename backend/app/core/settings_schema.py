"""系统设置的键与默认值(后端唯一定义处)

本文件只保留两类键:
  - 站点身份: 站点名/标题/描述/图标/头像/简介 - 布局层与多个模块都要读, 是共享输入
  - 平台约束: 单文件上传上限 - 全站所有上传入口共用同一个限制
某个能力的配置(内容与开关)归它自己的模块, 见 app/modules/<模块 id>/spec.py 的 settings,
在 settings 表里以 module.<模块 id>.<配置键> 存放(见 app/modules/base.py)

为什么单独抽一个模块:
    同一份默认值以前写在两处 - seed.py 的 DEFAULT_SETTINGS(带描述, 初始化数据库用)
    与 api/v1/settings.py 的 DEFAULTS(库里缺行时兜底) - 并且已经漂移过:
    同一种列表型设置在两处的元素个数与格式都不一样, 而 /settings/public 会把逗号串
    兜底解析成数组, 所以这个差异在界面上完全看不出来
    现在默认值只有这一份, 初始化脚本与路由都从这里取

    PUBLIC_KEYS 与 BOOL_KEYS 仍然显式列出, 不从默认值反推:
      - PUBLIC_KEYS 决定哪些键对前台公开, 属于安全边界, 必须逐个显式增删
      - BOOL_KEYS 无法可靠推断("默认值是 1" 不等于"这是个布尔开关")
      - ADMIN_ONLY_KEYS 是只在后台可编辑、不向前台公开的键, 同样显式列出

前端的对应契约在 frontend/src/types/index.ts 的 PublicSettings;
两侧是否一致由 scripts/check_settings_keys.py 校验(已挂进 verify_all.py)
"""

# 单文件上传上限的设置键(值以 MB 为单位)与可配置范围
UPLOAD_SIZE_KEY = "max_upload_size_mb"
MIN_UPLOAD_SIZE_MB = 1
MAX_UPLOAD_SIZE_MB = 2048

# 键 -> (默认值, 说明); 说明会在初始化数据库时写入 settings.description
DEFAULT_SETTINGS: dict[str, tuple[str, str]] = {
    "site_name": ("phxxblog", "站点名称"),
    "site_title": ("", "浏览器标签页名称(留空用站点名称)"),
    "site_desc": ("记录技术成长与生活点滴的个人博客", "站点描述"),
    "site_icon": ("", "站点图标URL"),
    "site_avatar": ("", "首页头像URL"),
    "site_bio": ("一个热爱编程的开发者", "首页个人简介"),
}

# 键 -> 默认值(不带说明), 供路由在库里缺行时兜底
DEFAULTS: dict[str, str] = {key: value for key, (value, _desc) in DEFAULT_SETTINGS.items()}

# 前台公开的配置键(其余键只在后台可读, 见 api/v1/settings.py)
PUBLIC_KEYS = [
    "site_name",
    "site_title",
    "site_desc",
    "site_icon",
    "site_avatar",
    "site_bio",
]

# 只在后台可编辑、不向前台公开的配置键(需要出现在后台表单里)
# 这些键不写入 DEFAULT_SETTINGS/seed: 它们的默认值来自环境变量等运行时配置
# (如上传上限跟随 PHXXBLOG_MAX_UPLOAD_SIZE), 一旦被 seed 写库就会反过来覆盖环境变量
ADMIN_ONLY_KEYS = [
    UPLOAD_SIZE_KEY,
]

# 布尔型开关: 1/true/yes/on 视为开启
# 站点级设置里已没有布尔开关(首页各区块的展示开关随各自模块走), 留空是刻意的:
# 路由仍按这份名单把值转成 true/false, 以后新增站点级开关时在这里加上即可
BOOL_KEYS: tuple[str, ...] = ()


def parse_upload_size_mb(raw: object) -> int | None:
    """把一个设置值解析成单文件上传上限(MB)

    @param raw 设置值(数据库中按字符串存储)
    @return 合法时返回 MB 数, 非法或超出可配置范围时返回 None
    """
    text = str(raw if raw is not None else "").strip()
    if not text.isdigit():
        return None
    value = int(text)
    if value < MIN_UPLOAD_SIZE_MB or value > MAX_UPLOAD_SIZE_MB:
        return None
    return value


def format_upload_size_mb(size_bytes: int) -> int:
    """把字节数换算成表单/设置值使用的整数 MB

    @param size_bytes 字节数
    @return 换算后的整数 MB(不小于 MIN_UPLOAD_SIZE_MB)
    """
    return max(MIN_UPLOAD_SIZE_MB, size_bytes // (1024 * 1024))
