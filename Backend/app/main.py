from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app import models


def create_app() -> FastAPI:
    init_db()

    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)
    return app


app = create_app()
