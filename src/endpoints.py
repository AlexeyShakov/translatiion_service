from fastapi import APIRouter
from shemas import NewsSchema

router = APIRouter()

@router.post("/traslate_news/", status_code=204)
async def translate_news(news: list[NewsSchema]):
    return
