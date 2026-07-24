from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.routes import router
from app.config.settings import Settings
from app.container import create_app_container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()  # type: ignore[call-arg]  # pydantic-settings loads required fields from env
    app.state.container = await create_app_container(settings)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.include_router(health_router)
