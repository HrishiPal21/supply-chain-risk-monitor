from __future__ import annotations

import time
import logging
from typing import Optional
from openai import RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

_DELAYS = [2, 4, 8, 16]


def chat_with_retry(client, **kwargs):
    """Wrap client.chat.completions.create with backoff on 429 and 5xx."""
    for attempt, delay in enumerate(_DELAYS, 1):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError:
            if attempt == len(_DELAYS):
                raise
            logger.warning("OpenAI rate limit — retrying in %ds (attempt %d)", delay, attempt)
            time.sleep(delay)
        except APIStatusError as exc:
            if exc.status_code < 500 or attempt == len(_DELAYS):
                raise
            logger.warning("OpenAI server error %d — retrying in %ds (attempt %d)", exc.status_code, delay, attempt)
            time.sleep(delay)


def embed_with_retry(client, model: str, input: str, dimensions: Optional[int] = None) -> list[float]:
    """Embed a single text with backoff on 429 and 5xx."""
    kwargs = {"model": model, "input": input}
    if dimensions is not None:
        kwargs["dimensions"] = dimensions
    for attempt, delay in enumerate(_DELAYS, 1):
        try:
            resp = client.embeddings.create(**kwargs)
            return resp.data[0].embedding
        except RateLimitError:
            if attempt == len(_DELAYS):
                raise
            logger.warning("OpenAI embed rate limit — retrying in %ds (attempt %d)", delay, attempt)
            time.sleep(delay)
        except APIStatusError as exc:
            if exc.status_code < 500 or attempt == len(_DELAYS):
                raise
            logger.warning("OpenAI embed server error %d — retrying in %ds (attempt %d)", exc.status_code, delay, attempt)
            time.sleep(delay)


def embed_batch_with_retry(client, model: str, inputs: list[str]) -> list[list[float]]:
    """Embed a batch of texts in a single API call with backoff on 429 and 5xx."""
    for attempt, delay in enumerate(_DELAYS, 1):
        try:
            resp = client.embeddings.create(model=model, input=inputs)
            ordered = sorted(resp.data, key=lambda x: x.index)
            return [item.embedding for item in ordered]
        except RateLimitError:
            if attempt == len(_DELAYS):
                raise
            logger.warning("OpenAI batch embed rate limit — retrying in %ds (attempt %d)", delay, attempt)
            time.sleep(delay)
        except APIStatusError as exc:
            if exc.status_code < 500 or attempt == len(_DELAYS):
                raise
            logger.warning("OpenAI batch embed server error %d — retrying in %ds (attempt %d)", exc.status_code, delay, attempt)
            time.sleep(delay)
