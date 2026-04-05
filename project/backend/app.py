# backend/app.py

from __future__ import annotations

from fastapi import FastAPI

from app.config import AppConfig
from backend.routes import router
from core.motion_registry import MotionRegistry


def create_app() -> FastAPI:
    """
    创建后端应用实例。
    """
    config = AppConfig()
    config.validate()

    motion_registry = MotionRegistry(config.motions_dir)
    motion_registry.load_all()

    app = FastAPI(
        title="Sports Analysis Force Line Backend",
        version="1.0.0",
        description="企业第一版运动力线分析后端接口",
    )

    app.state.config = config
    app.state.motion_registry = motion_registry

    app.include_router(router)

    return app


app = create_app()