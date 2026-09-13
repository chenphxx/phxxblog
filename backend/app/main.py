"""FastAPI 应用入口。"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.api.v1.rss import router as rss_router
from app.core.config import settings
from app.core.database import Base, check_schema, engine, ensure_schema_version_table
from app.core.middleware import restrict_docs_to_admin

# 项目根目录(backend/app/main.py -> 上两级为仓库根目录)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(
    title="phxxblog API",
    description="个人博客后端接口(账号/文章/评论/媒体/统计/日志/RSS/SEO)",
    version="0.1.0",
)

# 跨域(前后端分离开发)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 文档(/docs、/redoc、/openapi.json)仅 admin 角色可访问
app.middleware("http")(restrict_docs_to_admin)


@app.on_event("startup")
def on_startup() -> None:
    """启动时建表(幂等)并校验表结构。

    不再静默"补列": create_all 只建缺失的表, 不会改已有表结构。以前 ensure_columns
    只认 categories/tags 两列, 以后任何模型加列都不会补、也不报错, 直到某个查询
    才炸 "Unknown column" —— 排查成本高。现在改为启动即校验:
      - debug=True 时只告警(本地开发方便)
      - 否则直接拒绝启动, 并打印出需要执行的 ALTER 语句
    """
    Base.metadata.create_all(bind=engine)
    ensure_schema_version_table()
    check_schema(strict=not settings.debug)


# ---------- 统一异常处理 ----------


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """业务异常统一返回 { code, message, data }。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数校验失败返回第一条错误信息。"""
    errors = exc.errors()
    first = errors[0] if errors else {}
    loc = ".".join(str(part) for part in first.get("loc", []))
    message = f"{loc}: {first.get('msg', '参数错误')}" if loc else first.get("msg", "参数错误")
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": message, "data": None},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """兜底异常, 调试模式直接抛出以便排查。"""
    if settings.debug:
        raise exc
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


# ---------- 路由 ----------

app.include_router(api_router)
app.include_router(rss_router)

# 上传文件静态访问: /assets/...
app.mount(
    "/assets",
    StaticFiles(directory=PROJECT_ROOT / "assets"),
    name="assets",
)


@app.get("/", include_in_schema=False)
def root():
    """根路径提示。"""
    return {"message": "phxxblog API", "docs": "/docs"}
