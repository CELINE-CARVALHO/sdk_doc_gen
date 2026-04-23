"""
Token-aware chunker.
Uses tiktoken with a safe fallback so any model name works —
including HuggingFace models that tiktoken doesn't know about.
"""

import tiktoken
from config import CHAT_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


def _get_encoder():
    try:
        return tiktoken.encoding_for_model(CHAT_MODEL)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


_enc = _get_encoder()


def _token_len(text: str) -> int:
    return len(_enc.encode(text, disallowed_special=()))


def _split_by_tokens(text: str, size: int, overlap: int) -> list[str]:
    tokens = _enc.encode(text, disallowed_special=())
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + size, len(tokens))
        chunks.append(_enc.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start += size - overlap
    return chunks


def chunk_unit(unit: dict) -> list[dict]:
    source = unit.get("source", "").strip()
    if not source:
        return []
    if _token_len(source) <= CHUNK_SIZE:
        return [{**unit, "chunk_index": 0, "total_chunks": 1}]

    parts = _split_by_tokens(source, CHUNK_SIZE, CHUNK_OVERLAP)
    return [
        {**unit, "source": part, "chunk_index": i, "total_chunks": len(parts)}
        for i, part in enumerate(parts)
        if part.strip()
    ]


def chunk_units(units: list[dict]) -> list[dict]:
    result = []
    for unit in units:
        result.extend(chunk_unit(unit))
    return result