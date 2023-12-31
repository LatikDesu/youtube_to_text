from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from server.schemas import TranscriptPart

if TYPE_CHECKING:
    from aiohttp import ClientSession


class TranscriptProvider(ABC):
    """Класс для инкапсуляции логики получения текста из видео"""

    def __init__(
            self,
            url: str,
            session: ClientSession,
    ) -> None:
        self.url = url
        self.session = session

    @abstractmethod
    async def get_transcript(self) -> list[TranscriptPart]:
        raise NotImplementedError
