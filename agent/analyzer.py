"""
Analyzer agent.
Reads code samples, returns structured JSON describing the codebase's
public API, language, patterns, and a one-line summary.
"""

import json
from llm_client import call_llm

_SYSTEM = """You are a senior software engineer analyzing source code.
Given code samples, return a JSON object with exactly these keys:
- summary    : one sentence describing what this codebase does
- public_api : list of public function/class names worth documenting
- patterns   : list of notable architectural patterns observed
- language   : primary programming language detected

Rules:
- Respond ONLY with valid JSON — no preamble, no markdown fences.
- Do not invent symbols not present in the code.
- public_api must contain real names found in the source."""

_FALLBACK = {
    "summary": "Could not analyze codebase.",
    "public_api": [],
    "patterns": [],
    "language": "unknown",
}


def analyze(chunks: list[dict]) -> dict:
    if not chunks:
        return _FALLBACK

    sources = "\n\n---\n\n".join(
        f"File: {c['metadata'].get('file_path', 'unknown')}\n{c['source']}"
        for c in chunks[:20]
    )

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Analyze this codebase:\n\n{sources}"},
    ]

    raw = call_llm(messages, max_tokens=1024)

    if raw.startswith("Error:"):
        return {**_FALLBACK, "summary": raw}

    try:
        cleaned = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(cleaned)
        for key in _FALLBACK:
            result.setdefault(key, _FALLBACK[key])
        return result
    except json.JSONDecodeError:
        return {**_FALLBACK, "summary": f"Analysis parse error. Raw: {raw[:200]}"}