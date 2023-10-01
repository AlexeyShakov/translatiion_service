from pydantic import BaseModel


class NewsBaseSchema(BaseModel):
    id: int
    link: str


class NewsSchema(NewsBaseSchema):
    title: str
    short_description: str


class NewsTranslatedSchema(NewsBaseSchema):
    translated_title: str
    translated_short_description: str
