import re

import youtube_transcript_api
from fastapi.concurrency import run_in_threadpool

from server.logger import get_logger
from server.schemas import TranscriptPart
from server.services.transcript.transcript_provider_abc import TranscriptProvider

logger = get_logger()


class YouTubeTranscriptProvider(TranscriptProvider):
    """Получает расшифровку с YouTube"""

    _YOUTUBE_REGEX = r'^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*'
    _transcript_api = youtube_transcript_api.YouTubeTranscriptApi()

    async def get_transcript(self) -> list[TranscriptPart]:
        transcript = self._best_transcript(await self._get_transcripts())
        transcript_data = await run_in_threadpool(transcript.fetch)
        return [TranscriptPart(**entry) for entry in transcript_data]

    def _youtuble_url_to_video_id(self) -> str:
        if match := re.match(pattern=self._YOUTUBE_REGEX, string=self.url):
            return match[2]
        raise ValueError('Invalid youtube video URL')

    async def _get_transcripts(self) -> youtube_transcript_api.TranscriptList:
        video_id = self._youtuble_url_to_video_id()
        return await run_in_threadpool(self._transcript_api.list_transcripts, video_id)

    def _best_transcript(
            self,
            transcripts: youtube_transcript_api.TranscriptList,
    ) -> youtube_transcript_api.Transcript:
        best_langueges = [
            'ru', 'en', 'es', 'fr', 'de', 'it', 'pt', 'nl',
            'sv', 'da', 'no', 'fi', 'ru', 'ar', 'ja', 'ko', 'zh'
        ]

        def max_key(transcript: youtube_transcript_api.Transcript):
            language_code = transcript.language_code
            if language_code in best_langueges:
                return -best_langueges.index(language_code) - transcript.is_generated
            return float('-inf')

        return max(transcripts, key=max_key)
