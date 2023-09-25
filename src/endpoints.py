from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
from config import YANDEX_CATALOG, YANDEX_API_KEY, TRANSTLATION_URL
import asyncio
from db_connection import get_async_session
from enums import StepNameChoice
from models import Error, Post
from shemas import NewsSchema

router = APIRouter()

POST_WITH_ERRORS = []

@router.post("/traslate_news/", status_code=204)
async def translate_news(news: list[NewsSchema], session: AsyncSession=Depends(get_async_session)):
    """
    news: Список новостей об одной футбольной команде с ее веб-страницы.
    """
    global POST_WITH_ERRORS
    lock = asyncio.Lock()
    tasks = [asyncio.create_task(make_translate_request(element, session, lock)) for element in news]
    await asyncio.gather(*tasks)
    if POST_WITH_ERRORS:
        await _update_posts_with_errors(session)
        return
    return


async def make_translate_request(news: NewsSchema, db_session: AsyncSession, lock: asyncio.Lock):
    global POST_WITH_ERRORS
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(YANDEX_API_KEY)
        }
        body = {
            "targetLanguageCode": "ru",
            "texts": [news.short_description, news.title],
            "folderId": YANDEX_CATALOG
        }
        try:
            async with session.post(TRANSTLATION_URL, json=body, headers=headers) as resp:
                if resp.status == 200:
                    print(await resp.json())
                    # ЧТО-ТО НУЖНО ВЕРНУТЬ?????? TODO
                else:
                    await _handle_erorr_when_translating(news, db_session, lock)
                    # Добавить лог TODO
        except aiohttp.ClientConnectorError:
            await _handle_erorr_when_translating(news, db_session, lock)
        except Exception:
            await _handle_erorr_when_translating(news, db_session, lock)
            # Добавить лог TODO

async def _handle_erorr_when_translating(news: NewsSchema, db_session: AsyncSession, lock: asyncio.Lock) -> None:
    post_query = select(Post).where(Post.title == news.title)
    result = await db_session.execute(post_query)
    async with lock:
        POST_WITH_ERRORS.append(result.scalars().first())

async def _update_posts_with_errors(session: AsyncSession) -> None:
    global POST_WITH_ERRORS
    query = select(Error).where(Error.step == StepNameChoice.TRANSTALTION.name)
    result = await session.execute(query)
    error = result.scalars().first()
    for post in POST_WITH_ERRORS:
        post.error_id = error.id
    session.add_all(POST_WITH_ERRORS)
    await session.commit()
