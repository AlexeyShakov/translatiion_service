import asyncio
from dataclasses import asdict
from typing import Sequence
from sqlalchemy import select
from config import YANDEX_CATALOG, YANDEX_API_KEY, TRANSTLATION_URL
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from config import console_logger, logger
from enums import StepNameChoice
from shemas import NewsSchema
from models import Error, Post as PostDB


class NewsHandler:
    POST_WITH_ERRORS = []
    SUCCESS_NEWS = []

    def __init__(self, news: list[NewsSchema], session: AsyncSession) -> None:
        self.lock = asyncio.Lock()
        self.session = session
        self.news = news

    async def handle_news(self):
        tasks = [asyncio.create_task(self.make_translate_request(element)) for element in self.news]
        await asyncio.gather(*tasks)
        if self.POST_WITH_ERRORS:
            await self.update_posts_with_errors(StepNameChoice.TRANSTALTION.name, self.POST_WITH_ERRORS)
        if self.SUCCESS_NEWS:
            await self.send_news_to_telegram_service(self.SUCCESS_NEWS)

    async def make_translate_request(self, news: NewsSchema) -> None:
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
                        # self.SUCCESS_NEWS.append()
                        console_logger.info("Получен ответ от сервиса переводов")
                    else:
                        async with self.lock:
                            self.POST_WITH_ERRORS.append(news)
                        console_logger.info(
                            f"Сервис переводов вернул ошибку с кодом {resp.status} и текстом: {await resp.json()}"
                        )
                        logger.exception(
                            f"Сервис переводов вернул ошибку с кодом {resp.status} и текстом: {await resp.json()}")
            except aiohttp.ClientConnectorError:
                async with self.lock:
                    self.POST_WITH_ERRORS.append(news)
                logger.exception(f"Сервис переводов не отвечает")
            except Exception:
                async with self.lock:
                    self.POST_WITH_ERRORS.append(news)
                logger.exception(f"Сервис переводов не доступен по неизвестной ошибке")

    async def update_posts_with_errors(self, error_name: str, news: list[NewsSchema]) -> None:
        posts = await self._get_posts_from_db(news)
        query = select(Error).where(Error.step == error_name)
        result = await self.session.execute(query)
        error = result.scalars().first()
        for post in posts:
            post.error_id = error.id
        self.session.add_all(posts)
        await self.session.commit()

    async def _get_posts_from_db(self, news: list[NewsSchema]) -> Sequence[PostDB]:
        news_ids = [post.id for post in news]
        post_query = select(PostDB).where(PostDB.id.in_(news_ids))
        result = await self.session.execute(post_query)
        return result.scalars().all()

    async def send_news_to_telegram_service(self, news: list[NewsSchema]):
        async with aiohttp.ClientSession(timeout=5) as session:
            try:
                # Написать нормальный URL сервиса телеграмма и преобразовать news в list of dicts TODO
                async with session.post('http://something_228.com', json=asdict(news[0])) as resp:
                    pass
            except aiohttp.ClientConnectorError:
                logger.exception("Микросервис телеграмма недоступен")
                console_logger.exception("Микросервис телеграмма недоступен")
                # Вместо news я должен передавать list[PostDB] или не должен???? TODO
                await self.update_posts_with_errors(StepNameChoice.SENDING_TO_TELEGRAM.name, news)
            except Exception:
                logger.exception("Неизвестная ошибка при попытки отправить данные на сервис телеграмма")
                console_logger.exception("Неизвестная ошибка при попытки отправить данные на сервис телеграмма")
                await self.update_posts_with_errors(StepNameChoice.SENDING_TO_TELEGRAM.name, news)
