import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# ── Hugging Face Inference Router ─────────────────────────────────────────────
HF_TOKEN: str = os.getenv("HF_TOKEN", "")
HF_BASE_URL: str = "https://router.huggingface.co/v1"

# Set any HF-hosted chat model here — never hardcoded in logic files.
# Examples:
#   "Qwen/Qwen3-8B:fireworks-ai"
#   "meta-llama/Llama-3.1-8B-Instruct:fireworks-ai"
#   "microsoft/Phi-3-mini-4k-instruct"
CHAT_MODEL: str = os.getenv("CHAT_MODEL", "Qwen/Qwen3-8B:fireworks-ai")

LLM_TEMPERATURE: float = 0.3
MAX_TOKENS_RESPONSE: int = 2048

# ── Embeddings (local, no API key needed) ─────────────────────────────────────
EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

# ── ChromaDB ──────────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")
CHROMA_COLLECTION: str = "sdk_docs"

# ── Ingestion ─────────────────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS: list[str] = [".py", ".ts", ".js", ".go", ".java", ".rb", ".rs"]
CHUNK_SIZE: int = 512
CHUNK_OVERLAP: int = 64
CLONE_DIR: str = str(BASE_DIR / "data" / "repos")

# ── RAG ───────────────────────────────────────────────────────────────────────
TOP_K_RESULTS: int = 8

# ── Validation ────────────────────────────────────────────────────────────────
if not HF_TOKEN:
    raise EnvironmentError(
        "HF_TOKEN is not set. Add it to your .env file.\n"
        "Get your token at: https://huggingface.co/settings/tokens"
    )