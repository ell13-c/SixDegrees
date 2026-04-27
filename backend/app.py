"""SixDegrees FastAPI application entry point.

Registers all routers and starts the APScheduler daily pipeline job via a
FastAPI lifespan context manager.

Single-worker constraint: always run with ``uvicorn app:app --reload``.
Multi-worker mode causes APScheduler to fire N times per trigger.
See ``services.map.scheduler`` for details.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.map import router as map_router
from routes.interactions import router as interactions_router
from routes.profile import router as profile_router
from routes.match import router as match_router
from services.map.scheduler import setup_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context: start APScheduler on startup, shut it down on exit."""
    scheduler = setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174")
origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(map_router)
app.include_router(interactions_router)
app.include_router(profile_router)
app.include_router(match_router)
