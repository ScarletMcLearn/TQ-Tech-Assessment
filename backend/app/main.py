from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.routes.notifications import router
from app.services.scheduler import PollingScheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_db()
    scheduler = PollingScheduler(settings=settings, session_factory=SessionLocal)
    app.state.scheduler = scheduler
    await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


settings = get_settings()
app = FastAPI(title="AI Email Reading Agent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
