"""v1 路由汇总。"""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    categories,
    comments,
    dashboard,
    diaries,
    links,
    logs,
    media,
    misc,
    posts,
    search,
    settings,
    stats,
    tags,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(posts.router)
api_router.include_router(categories.router)
api_router.include_router(tags.router)
api_router.include_router(comments.router)
api_router.include_router(media.router)
api_router.include_router(diaries.router)
api_router.include_router(misc.router)
api_router.include_router(stats.router)
api_router.include_router(logs.router)
api_router.include_router(settings.router)
api_router.include_router(search.router)
api_router.include_router(dashboard.router)
api_router.include_router(links.router)
