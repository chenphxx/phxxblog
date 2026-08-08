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
from app.core.database import Base, engine

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


@app.on_event("startup")
def on_startup() -> None:
    """启动时自动建表(幂等), 正式环境可改用 Alembic 迁移。"""
    Base.metadata.create_all(bind=engine)


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
