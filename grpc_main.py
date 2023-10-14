import asyncio
from typing import Optional

from grpc_service import translation_pb2, translation_pb2_grpc
import grpc

from src.config import logger, console_logger, GRPC_TRANSLATION_PORT
from src.db.db_connection import async_session_maker
from src.utils.shemas import NewsSchema
from src.utils.funcs import NewsHandler


class TransltationServicer(translation_pb2_grpc.NewsTranslatorServicer):
    async def GetNews(self, request: translation_pb2.News, context) -> translation_pb2.NewsResponse:
        result = await self._validate_news(request)
        if not result:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Error while validating data!')
            return translation_pb2.NewsResponse()
        async with async_session_maker() as session:
            news_handler = NewsHandler(result, session)
            await news_handler.handle_news()
            return translation_pb2.NewsResponse()

    async def _validate_news(self, news: translation_pb2.News) -> Optional[list[NewsSchema]]:
        try:
            return [NewsSchema(id=post.id["id"], link=post.link["link"], title=post.title["title"],
                               short_description=post.short_description["short_description"]) for post in news.news]
        except Exception as e:
            logger.exception(f"При попытке валидировать данные возникла ошибка - {e}")
            return


async def serve():
    console_logger.info("Grpc-сервер поднят")
    server = grpc.aio.server()
    translation_pb2_grpc.add_NewsTranslatorServicer_to_server(TransltationServicer(), server)
    server.add_insecure_port(f"[::]:{GRPC_TRANSLATION_PORT}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
