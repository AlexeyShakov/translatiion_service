from dataclasses import dataclass


@dataclass
class Post:
    """
    Класс описывает пост на сайте
    """
    link: str
    title: str
    short_description: str
