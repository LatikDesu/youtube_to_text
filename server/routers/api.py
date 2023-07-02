from aiohttp import ClientSession
from fastapi import APIRouter, Depends

from server.dependencies import http_client
from server.schemas import ArticleRequest

router = APIRouter(prefix="/api/v1")


@router.post("/article/",
             tags=['article'],
             description="Automatic creation of a text publication based on a youtube video url.")
# response_model=Article)
def create_article(article_request: ArticleRequest,
                   session: ClientSession = Depends(http_client)):
    pass
