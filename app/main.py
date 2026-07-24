from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import Settings
from app.container import create_app_container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()  # type: ignore[call-arg]  # pydantic-settings loads required fields from env
    app.state.container = await create_app_container(settings)
    yield


app = FastAPI(lifespan=lifespan)
