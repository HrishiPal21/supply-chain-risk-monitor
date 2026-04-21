import time
import logging
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
