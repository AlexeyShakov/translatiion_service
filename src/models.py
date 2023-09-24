from sqlalchemy.orm import relationship

from db_connection import Base
from sqlalchemy import Integer, Column, Text, Enum, ForeignKey

from enums import StepNameChoice


class Error(Base):
    """
    Описывает, на каком этапе произошла ошибка при обработке новости
    """
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True)
    step = Column(Enum(StepNameChoice), nullable=False, unique=True)

    posts = relationship("Post", back_populates="error")


class Post(Base):
    """
    Описывает новости на сайте
    """
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    link = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    short_description = Column(Text, nullable=False)
    error_id = Column(Integer, ForeignKey('errors.id'), nullable=True, default=None)

    error = relationship("Error", back_populates="posts", lazy="joined")
