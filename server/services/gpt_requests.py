from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING

import server.services.g4f as g4f
from server.logger import get_logger

if TYPE_CHECKING:
    from aiohttp import ClientSession

logger = get_logger()

PROMPT = """
Choose a title and description for video subtitles and break subtitles into small topics which should cover the entire subtitles.
You will receive subtitles in the following format (start - video subtitles):
hh:mm:ss - subtitles
hh:mm:ss - subtitles
...

Respond with valid JSON in the following format (Substitude text in [square brackets]):
{"title": "[title]", "description": "[summarize what was said in the subtitles]", "topics": [{"start": "[hh:mm:ss]", "end": "[hh:mm:ss]"}, ...]}
"start" and "end" indicate the beginning and end of the discussion on this topic in video subtitles. Topics must cover all video subtitles and should last more than a minute. On russian language."""

TOPIC_PROMPT = """
Your task is to combine and format video subtitles into separate whole sentences in first person without losing the meaning, combine multiple video subtitles into one sentence to achive this task.
Highlight the actions that are asked to be done in subtitles with <b> at the beginning and </b> at the end. Make some sentences as oredred lists (1 ... 2 ... 3 ...)

Respond in russian language
You will receive subtitles in the following format:
hh:mm:ss - subtitles
hh:mm:ss - subtitles
...

Respond in russian language. Response template:
[title]
[hh:mm:ss - hh:mm:ss] [generated sentence]
[hh:mm:ss - hh:mm:ss] [generated sentence]
...

Substitude [hh:mm:ss - hh:mm:ss] with time, for example [00:01:22 - 00:01:35] and [generated sentences] with generated sentence. Do not provide text that does not fit the template.
"""


async def gpt_title_request(
        system: str,
        user: str,
        session: ClientSession,
) -> dict:
    content = {
        "title": None,
        "description": None,
        "topics": [],
    }

    if len(user) > 12000:
        request_query = await split_string(user, 12000)
    else:
        request_query = [user]

    for item in request_query:
        messages = [
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": item,
            },
        ]

        for event in await g4f.ChatCompletion.create(model="gpt-3.5-turbo-16k-0613", messages=messages, stream=True):
            try:
                json_data = try_loads(str(event))

                if not content['title']:
                    content["title"] = json_data["title"]
                    content["description"] = json_data["description"]
                content["topics"] += json_data["topics"]
            except json.JSONDecodeError:
                pass
    return content


async def gpt_topic_request(
        system: str,
        user: str,
        session: ClientSession,
) -> str:
    content = ''

    if len(user) > 12000:
        request_query = await split_string(user, 12000)
    else:
        request_query = [user]

    for item in request_query:
        messages = [
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": item,
            },
        ]

        for event in await g4f.ChatCompletion.create(model="gpt-3.5-turbo-16k-0613", messages=messages, stream=True):
            content += event
    return content


#
#
async def gpt_request(
        system: str,
        user: str,
        session: ClientSession,
):
    if system == "title":
        system = PROMPT
        content = await gpt_title_request(system=system, user=user, session=session)
        return content
    else:
        system = TOPIC_PROMPT
        content = await gpt_topic_request(system=system, user=user, session=session)
        return content


async def split_string(string, length) -> list[str]:
    substrings = []
    start = 0
    while start < len(string):
        end = start + length
        if end >= len(string):
            end = len(string)
        else:
            delimiter_index = string.rfind('\n', start, end)
            if delimiter_index != -1:
                end = delimiter_index + 1
        substrings.append(string[start:end])
        start = end
    return substrings


def try_loads(json_string: str):
    with contextlib.suppress(json.JSONDecodeError):
        return json.loads(json_string)
    json_string = (
        json_string.
        replace(', ...', '').
        replace(',...', '').
        replace('"end": ...', '"end": "0:00:00').
        replace('"end": "end"', '"end": "00:00:00"')
    )
    with contextlib.suppress(json.JSONDecodeError):
        return json.loads(json_string)
    with contextlib.suppress(json.JSONDecodeError):
        return json.loads(json_string.rstrip('}'))
    return json.loads(json_string.rstrip(']'))
