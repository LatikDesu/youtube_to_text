from contextlib import asynccontextmanager
from logging.config import dictConfig

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.dependencies import http_client
from server.logger import LogConfig
from server.routers import api

dictConfig(LogConfig().dict())


@asynccontextmanager
async def _lifespan(_: FastAPI):
    http_client.start()
    yield
    await http_client.stop()


app = FastAPI(
    title="Youtube to article API",
    description="Automatic creation of a text publication based on a youtube video.",
    contact={"name": "Крафтовый код",
             "url": "https://github.com/LatikDesu/youtube_to_text.git"},
    version="0.1.0",
    docs_url="/documentation",
    redoc_url=None,
    lifespan=_lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
