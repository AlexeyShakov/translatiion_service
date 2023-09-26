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