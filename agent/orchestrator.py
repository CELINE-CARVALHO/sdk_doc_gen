from ingestion.github_loader import load_repo
from ingestion.parser import parse_files
from ingestion.chunker import chunk_units
from rag.vectordb import index_chunks, query_similar, clear_collection
from agent.analyzer import analyze
from agent.retriever import retrieve_context
from agent.writer import write_symbol_doc, write_overview


def run_pipeline(
    repo_url: str,
    force_reindex: bool = False,
    progress_callback=None,
) -> str:
    def _log(msg: str):
        if progress_callback:
            progress_callback(msg)

    _log("Fetching repository file list via GitHub API...")
    files = load_repo(repo_url)
    _log(f"Fetched {len(files)} source files (no clone — API only).")

    _log("Parsing source files...")
    units = parse_files(files)
    _log(f"Parsed {len(units)} code units.")

    _log("Chunking code units...")
    chunks = chunk_units(units)
    _log(f"Created {len(chunks)} chunks.")

    if force_reindex:
        _log("Clearing existing index...")
        clear_collection()

    _log("Indexing into ChromaDB...")
    indexed = index_chunks(chunks)
    _log(f"Indexed {indexed} chunks.")

    _log("Analyzing codebase...")
    sample = query_similar("public API functions classes", top_k=20)
    analysis = analyze(sample)
    _log(f"Detected language: {analysis.get('language', 'unknown')} | "
         f"Found {len(analysis.get('public_api', []))} public symbols.")

    _log("Retrieving context for each symbol...")
    symbol_context = retrieve_context(analysis)

    _log("Writing documentation...")
    sections = [write_overview(analysis, repo_url=repo_url)]

    sections.append("---\n\n## 9. API Reference 📘\n")

    for symbol, ctx in symbol_context.items():
        _log(f"  ↳ {symbol}")
        sections.append(write_symbol_doc(symbol, ctx, analysis))

    sections.append(_build_footer(analysis))

    doc = "\n\n".join(sections)
    _log("Done.")
    return doc


def _build_footer(analysis: dict) -> str:
    return """---

## 10. Best Practices ✅

- Keep inputs focused and specific
- Handle errors with try/except around all SDK calls
- Check token/rate limits before bulk operations
- Use streaming for long-running generations

---

## 11. Troubleshooting 🛠️

**Output is cut off** → Increase `max_tokens`

**Output too random** → Lower `temperature` (try `0.3`)

**Rate limit error** → Add retry logic with exponential backoff

---

## 12. License 📄

See repository for license details.
"""