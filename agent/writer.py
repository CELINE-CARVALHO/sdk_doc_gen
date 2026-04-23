"""
Writer agent.
Generates SDK documentation strictly following the standard template format.
"""

from llm_client import call_llm

_SYSTEM = """You are a technical writer producing professional SDK documentation in Markdown.

STRICT FORMAT RULES — follow this exact structure for every symbol:

---

### `function_or_class_name()`

**Description**
One clear sentence explaining what this does.

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1    | str  | Yes      | What it does |

**Returns**
`ReturnType` — what it contains and when.

**Raises / Errors**

| Error | Cause | Solution |
|-------|-------|----------|
| ExceptionType | When it happens | How to fix |

**Example**

```language
# minimal working example
result = function_name(param1="value")
print(result)
```

**Notes**
- Any important edge cases, limits, or behavior to know.

---

Rules:
- Use the exact headers above — no variations
- Always include the Parameters table even for single params
- Always include a runnable code example
- Do not invent behavior not shown in the source
- Be concise — developers will skim this"""


_OVERVIEW_SYSTEM = """You are a technical writer producing professional SDK documentation.
Follow this EXACT structure — do not deviate:

# 🤖 {SDK Name} SDK Documentation

## 1. Overview

**SDK Name:** (fill from codebase)
**Version:** (fill if found, else "See repository")
**Description:** (one paragraph, what this SDK does)

**Key Features:**
- (bullet list from actual codebase capabilities)

**Supported Platforms:**
- (languages/platforms detected)

---

## 2. Quick Start 🚀

### Installation
```bash
pip install package-name
```

### Minimal Example
```language
(shortest possible working example)
```

---

## 3. Authentication 🔐
(how to provide API keys or tokens, from actual code)

---

## 4. Core Concepts 🧠
(key classes, models, or abstractions found in the codebase — one paragraph each)

---

## 5. Error Handling ⚠️

| Error | Cause | Solution |
|-------|-------|----------|
(fill from actual exceptions/errors found in code)

---

## 6. Best Practices ✅
- (inferred from code patterns)

---

## 7. Support 📞
- GitHub: (repo link if known)

Rules:
- Only use information from the provided code and analysis
- Keep all sections — use "Not found in source" if genuinely missing
- Use correct language tags on all code blocks"""


def _format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No source code available."
    return "\n\n".join(
        f"```\n{c['source'].strip()}\n```" for c in chunks[:5]
    )


def write_symbol_doc(symbol: str, chunks: list[dict], analysis: dict) -> str:
    language = analysis.get("language", "python")
    context = _format_context(chunks)

    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"Write SDK documentation for `{symbol}` using the exact format specified.\n"
                f"Language: {language}\n"
                f"Codebase summary: {analysis.get('summary', 'N/A')}\n\n"
                f"Source code:\n{context}"
            ),
        },
    ]

    result = call_llm(messages)
    if result.startswith("Error:"):
        return f"### `{symbol}()`\n\n> ⚠️ Documentation unavailable: {result}\n"
    return result


def write_overview(analysis: dict, repo_url: str = "") -> str:
    language = analysis.get("language", "unknown")
    patterns = ", ".join(analysis.get("patterns", [])) or "N/A"
    symbols = ", ".join(analysis.get("public_api", [])[:30]) or "N/A"

    messages = [
        {"role": "system", "content": _OVERVIEW_SYSTEM},
        {
            "role": "user",
            "content": (
                "Write the overview and quick-start sections using ONLY the information below.\n\n"
                f"Repository: {repo_url or 'unknown'}\n"
                f"Language: {language}\n"
                f"Summary: {analysis.get('summary', 'N/A')}\n"
                f"Architectural patterns: {patterns}\n"
                f"Public API symbols: {symbols}\n\n"
                "Follow the exact template format. Do not invent features not listed above."
            ),
        },
    ]

    result = call_llm(messages)
    if result.startswith("Error:"):
        return f"# SDK Documentation\n\n> ⚠️ Overview unavailable: {result}\n"
    return result