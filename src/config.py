from dotenv import load_dotenv
import os
import logging
from pathlib import Path

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PORT = os.getenv("DB_PORT")

TRANSTLATION_URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"
YANDEX_API_KEY = os.getenv("IAMTOKEN")
YANDEX_CATALOG = os.getenv("CATALOG")

SERVICE_NAME = "translation"

TELEGRAM_URL = os.getenv("TELEGRAM_URL")

logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = logging.FileHandler(os.path.join(Path(__file__).parent.parent, "logs//logs.log"), encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

console_logger = logging.getLogger("console_logger")
console_logger.setLevel(logging.INFO)
if not console_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
    console_handler.setFormatter(formatter)
    console_logger.addHandler(console_handler)

OVER_HTTP = int(os.getenv("OVER_HTTP"))
OVER_GRPC = int(os.getenv("OVER_GRPC"))
OVER_QUEUE = int(os.getenv("OVER_QUEUE"))

GRPC_TRANSLATION_PORT = os.getenv("GRPC_TRANSLATION_PORT")
GRPC_TELEGRAM_PORT = os.getenv("GRPC_TELEGRAM_PORT")
