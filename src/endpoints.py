from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
from config import YANDEX_CATALOG, YANDEX_API_KEY, TRANSTLATION_URL

from db_connection import get_async_session
from models import Error
from shemas import NewsSchema

router = APIRouter()

@router.post("/traslate_news/", status_code=204)
async def translate_news(news: list[NewsSchema], session: AsyncSession=Depends(get_async_session)):
    for element in news:
        await make_translate_request(element)
    return


async def make_translate_request(news: NewsSchema):
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
        async with session.post(TRANSTLATION_URL, json=body, headers=headers) as resp:
            if resp.status == 200:
                print(await resp.json())


