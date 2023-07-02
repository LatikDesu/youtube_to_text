from logging import getLogger
from logging.config import dictConfig

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.logger import LogConfig

dictConfig(LogConfig().dict())
logger = getLogger("YtoArticle")

app = FastAPI(
    title="Youtube to article API",
    description="Automatic creation of a text publication based on a youtube video.",
    contact={"name": "Крафтовый код",
             "url": "https://github.com/Hacaton"},
    version="0.1.0",
    docs_url="/documentation",
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
