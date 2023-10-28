import asyncio
from src.config import console_logger, TRANSLATION_QUEUE, RABBITMQ_USER, RABBITMQ_PASS, logger, RABBIT_HOST

from aio_pika import connect
from aio_pika.abc import AbstractIncomingMessage
import base64
from src.utils.shemas import NewsSchema
from src.utils.funcs import NewsHandler
from src.db.db_connection import async_session_maker
import json


async def validate(news: list[dict]) -> list[NewsSchema]:
    return [NewsSchema(id=el["id"], link=el["link"], title=el["title"], short_description=el["short_description"])
            for el in news]


async def on_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        news = json.loads(base64.b64decode(message.body).decode())
        validated_news = await validate(news)
        async with async_session_maker() as session:
            news_handler = NewsHandler(validated_news, session)
            await news_handler.handle_news()


async def main() -> None:
    console_logger.info("В ожидании сообщений. Для выхода нажать CTRL+C")

    connection = await connect(f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBIT_HOST}/")

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(
            TRANSLATION_QUEUE,
            durable=True,
        )

        await queue.consume(on_message)
        await asyncio.Future()  # для того, чтобы программа работала бесконечно


if __name__ == "__main__":
    asyncio.run(main())
