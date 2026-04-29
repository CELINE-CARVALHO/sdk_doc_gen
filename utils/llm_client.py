"""
utils/llm_client.py
Groq LLM client with retry logic, rate limit handling, and error reporting.
"""

import os
import re
import time
import logging
import random
import threading
from math import ceil
from typing import Optional, List, Dict
from groq import Groq, APIError, RateLimitError, APIConnectionError, AuthenticationError

from dotenv import load_dotenv

load_dotenv(override=True)


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.1-8b-instant"
MAX_RETRIES = 6
BASE_BACKOFF = 8.0
MIN_REQUEST_INTERVAL = 4.0
MAX_RETRY_WAIT = 90.0
MAX_CONNECTION_WAIT = 30.0
REQUEST_TOKEN_BUDGET = 5800
MIN_COMPLETION_TOKENS = 700


class LLMClient:
    """Groq LLM client with production-grade error handling."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError(
                "GROQ_API_KEY not found. Set it in your .env file or environment."
            )
        self.client = Groq(api_key=key)
        self.model = model or DEFAULT_MODEL
        self.min_request_interval = _env_float("GROQ_MIN_REQUEST_INTERVAL", MIN_REQUEST_INTERVAL)
        self.max_retries = _env_int("GROQ_MAX_RETRIES", MAX_RETRIES)
        self.max_retry_wait = _env_float("GROQ_MAX_RETRY_WAIT", MAX_RETRY_WAIT)
        self.request_token_budget = _env_int("GROQ_REQUEST_TOKEN_BUDGET", REQUEST_TOKEN_BUDGET)
        self.min_completion_tokens = _env_int("GROQ_MIN_COMPLETION_TOKENS", MIN_COMPLETION_TOKENS)
        self._last_request_at = 0.0
        self._request_lock = threading.Lock()

    def chat(
        self,
        messages: List[Dict],
        temperature: float = 0.3,
        max_tokens: int = 800,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Call Groq chat completion with retry/backoff.
        Returns the assistant's text response.
        """
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        max_tokens = self._fit_completion_budget(full_messages, max_tokens)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                self._pace_request()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content.strip()

            except AuthenticationError as e:
                raise ValueError(
                    "Groq API authentication failed (401/403). "
                    "Check your GROQ_API_KEY in .env."
                ) from e

            except RateLimitError as e:
                wait = self._retry_wait_seconds(e, attempt)
                logger.warning(
                    "Rate limited by Groq. Waiting %.1fs (attempt %s/%s)",
                    wait,
                    attempt + 1,
                    self.max_retries,
                )
                time.sleep(wait)
                last_error = e

            except APIConnectionError as e:
                wait = _with_jitter(min(BASE_BACKOFF * (attempt + 1), MAX_CONNECTION_WAIT))
                logger.warning("Connection error: %s. Retrying in %.1fs...", e, wait)
                time.sleep(wait)
                last_error = e

            except APIError as e:
                if getattr(e, "status_code", None) == 413:
                    retry_tokens = self._retry_tokens_after_payload_error(e, max_tokens)
                    if retry_tokens is not None:
                        logger.warning(
                            "Groq request was too large. Retrying with max_tokens=%s.",
                            retry_tokens,
                        )
                        max_tokens = retry_tokens
                        last_error = e
                        continue

                if getattr(e, "status_code", None) in {500, 502, 503, 504}:
                    wait = _with_jitter(min(BASE_BACKOFF * (2 ** attempt), self.max_retry_wait))
                    logger.warning(
                        "Groq API server error [%s]. Retrying in %.1fs (attempt %s/%s)",
                        e.status_code,
                        wait,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(wait)
                    last_error = e
                    continue

                raise RuntimeError(f"Groq API error [{e.status_code}]: {e.message}") from e

            except Exception as e:
                raise RuntimeError(f"Unexpected LLM error: {e}") from e

        raise RuntimeError(
            f"Groq API failed after {self.max_retries} retries. Last error: {last_error}"
        )

    def simple_prompt(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Convenience wrapper for single-turn prompts."""
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system,
            **kwargs,
        )

    def _pace_request(self) -> None:
        """Serialize requests and keep a small gap between them to avoid burst limits."""
        with self._request_lock:
            elapsed = time.monotonic() - self._last_request_at
            wait = self.min_request_interval - elapsed
            if wait > 0:
                time.sleep(wait)
            self._last_request_at = time.monotonic()

    def _retry_wait_seconds(self, error: RateLimitError, attempt: int) -> float:
        retry_after = _retry_after_header(error)
        if retry_after is not None:
            return min(_with_jitter(retry_after + 1.0), self.max_retry_wait)

        retry_from_message = _retry_after_message(str(error))
        if retry_from_message is not None:
            return min(_with_jitter(retry_from_message + 1.0), self.max_retry_wait)

        return min(_with_jitter(BASE_BACKOFF * (2 ** attempt)), self.max_retry_wait)

    def _fit_completion_budget(self, messages: List[Dict], requested_max_tokens: int) -> int:
        input_tokens = _estimate_messages_tokens(messages)
        available = self.request_token_budget - input_tokens
        if available >= requested_max_tokens:
            return requested_max_tokens

        fitted = max(self.min_completion_tokens, available)
        if fitted < requested_max_tokens:
            logger.warning(
                "Reducing max_tokens from %s to %s to fit Groq request budget "
                "(estimated input=%s, budget=%s).",
                requested_max_tokens,
                fitted,
                input_tokens,
                self.request_token_budget,
            )
        return fitted

    def _retry_tokens_after_payload_error(self, error: APIError, current_max_tokens: int) -> Optional[int]:
        requested = _requested_tokens_from_error(str(error))
        if requested is None or requested <= self.request_token_budget:
            return None

        overflow = requested - self.request_token_budget
        retry_tokens = current_max_tokens - overflow - 100
        if retry_tokens < self.min_completion_tokens:
            return None
        return retry_tokens


def _retry_after_header(error: RateLimitError) -> Optional[float]:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None

    value = headers.get("retry-after") or headers.get("Retry-After")
    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def _retry_after_message(message: str) -> Optional[float]:
    match = re.search(
        r"(?:try again|retry) in\s+(?:(\d+(?:\.\d+)?)\s*m(?:in(?:ute)?s?)?)?\s*(?:(\d+(?:\.\d+)?)\s*s(?:ec(?:ond)?s?)?)?",
        message,
        re.I,
    )
    if not match:
        return None

    minutes = float(match.group(1) or 0)
    seconds = float(match.group(2) or 0)
    total = minutes * 60 + seconds
    return total if total > 0 else None


def _with_jitter(seconds: float) -> float:
    return max(0.0, seconds + random.uniform(0.0, 1.5))


def _estimate_messages_tokens(messages: List[Dict]) -> int:
    text = "\n".join(str(message.get("content", "")) for message in messages)
    return max(1, ceil(len(text) / 3.6) + (len(messages) * 4))


def _requested_tokens_from_error(message: str) -> Optional[int]:
    match = re.search(r"Requested\s+(\d+)", message, re.I)
    if not match:
        return None
    return int(match.group(1))


def _env_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default
    return max(0.0, value)


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default
    return max(1, value)
