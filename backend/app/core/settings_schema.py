"""系统设置的键与默认值(后端唯一定义处)。

为什么单独抽一个模块:
    同一份默认值以前写在两处 —— seed.py 的 DEFAULT_SETTINGS(带描述, 初始化数据库用)
    与 api/v1/settings.py 的 DEFAULTS(库里缺行时兜底) —— 并且已经漂移过:
    tech_tags 在 seed 里是 ["Python", "Vue", "FastAPI", "MySQL"], 在兜底里是
    "Python, Vue, FastAPI"(个数与格式都不一样), 而 /settings/public 会把逗号串
    兜底解析成数组, 所以这个差异在界面上完全看不出来。
    现在默认值只有这一份, 初始化脚本与路由都从这里取, 新增设置项时后端只需改本文件。

    PUBLIC_KEYS 与 BOOL_KEYS 仍然显式列出, 不从默认值反推:
      - PUBLIC_KEYS 决定哪些键对前台公开, 属于安全边界, 必须逐个显式增删
      - BOOL_KEYS 无法可靠推断("默认值是 1" 不等于"这是个布尔开关")

前端的对应契约在 frontend/src/types/index.ts 的 PublicSettings;
两侧是否一致由 scripts/check_settings_keys.py 校验(已挂进 verify_all.py)。
"""
# 键 -> (默认值, 说明); 说明会在初始化数据库时写入 settings.description
DEFAULT_SETTINGS: dict[str, tuple[str, str]] = {
    "site_name": ("phxxblog", "站点名称"),
    "site_title": ("", "浏览器标签页名称(留空用站点名称)"),
    "site_desc": ("记录技术成长与生活点滴的个人博客", "站点描述"),
    "site_keywords": ("blog, 技术, 分享", "SEO 关键词"),
    "site_icon": ("", "站点图标URL"),
    "site_avatar": ("", "首页头像URL"),
    "site_bio": ("一个热爱编程的开发者", "首页个人简介"),
    "site_readme": ("", "主页 README(Markdown)"),
    "show_readme": ("1", "首页是否展示 README 模块(1=展示, 0=隐藏)"),
    "show_contributions": ("1", "首页是否展示文章发布记录(1=展示, 0=隐藏)"),
    "show_history": ("1", "首页是否展示程序员历史上的今天(1=展示, 0=隐藏)"),
    "show_session": ("1", "首页是否展示 session 终端卡片(1=展示, 0=隐藏)"),
    "show_kanbanniang": ("1", "全站是否展示看板娘(1=展示, 0=隐藏)"),
    "footer_text": ("© {year} {site_name} · Vue3 + FastAPI", "页脚版权信息(支持 {year}/{site_name} 占位符, 留空则不显示)"),
    "tech_tags": ('["Python", "Vue", "FastAPI", "MySQL"]', "首页技术标签(JSON数组)"),
    "social_links": ('[{"name": "GitHub", "url": "https://github.com/chenphxx"}]', "社交账号链接(JSON数组)"),
    "website_links": ("[]", "网站链接(JSON数组)"),
    "beian_info": ("[]", "网站备案信息(JSON数组, 元素含 name/url/icon)"),
}

# 键 -> 默认值(不带说明), 供路由在库里缺行时兜底
DEFAULTS: dict[str, str] = {key: value for key, (value, _desc) in DEFAULT_SETTINGS.items()}

# 前台公开的配置键(其余键只在后台可读, 见 api/v1/settings.py)
PUBLIC_KEYS = [
    "site_name",
    "site_title",
    "site_desc",
    "site_keywords",
    "site_icon",
    "site_avatar",
    "site_bio",
    "site_readme",
    "tech_tags",
    "social_links",
    "website_links",
    "beian_info",
    "show_readme",
    "show_contributions",
    "show_history",
    "show_session",
    "show_kanbanniang",
    "footer_text",
]

# 布尔型开关: 1/true/yes/on 视为开启
BOOL_KEYS = ("show_readme", "show_contributions", "show_history", "show_session", "show_kanbanniang")
