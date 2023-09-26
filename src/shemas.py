from pydantic import BaseModel


class NewsSchema(BaseModel):
    id: int
    link: str
    title: str
    short_description: str
