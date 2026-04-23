"""
Shared LLM client for all agents.
Uses OpenAI-compatible interface pointed at HuggingFace Inference Router.
Import call_llm() anywhere — model is always read from config, never hardcoded.
"""

import re
from openai import OpenAI, APIError, APITimeoutError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import HF_TOKEN, HF_BASE_URL, CHAT_MODEL, LLM_TEMPERATURE, MAX_TOKENS_RESPONSE

_client = OpenAI(
    api_key=HF_TOKEN,
    base_url=HF_BASE_URL,
)

_RETRYABLE = (APITimeoutError, APIConnectionError)


def _strip_thinking(text: str) -> str:
    """
    Remove <think>...</think> blocks produced by Qwen3 and similar
    reasoning models before returning content to callers.
    Handles both closed blocks and unclosed/truncated ones.
    """
    # Remove complete <think>...</think> blocks (including multiline)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove any leftover unclosed opening tag and everything after it
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    return text.strip()


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=2, max=15),
)
def call_llm(messages: list[dict], max_tokens: int = MAX_TOKENS_RESPONSE) -> str:
    """
    Send messages to the configured HF chat model.
    Returns the response text, or a descriptive error string on failure.
    Automatically strips <think> reasoning blocks (Qwen3, DeepSeek-R1, etc.).
    """
    if not messages:
        return "Error: No messages provided to call_llm."

    try:
        response = _client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            return "Error: Model returned an empty response."

        content = _strip_thinking(content)

        if not content:
            return "Error: Model returned only a thinking block with no actual content."

        return content

    except APIError as e:
        return f"Error: LLM API error — {e.status_code}: {e.message}"
    except Exception as e:
        return f"Error: Unexpected failure — {e}"