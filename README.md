# Сервис переводов футбольных новостей

## Описание проекта
Данный проект является вспомогательным для данного проекта https://github.com/AlexeyShakov/club_news_parser, где можно прочитать
более детальное описание в README.md

## Описание работы сервиса
1. Получает новости от парсера.
2. Переводит новости с помощью яндекс переводчика.
3. Переведенные данные отправляются на сервис, где они(новости) публикуются в группу в телеграмме.

В качестве "доставщика" сообщений между сервисами может использоваться одна из следующих технологий: REST API, GRPC, 
брокер сообщений.

## Используемые технологии
* aiohttp - в качестве асинхронного клиента для посылки данных на другие сервисы;
* grpc - для посылки данных на другие микросервисы;
* брокер сообщений - для посылки данных на другие микросервисы;
* sqlalchemy и alembic - для взаимодействие с SQL БД(PostgreSQL);
* fastapi - для реализации асинхронного сервера, который принимает информацию от сервиса парсера.

## Зависимости
См. файл requirements.txt.

В процессе работы сервисов используется стороннее API(яндекс переводчик) для перевода новостей.
Для работы c переводчиком нужно зарегистрироваться и получить специальный токен. Этот токен должен лежать в
.env-файле. Инструкция по получению токена: https://cloud.yandex.ru/docs/translate/operations/

## Структура проекта
- logs
- src
- .env
- .gitignore
- main.py
- grpc_main.py
...

## Структура .env
DB_PORT=<порт для postgres-сервера>

DB_HOST=localhost

POSTGRES_DB=<название базы данных>

POSTGRES_USER=<юзернэйм пользователя БД>

POSTGRES_PASSWORD=<пароль от БД>

IAMTOKEN=<Токен для использования API яндекс переводчика>

CATALOG=<Нужен для использования яндекс переводчика>

TELEGRAM_URL=<URL сервиса отправки сообщений в телеграмм>

OVER_HTTP= 0 или 1 - указатель того, что используется REST API для общения между сервисами

OVER_GRPC= 0 или 1 - указатель того, что используется GRPC для общения между сервисами

OVER_QUEUE= 0 или 1 - указатель того, что используется брокер сообщений для общения между сервисами

GRPC_TRANSLATION_PORT=<порт, на котором запущен grpc-сервер сервиса переводов>

GRPC_TELEGRAM_PORT=<порт, на котором запущен grpc-сервер сервиса публикации новостей в телеграмм>

## Разворачивание проекта
