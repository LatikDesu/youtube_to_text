import asyncio
import time
from datetime import timedelta
from typing import Sequence, Iterable, TYPE_CHECKING

import nltk
import pytube
from aiohttp import ClientSession
from youtube_transcript_api import _errors as youtube_transcript_errors

from server.logger import get_logger
from server.schemas import ArticleRequest, Article, TranscriptPart, ArticleTopic, GenerationTime
from server.services.gpt_requests import gpt_request
from server.services.transcript.fromWhisper import WhisperTranscriptProvider
from server.services.transcript.fromYoutube import YouTubeTranscriptProvider
from server.services.transcript.restorePunctuation import restore_punctuation
from server.services.transcript.utils import preporcess_transcript

if TYPE_CHECKING:
    from aiohttp import ClientSession

logger = get_logger()


class ArticleGenerator:
    """
    Генерирует статьи на основе запроса.
    """

    def __init__(
            self,
            request: ArticleRequest,
            session: ClientSession
    ) -> None:
        self.request = request
        self.session = session
        self._article: Article

    async def generate_article(self) -> Article:
        """Выполняет все шаги по генерации статьи и возвращает её"""

        start_time = time.monotonic()
        request = self.request

        url = pytube.YouTube(request.url).watch_url

        logger.info('Starting generating article for %s', url)
        logger.info('Gathering transcript for %s', url)
        transcript_generation_start_time = time.monotonic()
        transcript = await self._get_transcript()  # получили список объектов транскрипции вида TranscriptPart(text=..., start=..., duration=...)
        transcript_generation_time = time.monotonic() - transcript_generation_start_time
        if request.start or request.end:  # если есть начало и конец запроса, то получили список объектов из этого промежутка
            transcript = _truncate_transcript(transcript, request.start, request.end)
        logger.debug('Transcript for %s %s', url, transcript)

        sentences = await self._get_sentences(transcript)
        logger.debug('Sentences from transcript -->  %s', transcript)

        logger.info('Start generating article title and themes for %s', url)
        await self._generate_partial_article(transcript)

        await self._generate_article_content(transcript)

        article = self._article
        article.generation_time.transcript = transcript_generation_time
        return article

    #
    #         screenshot_periods = [
    #             (get_sec(topic.start), get_sec(topic.end)) for topic in article.topics
    #         ]
    #         logger.info('gathering frames and generating content for %s', url)
    #         logger.debug('Screenshot Periods %s', screenshot_periods)
    #         images_start_time = time.monotonic()
    #         frames, _ = await asyncio.gather(
    #             run_in_threadpool(
    #                 extract_frames,
    #                 url,
    #                 screenshot_periods,
    #                 request.number_of_screenshots,
    #                 request.selector,
    #             ),
    #             self._generate_article_content(transcript)
    #         )
    #         article.generation_time.images = time.monotonic() - images_start_time
    #         logger.info('process images for %s using %s', url, request.image_format)
    #         postprocessor = get_postrocessor(request.image_format)()
    #         processed_images = await asyncio.gather(
    #             *[postprocessor.process_many(topic_frames, self.session) for topic_frames in frames]
    #         )
    #         for topic, processed_topic_frames in zip(article.topics, processed_images):
    #             topic.images = processed_topic_frames
    #         article.generation_time.total = time.monotonic() - start_time
    #         article.generation_time.transcript = transcript_generation_time
    #         return article
    #
    async def _get_transcript(self) -> list[TranscriptPart]:
        """Выбирает TranscriptProvider исходя из запроса и запрашивает транскрипцию"""
        url = pytube.YouTube(self.request.url).watch_url
        if self.request.force_whisper:
            provider = WhisperTranscriptProvider(url, self.session)
        else:
            provider = YouTubeTranscriptProvider(url, self.session)
        try:
            return await provider.get_transcript()
        except youtube_transcript_errors.TranscriptsDisabled:
            logger.info('No transcripts for %s, use whisper fallback', url)
            provider = WhisperTranscriptProvider(url, self.session)
            return await provider.get_transcript()

    async def _get_sentences(
            self,
            transcript_parts: Sequence[TranscriptPart],
    ) -> list[TranscriptPart]:
        """Разделяем субтитры из видео на предложения"""
        raw_text = ' '.join([part.text for part in transcript_parts]).lower()  # получаем голый текст
        clear_text = preporcess_transcript(raw_text)  # убираем лишнее из текста
        del raw_text

        sentences_list = restore_punctuation(clear_text)  # восстанавливаем пунктуацию
        sentences_str = ' '.join(sentences_list[0])
        del sentences_list

        sentences = nltk.sent_tokenize(sentences_str)  # разделяем на предложения
        del sentences_str

        print("ПРЕДЛОЖЕНИЯ", sentences)
        return sentences

    async def _generate_partial_article(
            self,
            transcript_parts: Sequence[TranscriptPart],
    ) -> None:
        """Генерирует заголовок и время для каждой темы"""
        start_time = time.monotonic()
        subtitles = _format_transcript(transcript_parts)
        article_dict = await gpt_request('title', '\n'.join(subtitles), self.session)
        logger.info('Complete theme and topics ...')

        if self.request.number_of_paragraphs == 3:
            number_of_paragraphs = (transcript_parts[-1].start - transcript_parts[0].start) / 300
        else:
            number_of_paragraphs = self.request.number_of_paragraphs

        topics = [ArticleTopic(**topic_data) for topic_data in article_dict['topics']]
        if number_of_paragraphs < len(topics):
            number_of_seconds = transcript_parts[-1].start - transcript_parts[0].start
            approximate_topic_length = number_of_seconds / number_of_paragraphs
            topics = _recombine_topics(approximate_topic_length, topics)
        if number_of_paragraphs != len(topics):
            logger.warning('Number of topics is not equal to the requested')
        logger.info('Complete topics count ...')

        self._article = Article(
            video_id=pytube.YouTube(self.request.url).video_id,
            title=article_dict['title'],
            description=article_dict['description'],
            topics=topics,
            generation_time=GenerationTime(title=time.monotonic() - start_time),
        )

    async def _generate_article_content(
            self,
            transcript_parts: Sequence[TranscriptPart],
    ) -> None:
        """Генерирует контент и заголовок для каждой темы"""
        start_time = time.monotonic()
        topics = self._article.topics

        transcript_parts_for_topics = [
            _select_transcript_entries_for_topic(
                transcript_parts, topic
            ) for topic in topics
        ]

        logger.debug(
            'Lenght of transcript: %d before splitting, %d after',
            len(transcript_parts),
            sum(len(entry) for entry in transcript_parts_for_topics)
        )

        topic_datas = await asyncio.gather(*[
            gpt_request('topic', '\n'.join(_format_transcript(transcript_parts)), self.session)
            for transcript_parts in transcript_parts_for_topics if transcript_parts
        ])
        for data, filtered_topics in zip(topic_datas, topics):
            title, *paragraphs = data.splitlines()
            if not paragraphs:
                filtered_topics.title = 'Не удалось сгенерировать'
                filtered_topics.paragraphs = title
            else:
                filtered_topics.title = title
                filtered_topics.paragraphs = '\n'.join(paragraphs)
        filtered_topics = list(filter(lambda topic: topic.paragraphs, topics))
        if len(filtered_topics) != len(topics):
            logger.warning(
                'Some topics has no paragraphs so was removed. This means that the model '
                'gave the wrong answer, the quality of the article may suffer.'
            )
        self._article.generation_time.content = time.monotonic() - start_time


def _truncate_transcript(
        transcript: list[TranscriptPart],
        start: float,
        end: float
) -> list[TranscriptPart]:
    """Выбирает субтитры, которые подходят по времени."""
    return [entry for entry in transcript if start < entry.start < end]


def _format_transcript(transcript_parts: Iterable[TranscriptPart]) -> list[str]:
    """Приводит TranscriptPart к формату строки, которая будет отправлена языковой модели"""
    result = []
    for entry in transcript_parts:
        start = entry.start
        text = entry.text
        result.append(f'{timedelta(seconds=int(start))} - {text}')
    return result


def _recombine_topics(
        approximate_topic_length: float,
        old_topics: list[ArticleTopic]
) -> list[ArticleTopic]:
    """
    Соединяет несколько подтем в одну
    """
    last_topic_end = get_sec(old_topics[-1].end)
    topics = []
    topic_start_time = old_topics[0].start
    topic_start_second = get_sec(topic_start_time)
    for old_topic in old_topics:
        end_time = get_sec(old_topic.end)
        if (
                end_time - topic_start_second > approximate_topic_length and
                last_topic_end - topic_start_second > approximate_topic_length
        ):
            topics.append(ArticleTopic(
                start=topic_start_time,
                end=old_topic.end,
            ))
            topic_start_time = old_topic.end
            topic_start_second = end_time
        if end_time != topic_start_second:
            topics.append(ArticleTopic(
                start=topic_start_time,
                end=old_topic.end,
            )
            )

    return topics


def get_sec(time_str: str) -> int:
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def _select_transcript_entries_for_topic(
        transcript_parts: Sequence[TranscriptPart],
        topic: ArticleTopic,
) -> list[TranscriptPart]:
    """
    Выбирает субтитры, которые подходят под указанную тему исходя из времени.
    """
    start = get_sec(topic.start)
    end = get_sec(topic.end)
    return [entry for entry in transcript_parts if start <= entry.start <= end]
