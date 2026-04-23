# sdk_doc_gen
# AI SDK Documentation Generator

A production-grade system that ingests GitHub repositories and generates structured SDK documentation using a multi-agent AI pipeline.

## Architecture

```
sdk_doc_gen/
├── config.py                  # Central configuration & env loading
├── main.py                    # CLI entry point
├── requirements.txt
├── .env.example
│
├── ingestion/
│   ├── github_loader.py       # Clone/pull repos, collect source files
│   ├── parser.py              # Extract functions & classes per language
│   └── chunker.py             # Token-aware chunking with overlap
│
├── rag/
│   ├── embeddings.py          # OpenAI text-embedding-3-small wrapper
│   └── vectordb.py            # ChromaDB upsert, query, clear
│
├── agent/
│   ├── analyzer.py            # Summarize codebase, detect public API
│   ├── retriever.py           # RAG retrieval per symbol
│   ├── writer.py              # Generate Markdown docs per symbol
│   └── orchestrator.py        # Full pipeline coordinator
│
├── ui/
│   └── app.py                 # Streamlit frontend
│
└── data/
    ├── repos/                 # Cloned repositories (git-ignored)
    └── chroma_db/             # Persistent vector store (git-ignored)
```

## Pipeline

```
GitHub URL
    → github_loader   (clone + collect files)
    → parser          (extract functions/classes)
    → chunker         (token-aware chunks)
    → vectordb        (embed + upsert to ChromaDB)
    → analyzer        (GPT-4o-mini: summarize + identify public API)
    → retriever       (RAG: top-k chunks per symbol)
    → writer          (GPT-4o-mini: write docs per symbol)
    → Markdown output
```

## Setup

```bash
# 1. Clone this repo
git clone <this-repo>
cd sdk_doc_gen

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
cp .env.example .env
# Edit .env and add your key:
# OPENAI_API_KEY=sk-...
```

## Run

### Streamlit UI (recommended)
```bash
streamlit run ui/app.py
```
Open http://localhost:8501, paste a GitHub URL, click **Generate Docs**.

### CLI
```bash
python main.py https://github.com/owner/repo --output docs.md

# Force re-index (clears ChromaDB for this collection):
python main.py https://github.com/owner/repo --force-reindex
```

## Configuration (`config.py`)

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `CHAT_MODEL` | `gpt-4o-mini` | OpenAI chat model |
| `CHUNK_SIZE` | `512` | Tokens per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap tokens between chunks |
| `TOP_K_RESULTS` | `8` | RAG results per symbol query |

## Scaling Improvements

**Parallelism**
- Use `concurrent.futures.ThreadPoolExecutor` in `retriever.py` and `writer.py` to process symbols concurrently — the current loop is sequential.

**Incremental indexing**
- Store a file hash manifest in `data/` and skip re-embedding unchanged files instead of always calling `force_reindex`.

**Model upgrade path**
- Swap `gpt-4o-mini` → `gpt-4o` in `config.py` for higher-quality docs on large or complex codebases.

**Caching**
- Cache `analyzer.analyze()` results to disk (e.g. `joblib.Memory`) so repeated runs on the same repo skip the analysis step.

**Rate limiting**
- The `tenacity` retry decorator is already on embeddings. Add it to `writer.py` completions calls too for robustness under high load.

**Namespace isolation**
- Pass a per-repo ChromaDB collection name (derived from repo URL hash) so multiple repos coexist in the same vector store without collision.
