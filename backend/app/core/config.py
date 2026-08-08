"""应用配置。

通过 pydantic-settings 从环境变量 / .env 文件加载配置。
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 仓库根目录(backend/app/core/config.py -> 上三级)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """全局配置项。"""

    # 应用信息
    app_name: str = "phxxblog-api"
    debug: bool = True

    # 数据库连接(默认使用 PyMySQL 驱动)
    database_url: str = (
        "mysql+pymysql://root:password@localhost:3306/phxxblog?charset=utf8mb4"
    )

    # JWT 配置
    secret_key: str = "change-me-to-a-random-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 跨域来源(前端开发服务器)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 上传目录(默认指向仓库根目录的 assets/uploads, 与 .env 可覆盖)
    upload_dir: str = str(PROJECT_ROOT / "assets" / "uploads")

    # 离线 IP 归属地数据库(ip2region xdb 文件)
    geo_db_path: str = str(PROJECT_ROOT / "backend" / "data" / "ip2region_v4.xdb")
    max_upload_size: int = 100 * 1024 * 1024  # 100MB

    # 站点地址(用于 RSS / sitemap 生成绝对链接)
    site_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_prefix="PHXXBLOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """解析逗号分隔的跨域来源列表。"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """获取单例配置。"""
    return Settings()


settings = get_settings()
