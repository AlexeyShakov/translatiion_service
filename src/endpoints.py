from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db_connection import get_async_session
from shemas import NewsSchema
from utils import NewsHandler

router = APIRouter()


@router.post("/traslate_news/", status_code=204)
async def translate_news(news: list[NewsSchema], session: AsyncSession = Depends(get_async_session)):
    """
    news: Список новостей об одной футбольной команде с ее веб-страницы.
    """
    news_handler = NewsHandler(news, session)
    await news_handler.handle_news()
    return
