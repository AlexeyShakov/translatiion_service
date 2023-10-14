import asyncio
from typing import Sequence
from sqlalchemy import select

from src.custom_exceptions import SenderNotFound
from src.config import YANDEX_CATALOG, YANDEX_API_KEY, TRANSTLATION_URL, TELEGRAM_URL, console_logger, logger, \
    OVER_HTTP, OVER_QUEUE, OVER_GRPC
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from .enums import StepNameChoice
from .shemas import NewsSchema, NewsTranslatedSchema, NewsBaseSchema
from src.db.models import Error, Post as PostDB


class NewsHandler:
    def __init__(self, news: list[NewsSchema], session: AsyncSession) -> None:
        self.lock = asyncio.Lock()
        self.session = session
        self.news = news
        self.post_with_errors = []
        self.success_news = []

    async def handle_news(self):
        tasks = [asyncio.create_task(self.make_translate_request(element)) for element in self.news]
        await asyncio.gather(*tasks)
        if self.post_with_errors:
            await self.update_posts_with_errors(StepNameChoice.TRANSTALTION.name, self.post_with_errors)
        if self.success_news:
            await self.send_news_to_telegram_service(self.success_news)

    async def make_translate_request(self, news: NewsSchema) -> None:
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
                        response_body = await resp.json()
                        translated_news = NewsTranslatedSchema(
                            id=news.id,
                            link=news.link,
                            translated_short_description=response_body["translations"][0]["text"],
                            translated_title=response_body["translations"][1]["text"]
                        )
                        async with self.lock:
                            self.success_news.append(translated_news)
                        console_logger.info("Получен ответ от сервиса переводов")
                    else:
                        async with self.lock:
                            self.post_with_errors.append(news)
                        console_logger.info(
                            f"Сервис переводов вернул ошибку с кодом {resp.status} и текстом: {await resp.json()}"
                        )
                        logger.exception(
                            f"Сервис переводов вернул ошибку с кодом {resp.status} и текстом: {await resp.json()}")
            except aiohttp.ClientConnectorError:
                async with self.lock:
                    self.post_with_errors.append(news)
                logger.exception(f"Сервис переводов не отвечает")
            except Exception:
                async with self.lock:
                    self.post_with_errors.append(news)
                logger.exception(f"Сервис переводов не доступен по неизвестной ошибке")

    async def update_posts_with_errors(self, error_name: str, news: list[NewsBaseSchema]) -> None:
        posts = await self._get_posts_from_db(news)
        query = select(Error).where(Error.step == error_name)
        result = await self.session.execute(query)
        error = result.scalars().first()
        for post in posts:
            post.error_id = error.id
        self.session.add_all(posts)
        await self.session.commit()

    async def update_post_with_translations(self, news: list[NewsTranslatedSchema]) -> None:
        """
        Если во время отправки новостей в сервис телеграмма произошло ошибка, то мы должны сохранить переведенные данные
        """
        posts = await self._get_posts_from_db(news)
        for post_db, post in zip(posts, news):
            post_db.translated_title = post.translated_title
            post_db.translated_short_description = post.translated_short_description
        self.session.add_all(posts)
        await self.session.commit()

    async def _get_posts_from_db(self, news: list[NewsBaseSchema]) -> Sequence[PostDB]:
        news_ids = [post.id for post in news]
        post_query = select(PostDB).where(PostDB.id.in_(news_ids))
        result = await self.session.execute(post_query)
        return result.scalars().all()

    async def send_news_to_telegram_service(self, news: list[NewsTranslatedSchema]) -> None:
        if OVER_HTTP:
            return await self.send_news_to_telegram_service_by_http(news)
        if OVER_QUEUE:
            return
        if OVER_GRPC:
            return await self.send_news_to_telegram_service_by_grpc(news)
        raise SenderNotFound()

    async def send_news_to_telegram_service_by_grpc(self, news: list[NewsTranslatedSchema]) -> None:
        pass

    async def send_news_to_telegram_service_by_http(self, news: list[NewsTranslatedSchema]) -> None:
        async with aiohttp.ClientSession() as session:
            try:
                data_for_telegram = [dict(element) for element in news]
                async with session.post(TELEGRAM_URL, json=data_for_telegram) as resp:
                    if resp.status != 204:
                        await self.update_posts_with_errors(StepNameChoice.SENDING_TO_TELEGRAM.name, news)
                        await self.update_post_with_translations(news)
                        return
                    console_logger.info("Данные успешно переданые на микросервис управлением телеграмма")
            except aiohttp.ClientConnectorError:
                logger.exception("Микросервис телеграмма недоступен")
                console_logger.exception("Микросервис телеграмма недоступен")
                await self.update_posts_with_errors(StepNameChoice.SENDING_TO_TELEGRAM.name, news)
                await self.update_post_with_translations(news)
            except Exception:
                logger.exception("Неизвестная ошибка при попытки отправить данные на сервис телеграмма")
                console_logger.exception("Неизвестная ошибка при попытки отправить данные на сервис телеграмма")
                await self.update_posts_with_errors(StepNameChoice.SENDING_TO_TELEGRAM.name, news)
                await self.update_post_with_translations(news)
