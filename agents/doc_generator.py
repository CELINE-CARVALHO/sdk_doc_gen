"""
agents/doc_generator.py
Generates deep, SDK-quality documentation using LLM + RAG context.
Extracts reasoning, intent, logic flow, and full API surface per file.
"""

import logging
from typing import List, Dict, Optional
from utils.llm_client import LLMClient
from rag.retriever import VectorStore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite SDK documentation engine used by world-class engineering teams.

ABSOLUTE RULES — NEVER VIOLATE:
1. ONLY document what is explicitly present in the provided source code context.
2. NEVER invent, assume, or hallucinate function names, parameters, return types, or behaviors.
3. If a type annotation is missing from the code, write `Any` — do not guess.
4. If a docstring exists in the code, quote it verbatim in italics. Do not paraphrase it.
5. If something cannot be determined from the context, write: `*Not determinable from source.*`
6. Output ONLY valid Markdown. Zero prose introductions. Zero filler sentences.
7. Every code example must use REAL names from the source. Never write placeholder comments.
8. Be surgical and precise. A developer will copy this into production documentation.

REASONING EXTRACTION RULES:
- Read the code deeply. Understand WHY it was written that way, not just WHAT it does.
- Identify implicit contracts: what must be true BEFORE calling a function, and what is guaranteed AFTER.
- Detect error conditions, edge cases, and side effects visible in the code.
- Identify the design intent from class/function naming, inheritance, and composition patterns.
- Surface non-obvious behavior: mutation of inputs, global state, thread safety, ordering requirements."""


class DocGeneratorAgent:
    """Generates deep, reasoning-aware documentation from source code via LLM + RAG."""

    def __init__(self, llm: LLMClient, vector_store: VectorStore):
        self.llm = llm
        self.vs = vector_store

    def _retrieve_context(self, query: str, top_k: int = 6) -> str:
        chunks = self.vs.retrieve(query, top_k=top_k)
        if not chunks:
            return "*No source context retrieved.*"
        parts = [f"<!-- SOURCE: {c['source']} -->\n{c['text']}" for c in chunks]
        return "\n\n---\n\n".join(parts)

    def generate_overview(self, analysis: Dict, files: List[Dict] = None) -> str:
        ctx_parts = []
        for q in [
            f"entry point main module __init__ {analysis.get('project_name', '')}",
            "class definition public interface exports purpose",
            "README description goal problem",
        ]:
            ctx_parts.append(self._retrieve_context(q, top_k=4))
        ctx = "\n\n===\n\n".join(ctx_parts)

        prompt = f"""You are documenting `{analysis['project_name']}` for its SDK reference page.

METADATA:
{_fmt_analysis(analysis)}

SOURCE CODE CONTEXT:
{ctx}

Extract deep understanding: What problem does this solve? What is the primary abstraction?
What are the REAL capabilities derived from actual classes/functions?

OUTPUT — EXACTLY this structure:

# `{analysis['project_name']}`

> **One sentence.** What this does and who it is for. Derived strictly from the code.

## What It Does
*(2–4 sentences. Explain the core problem solved and approach. Reference actual module/class names.)*

## Key Capabilities
*(Each bullet = one concrete capability backed by a real class or function from context. Format: `**Name** — description.`)*

## Mental Model
*(2–3 sentences. The primary abstraction a developer must internalize. What is the unit of work? What owns what?)*

## Tech Stack
| Component | Technology | Version / Notes |
|-----------|------------|-----------------|

## Project Layout
```
{analysis.get('file_tree', '(file tree not available)')}
```
*(After the tree, one bullet per top-level module explaining its role.)*"""

        return self.llm.simple_prompt(prompt, system=SYSTEM_PROMPT, max_tokens=2000)

    def generate_installation(self, analysis: Dict, files: List[Dict]) -> str:
        setup_content = ""
        for f in files:
            fname = f["path"].lower().split("/")[-1]
            if any(kw in fname for kw in ["requirements", "setup.py", "pyproject.toml",
                                           "package.json", "go.mod", "cargo.toml", "gemfile"]):
                setup_content += f"\n<!-- FILE: {f['path']} -->\n```\n{f['content'][:1000]}\n```\n"

        env_ctx = self._retrieve_context("os.getenv environ .env environment variable config", top_k=5)

        prompt = f"""Document the installation and setup procedure for `{analysis['project_name']}`.

LANGUAGE: {analysis.get('language', 'unknown')}
FRAMEWORK: {analysis.get('framework', 'unknown')}
DEPENDENCIES: {', '.join(analysis.get('dependencies', [])[:15]) or 'none detected'}

DEPENDENCY FILES:
{setup_content or '*(No setup files found.)*'}

ENVIRONMENT VARIABLE USAGE IN SOURCE:
{env_ctx}

RULES:
- Use EXACT package names from the dependency files above.
- List ONLY env vars that appear in the source context.
- If no env vars detected, omit the Environment section entirely.
- Version numbers must come from dependency files — do not invent them.
- Verification step must use a real import or command from the code.

OUTPUT — EXACTLY this structure:

## Installation

### Prerequisites
*(Runtime requirements: language version, system tools. Base on setup files. If unspecified, say so.)*

### Install
```bash
(exact commands from dependency files)
```

### Environment Variables
*(Include ONLY if env vars detected in source.)*

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|

### Verify
```{analysis.get('language', 'bash').lower()}
(smoke-test using real module/class names from the code)
```"""

        return self.llm.simple_prompt(prompt, system=SYSTEM_PROMPT, max_tokens=1500)

    def generate_api_docs(self, analysis: Dict, files: List[Dict] = None) -> str:
        ctx = self._retrieve_context(
            "class def function method __init__ return raise parameter self async property staticmethod classmethod decorator",
            top_k=15,
        )

        prompt = f"""Produce a COMPLETE SDK-style API Reference for `{analysis['project_name']}`.

SOURCE CODE — your ONLY ground truth. Document everything visible here:
{ctx}

EXTRACTION RULES:
- Document EVERY class, public function, and public method visible in the context.
- For each item extract:
  1. Exact signature with type annotations as written (use `Any` if unannotated)
  2. Purpose from docstring (verbatim) or inferred from implementation (mark as *(inferred)*)
  3. All parameters: name, type, default value, what it controls
  4. Return value: type and what it represents
  5. All exceptions raised: type and the condition that triggers each
  6. Pre-conditions: what must be true before calling (from assertions, validation code)
  7. Side effects: state mutations, I/O, writes, external calls
  8. Minimal real usage example using exact names from source
- Skip private members (prefix `_`) unless called from the public interface.
- Group by file/module.

OUTPUT FORMAT — follow this hierarchy EXACTLY:

---

## API Reference

---

## Module: `path/to/file.py`

*(One sentence: this module's responsibility in the system.)*

---

### Class: `ClassName`

```python
class ClassName(BaseClass):
```

> *(Docstring verbatim — or inferred purpose marked *(inferred)*.)*

**Inherits from:** `BaseClass` *(or "None")*

**Constructor**

```python
def __init__(self, param1: Type1, param2: Type2 = default) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `param1` | `Type1` | — | *(what it controls)* |

**Instance Attributes**

| Attribute | Type | Set In | Description |
|-----------|------|--------|-------------|
| `self.attr` | `Type` | `__init__` | *(what it holds)* |

---

#### Method: `method_name()`

```python
def method_name(self, param: Type, flag: bool = False) -> ReturnType
```

> *(Docstring or inferred purpose.)*

**Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `param` | `Type` | — | *(description)* |

**Returns:** `ReturnType` — *(what it represents)*

**Raises:**
- `ExceptionType` — *(condition)*

**Pre-conditions:** *(what must be true before calling — or "None detected.")*

**Side effects:** *(mutations, I/O, external calls — or "None detected.")*

**Example**
```python
# Using real names from the source
obj = ClassName(actual_value)
result = obj.method_name(real_param)
```

---

### Function: `function_name()`

*(Same structure as Method, without `self`.)*

---

*(Repeat for EVERY item in the source context. Do not skip any.)*"""

        return self.llm.simple_prompt(prompt, system=SYSTEM_PROMPT, max_tokens=4096)

    def generate_architecture_doc(self, analysis: Dict) -> str:
        ctx = self._retrieve_context(
            "import from module pipeline flow inheritance composition dependency inject factory singleton abstract",
            top_k=8,
        )

        prompt = f"""Document the architecture and internal design of `{analysis['project_name']}`.

METADATA:
{_fmt_analysis(analysis)}

FILE TREE:
{analysis.get('file_tree', '(not available)')}

SOURCE CONTEXT (imports, class hierarchies, module relationships):
{ctx}

EXTRACTION RULES:
- Map EVERY module dependency from import statements visible in context.
- Trace the execution flow using real function/method names.
- Name design patterns ONLY if clearly implemented in the code.
- Describe the lifecycle of the primary object from creation to disposal.

OUTPUT — EXACTLY this structure:

## Architecture & Design

### System Responsibility Map
| Module / File | Responsibility | Owned Abstractions |
|---------------|----------------|-------------------|

### Dependency Graph
*(A → B means "A depends on B". Derived from import statements.)*
```
(plain-text dependency arrows)
```

### Execution Flow
*(Trace primary use case from entry point to result using exact function names.)*

1. **Entry:** `module.function()` — *(what triggers it)*
2. **Step:** `module.function()` — *(what happens)*
*(continue for each major step)*

### Design Patterns
| Pattern | Location | Evidence in Code |
|---------|----------|-----------------|
*(ONLY patterns directly observable. If none: "No canonical patterns detected.")*

### Key Design Decisions
*(5 bullets. Each explains WHY the code is structured this way — infer from naming, composition, layering. Mark each *(inferred)* if not from a comment.)*

### Directory Structure
```
{analysis.get('file_tree', '(not available)')}
```"""

        return self.llm.simple_prompt(prompt, system=SYSTEM_PROMPT, max_tokens=2000)

    def generate_usage_guide(self, analysis: Dict) -> str:
        ctx = self._retrieve_context(
            "example usage import instantiate call invoke __main__ demo test fixture client",
            top_k=10,
        )

        prompt = f"""Write the Usage Guide for `{analysis['project_name']}`.

METADATA:
{_fmt_analysis(analysis)}

SOURCE CONTEXT (call sites, examples, entry points, test fixtures):
{ctx}

RULES:
- Quick Start = MINIMUM sequence of real function calls to produce a result.
- Every code example must use EXACT class/function names from the context.
- NEVER write placeholder examples. Use real API names only.
- Each use case demonstrates a DISTINCT capability visible in source.
- Gotchas must come from observable code behavior.

OUTPUT — EXACTLY this structure:

## Usage Guide

### Quick Start

```python
from {analysis.get('project_name', 'module').replace('-','_').replace(' ','_')} import RealClassName

obj = RealClassName(real_param)
result = obj.real_method()
print(result)
```

### Use Case 1: *(name it after a specific capability)*

```python
# Complete runnable example
```

**What this does:**
- *(key behavior)*
- *(non-obvious detail or required ordering)*

### Use Case 2: *(name)*

```python
```

**What this does:**
- *(bullets)*

### Use Case 3: *(name)*

```python
```

**What this does:**
- *(bullets)*

*(Max 4 use cases. Only include if backed by the source context.)*

### Error Handling

```python
# Real exception types from source
```

| Exception | When It Occurs | How to Handle |
|-----------|---------------|---------------|

### Gotchas & Non-Obvious Behavior
- *(Real behavioral quirk from code: ordering, mutation, state requirement, etc.)*
- *(If none detectable: "No gotchas detected from source.")*"""

        return self.llm.simple_prompt(prompt, system=SYSTEM_PROMPT, max_tokens=2500)

    def generate_configuration_doc(self, analysis: Dict, files: List[Dict]) -> Optional[str]:
        config_files = [f for f in files if any(
            kw in f["path"].lower()
            for kw in [".env", "config", "settings", ".yaml", ".yml", ".toml", ".ini", ".cfg"]
        )]
        if not config_files:
            return None

        config_snippets = "\n\n".join(
            f"<!-- FILE: {f['path']} -->\n```\n{f['content'][:800]}\n```"
            for f in config_files[:6]
        )
        env_ctx = self._retrieve_context(
            "os.getenv os.environ getenv environ config settings default value required", top_k=6
        )

        prompt = f"""Document every configuration option for `{analysis.get('project_name', 'this project')}`.

CONFIGURATION FILES:
{config_snippets}

ENVIRONMENT VARIABLE USAGE IN SOURCE:
{env_ctx}

RULES:
- Document ONLY keys/variables present in the files or source context above.
- Default column: actual default from code or file. If none exists, write `—`.
- Type: infer from value format (string, int, bool, path, URL).
- Required = Yes if no default exists anywhere in code or config.
- If a key's purpose is unclear from its name, infer from surrounding code.

OUTPUT — EXACTLY this structure:

## Configuration

*(One table per configuration file.)*

### `(filename)`

| Key | Type | Default | Required | Description |
|-----|------|---------|----------|-------------|

### Environment Variables

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
*(One row per os.getenv call detected. Omit this section if none detected.)*

### Configuration Precedence
*(Which source takes priority if multiple exist? Infer from code loading order. If not determinable, say so.)*"""

        return self.llm.simple_prompt(prompt, system=SYSTEM_PROMPT, max_tokens=1500)


def _fmt_analysis(analysis: Dict) -> str:
    components = ", ".join(c.get("name", "") for c in analysis.get("key_components", [])[:8])
    return "\n".join([
        f"Project      : {analysis.get('project_name', 'unknown')}",
        f"Description  : {analysis.get('description', 'not available')}",
        f"Language     : {analysis.get('language', 'unknown')}",
        f"Framework    : {analysis.get('framework', 'unknown')}",
        f"Architecture : {analysis.get('architecture', 'unknown')}",
        f"Complexity   : {analysis.get('complexity', 'unknown')}",
        f"Features     : {', '.join(analysis.get('features', [])[:8]) or 'none detected'}",
        f"Components   : {components or 'none detected'}",
        f"Dependencies : {', '.join(analysis.get('dependencies', [])[:12]) or 'none detected'}",
        f"Entry Points : {', '.join(analysis.get('entry_points', [])[:5]) or 'none detected'}",
    ])