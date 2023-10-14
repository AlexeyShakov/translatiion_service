from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .config import SERVICE_NAME
from src.db.db_connection import get_async_session
from .utils.shemas import NewsSchema
from .utils.funcs import NewsHandler

router = APIRouter(prefix=f"/api/{SERVICE_NAME}")


@router.post(f"/traslate_news/", status_code=204)
async def translate_news(news: list[NewsSchema], session: AsyncSession = Depends(get_async_session)):
    """
    news: Список новостей об одной футбольной команде с ее веб-страницы.
    """
    news_handler = NewsHandler(news, session)
    await news_handler.handle_news()
    return
