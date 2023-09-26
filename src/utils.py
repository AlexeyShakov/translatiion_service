"""
Что будет в классе?
1. Отправить запрос на перевод
2. Хранить новости, которые по каким-либо причинам не перевелись.
3. Отправить данные в телеграм
4. Сохранение новостей с ошибками.
    4.1 - при попытке перевода
    4.2 - при попытке отправить в телегу
"""
import asyncio

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
        self.handle_news(news)

    def handle_news(self, news: list[NewsSchema]):
        tasks = [asyncio.create_task(self.make_translate_request(element)) for element in news]
        await asyncio.gather(*tasks)
        if self.POST_WITH_ERRORS:
            await self.update_posts_with_errors(StepNameChoice.TRANSTALTION.name)
        if self.SUCCESS_NEWS:
            pass

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
                        self.POST_WITH_ERRORS.append(news)
                        console_logger.info(
                            f"Сервис переводов вернул ошибку с кодом {resp.status} и текстом: {await resp.json()}"
                        )
                        logger.exception(
                            f"Сервис переводов вернул ошибку с кодом {resp.status} и текстом: {await resp.json()}")
            except aiohttp.ClientConnectorError:
                self.POST_WITH_ERRORS.append(news)
                logger.exception(f"Сервис переводов не отвечает")
            except Exception:
                self.POST_WITH_ERRORS.append(news)
                logger.exception(f"Сервис переводов не доступен по неизвестной ошибке")

    async def update_posts_with_errors(self, error_name: str) -> None:
        posts = await self._get_posts_from_db()
        query = select(Error).where(Error.step == error_name)
        result = await self.session.execute(query)
        error = result.scalars().first()
        for post in posts:
            post.error_id = error.id
        self.session.add_all(posts)
        await self.session.commit()

    async def _get_posts_from_db(self) -> list[PostDB]:
        # Здесь нужно находить Post по списку их айдишке. Нужно в объекте news
        # из микросервиса парсера передавать еще айдишки новостей, т.к. после перевода
        # их заголовки изменяться # TODO
        pass
