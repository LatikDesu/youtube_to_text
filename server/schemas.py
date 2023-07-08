from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

_YOUTUBE_REGEX = r'^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*'
_TIME_REGEX = r'^\d{1,2}:\d{1,2}:\d{1,2}$'


@dataclass
class TranscriptEntry:
    """Фрагмент расшифровки"""
    text: str
    start: float
    duration: float


class ScreenshotSaveType(str, Enum):
    """Типы сохранения скриншотов"""
    DIRECT = 'direct'
    IMGUR = 'imgur'


class ScreenshotSelectorType(str, Enum):
    """Типы селектора скриншотов"""
    UNIFORM = 'uniform'
    SIMILARITY = 'similarity'
    CIRCLE_RECTANGLE = 'circle_rectangle'


class ArticleRequest(BaseModel):
    """Схема запроса статьи, для endpoint"""

    number_of_paragraphs: int = Field(ge=2, default=3)
    number_of_screenshots: int = Field(ge=1, default=3)
    url: str = Field(regex=_YOUTUBE_REGEX)
    start: int = Field(ge=0, default=0)
    end: int = Field(ge=0, default=0)
    force_whisper: bool = False
    selector: ScreenshotSelectorType = ScreenshotSelectorType.UNIFORM
    image_save_format: ScreenshotSaveType = ScreenshotSaveType.DIRECT


class ArticleTopic(BaseModel):
    """Одна из тем статьи. Статья может иметь произвольное количество тем"""
    start: str = Field(regex=_TIME_REGEX)
    end: str = Field(regex=_TIME_REGEX)
    title: Optional[str] = None
    paragraphs: Optional[str] = None
    images: list[str] = []


class GenerationTime(BaseModel):
    """Время генерации каждой части статьи"""
    total: float = 0
    images: float = 0
    title: float = 0
    transcript: float = 0
    content: float = 0


class Article(BaseModel):
    """Готовая статья"""
    video_id: str
    title: str
    description: str
    topics: list[ArticleTopic]
    generation_time: GenerationTime
