from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
from config import YANDEX_CATALOG, YANDEX_API_KEY, TRANSTLATION_URL
import asyncio

from datastructures import Post
from db_connection import get_async_session
from enums import StepNameChoice
from models import Error, Post as PostDB
from shemas import NewsSchema
from config import console_logger, logger

router = APIRouter()

POST_WITH_ERRORS = []

"""
Подумать, как я буду обрабатывать ошибки, которые случаются во время перевода статей и во время отправки на
сервис телеграмма. Сейчас я оперирую разными структурами. При попытки отправить данные на Телеграм я оперирую
списком новостей, а при попытке перевести одной новостью!!!!!!! Кажется надо переделывать 
"""
# TODO

@router.post("/traslate_news/", status_code=204)
async def translate_news(news: list[NewsSchema], session: AsyncSession = Depends(get_async_session)):
    """
    news: Список новостей об одной футбольной команде с ее веб-страницы.

    В объекте, который приходит из микросервиса парсера, в объекте новостей нужно передавать айдишки, по
    которым их можно найти в базе. Т.к. мне нужно как-то найти нужные объекты после того ,как я переведу
    заголовки статей TODO
    """
    global POST_WITH_ERRORS
    lock = asyncio.Lock()
    tasks = [asyncio.create_task(make_translate_request(element, session, lock)) for element in news]
    traslated_news = await asyncio.gather(*tasks)
    if POST_WITH_ERRORS:
        await _update_posts_with_errors(session, StepNameChoice.TRANSTALTION.name, POST_WITH_ERRORS)
        return
    # Отправляем ПЕРЕВЕДЕННЫЕ ДАННЫЕ на сервис, который работает с телеграммом
    await _send_news_to_telegram_service(traslated_news)
    return


async def make_translate_request(news: NewsSchema, db_session: AsyncSession, lock: asyncio.Lock) -> None:
    global POST_WITH_ERRORS
    async with aiohttp.ClientSession(timeout=5) as session:
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
                    console_logger.info("Получен ответ от сервиса переводов")
                    # НУЖНО ВОЗВРАЩАТЬ ПЕРЕВЕДЕННЫЙ объект
                else:
                    await _handle_erorr_when_translating(news, db_session, lock)
                    console_logger.info(
                        f"Сервис переводов вернул ошибку с кодом {resp.status} и текстом: {await resp.json()}"
                    )
                    logger.exception(f"Сервис переводов вернул ошибку с кодом {resp.status} и текстом: {await resp.json()}")
        except aiohttp.ClientConnectorError:
            await _handle_erorr_when_translating(news, db_session, lock)
            logger.exception(f"Сервис переводов не отвечает")
        except Exception:
            await _handle_erorr_when_translating(news, db_session, lock)
            logger.exception(f"Сервис переводов не доступен по неизвестной ошибке")


async def _handle_erorr_when_translating(news: NewsSchema, db_session: AsyncSession, lock: asyncio.Lock) -> None:
    post_query = select(PostDB).where(PostDB.title == news.title)
    result = await db_session.execute(post_query)
    async with lock:
        POST_WITH_ERRORS.append(result.scalars().first())


async def _update_posts_with_errors(session: AsyncSession, error_name: str, posts: list[PostDB]) -> None:
    global POST_WITH_ERRORS
    query = select(Error).where(Error.step == error_name)
    result = await session.execute(query)
    error = result.scalars().first()
    for post in posts:
        post.error_id = error.id
    session.add_all(POST_WITH_ERRORS)
    await session.commit()

async def _send_news_to_telegram_service(news: list[Post], db_session: AsyncSession):
    async with aiohttp.ClientSession(timeout=5) as session:
        try:
            # Написать нормальный URL сервиса телеграмма и преобразовать news в list of dicts TODO
            async with session.post('http://something_228.com', json=asdict(news[0])) as resp:
                pass
        except aiohttp.ClientConnectorError:
            logger.exception("Микросервис телеграмма недоступен")
            console_logger.exception("Микросервис телеграмма недоступен")
            # Вместо news я должен передавать list[PostDB] или не должен???? TODO
            await _update_posts_with_errors(db_session, "some_error", news)
        except Exception:
            logger.exception("Неизвестная ошибка при попытки отправить данные на сервис телеграмма")
            console_logger.exception("Неизвестная ошибка при попытки отправить данные на сервис телеграмма")
            await _update_posts_with_errors(db_session, "some_error", news)
