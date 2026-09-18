"""应用配置。

通过 pydantic-settings 从环境变量 / .env 文件加载配置。
"""

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 仓库根目录(backend/app/core/config.py -> 上三级)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 仓库里公开的占位密钥。用它签名 JWT 等于没有签名 —— 任何人都能离线伪造 admin 令牌。
DEFAULT_SECRET_KEY = "change-me-to-a-random-secret-key"
# 密钥最小长度(HS256 建议至少 32 字节熵)
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """全局配置项。"""

    # 应用信息
    app_name: str = "phxxblog-api"
    # 默认关闭: 开启时会把每条 SQL 打进 stdout(含注册/登录的 INSERT),
    # 并且 main.py 会把未捕获异常原样抛给 ASGI server。本地按需在 .env 里打开。
    debug: bool = False

    # 数据库连接(默认使用 PyMySQL 驱动)
    database_url: str = "mysql+pymysql://root:password@localhost:3306/phxxblog?charset=utf8mb4"

    # JWT 配置
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 是否开放注册。个人博客默认关闭, 否则任意访客都能注册成 author 并上传文件。
    allow_register: bool = False

    # 可信反向代理 IP(逗号分隔)。仅当请求来自这些地址时才采信 X-Forwarded-For。
    # 留空表示不信任任何 XFF, 一律用 TCP 直连地址。
    trusted_proxies: str = ""

    # 跨域来源(前端开发服务器)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 上传目录(默认指向仓库根目录的 assets/uploads, 与 .env 可覆盖)
    upload_dir: str = str(PROJECT_ROOT / "assets" / "uploads")

    # 离线 IP 归属地数据库(ip2region xdb 文件)
    geo_db_path: str = str(PROJECT_ROOT / "backend" / "data" / "ip2region_v4.xdb")
    max_upload_size: int = 100 * 1024 * 1024  # 100MB

    # 站点地址(用于 RSS / sitemap 生成绝对链接)
    site_url: str = "http://localhost:5173"

    # 数据保留天数(天)。超出后由 scripts/cleanup_old_data.py 清理:
    #   - visit_logs: 访问明细。趋势图读的是 daily_stats(按日聚合, 永久保留),
    #     所以清理明细不会影响趋势; 但"访问来源/浏览器/设备"分布会变成近 N 天。
    #   - refresh_tokens: 已吊销或已过期的令牌记录。
    #   - operation_logs: 操作日志(审计用途, 默认保留更久)。
    data_retention_days: int = 180
    audit_log_retention_days: int = 365

    model_config = SettingsConfigDict(
        env_prefix="PHXXBLOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _reject_unsafe_secret_key(self) -> "Settings":
        """拒绝用占位密钥启动。

        忘记创建 .env 时, 以前会用仓库里公开的 DEFAULT_SECRET_KEY 签名 JWT,
        且不会有任何提示 —— 攻击者可离线伪造任意用户(含 admin)的访问令牌。
        这里直接拒绝启动, 让问题在部署时暴露, 而不是被静默利用。
        """
        key = (self.secret_key or "").strip()
        if key == DEFAULT_SECRET_KEY:
            raise ValueError(
                "PHXXBLOG_SECRET_KEY 仍是仓库里的默认占位值, 拒绝启动。\n"
                "  请生成一个随机密钥写入 backend/.env, 例如:\n"
                "    python -c \"import secrets; print('PHXXBLOG_SECRET_KEY=' + secrets.token_urlsafe(48))\""
            )
        if len(key) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"PHXXBLOG_SECRET_KEY 长度 {len(key)} 过短, 至少需要 {MIN_SECRET_KEY_LENGTH} 个字符。\n"
                "  生成方式: python -c \"import secrets; print('PHXXBLOG_SECRET_KEY=' + secrets.token_urlsafe(48))\""
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        """解析逗号分隔的跨域来源列表。"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_proxy_list(self) -> list[str]:
        """解析逗号分隔的可信代理列表。"""
        return [ip.strip() for ip in self.trusted_proxies.split(",") if ip.strip()]


@lru_cache
def get_settings() -> Settings:
    """获取单例配置。"""
    return Settings()


settings = get_settings()
