from pydantic import BaseModel


class NewsSchema(BaseModel):
    link: str
    title: str
    short_description: str
