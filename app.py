"""
app.py
Streamlit UI for the Agentic Documentation Generator.
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic Doc Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');

    :root {
        --bg-base: #070d1a;
        --bg-surface: #0d1526;
        --bg-elevated: #111d33;
        --bg-card: #131f38;
        --border: #1c2d4a;
        --border-bright: #243d60;
        --text-primary: #e8effc;
        --text-secondary: #8ba3c7;
        --text-muted: #4a6484;
        --accent: #3b82f6;
        --accent-glow: rgba(59,130,246,0.18);
        --accent-2: #0ea5e9;
        --success: #22c55e;
        --success-bg: rgba(34,197,94,0.08);
        --error: #f87171;
        --error-bg: rgba(248,113,113,0.08);
        --warning: #fbbf24;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
        background: var(--bg-base) !important;
    }

    /* ── Global page bg ── */
    .stApp {
        background: var(--bg-base) !important;
        background-image:
            radial-gradient(ellipse 80% 40% at 50% -10%, rgba(59,130,246,0.12) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 90% 60%, rgba(14,165,233,0.06) 0%, transparent 60%);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg-surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1rem;
    }
    [data-testid="stSidebar"] * { color: var(--text-secondary) !important; }
    [data-testid="stSidebar"] h3 { color: var(--text-primary) !important; font-family: 'Syne', sans-serif !important; font-size: 0.9rem !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }

    /* ── Main container ── */
    .main .block-container {
        padding: 2.5rem 3rem 4rem !important;
        max-width: 980px !important;
    }

    /* ── Typography ── */
    h1, h2, h3 { color: var(--text-primary) !important; }

    /* ── Radio buttons ── */
    .stRadio > label { color: var(--text-secondary) !important; font-size: 0.85rem !important; }
    .stRadio [data-testid="stMarkdownContainer"] p { color: var(--text-secondary) !important; }
    div[role="radiogroup"] label {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 0.55rem 1.1rem !important;
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        transition: all 0.18s ease !important;
        cursor: pointer !important;
    }
    div[role="radiogroup"] label:hover {
        border-color: var(--accent) !important;
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
    }

    /* ── Inputs ── */
    .stTextInput input, .stTextArea textarea {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 0.9rem !important;
        transition: border-color 0.18s ease !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
        outline: none !important;
    }
    .stTextInput input::placeholder { color: var(--text-muted) !important; }
    .stTextInput label, .stTextArea label { color: var(--text-secondary) !important; font-size: 0.82rem !important; font-weight: 500 !important; letter-spacing: 0.02em !important; }

    /* ── File uploader ── */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--bg-elevated) !important;
        border: 1.5px dashed var(--border-bright) !important;
        border-radius: 14px !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: var(--accent) !important;
        background: var(--bg-card) !important;
    }
    [data-testid="stFileUploaderDropzone"] * { color: var(--text-secondary) !important; }

    /* ── Buttons ── */
    .stButton button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.88rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.18s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3), 0 0 0 0 var(--accent-glow) !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(37,99,235,0.4), 0 1px 3px rgba(0,0,0,0.2) !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    }
    .stButton button:active { transform: translateY(0) !important; }

    /* Generate button — larger */
    [data-testid="baseButton-secondary"]:last-of-type button,
    .generate-btn .stButton button {
        padding: 0.75rem 2rem !important;
        font-size: 0.95rem !important;
    }

    /* ── Download button ── */
    .stDownloadButton button {
        background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.18s ease !important;
    }
    .stDownloadButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(13,148,136,0.4) !important;
    }

    /* ── Progress bar ── */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #2563eb, #0ea5e9) !important;
        border-radius: 9999px !important;
    }
    .stProgress > div > div {
        background: var(--border) !important;
        border-radius: 9999px !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted) !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 0 !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.18s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text-primary) !important; }
    .stTabs [aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 0 0 14px 14px !important;
        padding: 1.5rem !important;
    }

    /* ── Code block ── */
    .stCodeBlock {
        background: var(--bg-surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }
    pre { background: transparent !important; }

    /* ── Caption ── */
    .stCaption { color: var(--text-muted) !important; font-size: 0.78rem !important; }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-secondary) !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
    }

    /* ── Info / Success / Warning ── */
    .stInfo, div[data-testid="stNotification"] {
        background: rgba(59,130,246,0.08) !important;
        border: 1px solid rgba(59,130,246,0.25) !important;
        border-radius: 10px !important;
        color: var(--text-secondary) !important;
    }
    .stWarning {
        background: rgba(251,191,36,0.07) !important;
        border: 1px solid rgba(251,191,36,0.22) !important;
        border-radius: 10px !important;
    }
    .stSuccess {
        background: var(--success-bg) !important;
        border: 1px solid rgba(34,197,94,0.25) !important;
        border-radius: 10px !important;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu, footer, header { visibility: hidden; }
    .viewerBadge_container__1QSob { display: none !important; }

    /* ── Custom components ── */

    .hero-wrap {
        text-align: center;
        padding: 3.5rem 1rem 2.5rem;
    }
    .hero-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(59,130,246,0.1);
        border: 1px solid rgba(59,130,246,0.25);
        border-radius: 9999px;
        padding: 0.28rem 0.9rem;
        font-size: 0.72rem;
        font-weight: 600;
        color: #60a5fa;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1.2rem;
    }
    .hero-title {
        font-family: 'Syne', sans-serif;
        font-size: 3.4rem;
        font-weight: 800;
        line-height: 1.05;
        letter-spacing: -0.03em;
        color: var(--text-primary);
        margin-bottom: 0.6rem;
    }
    .hero-title span {
        background: linear-gradient(120deg, #3b82f6 0%, #0ea5e9 50%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-sub {
        color: var(--text-secondary);
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 2rem;
        max-width: 480px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }
    .pill-row { display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: center; }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.3rem 0.75rem;
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: 9999px;
        font-size: 0.77rem;
        color: var(--text-secondary);
        font-weight: 500;
    }

    .section-label {
        font-family: 'Syne', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-label::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    .card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.6rem 1.75rem;
        margin-bottom: 1.25rem;
        position: relative;
        overflow: hidden;
    }
    .card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59,130,246,0.3), transparent);
    }
    .card-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .card-desc {
        font-size: 0.81rem;
        color: var(--text-muted);
        margin-bottom: 1.1rem;
    }

    .agent-row { display: flex; flex-direction: column; gap: 0.6rem; margin-top: 0.5rem; }
    .agent-item {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.5rem 0.75rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    .agent-dot {
        width: 7px; height: 7px;
        border-radius: 9999px;
        flex-shrink: 0;
    }
    .dot-blue { background: #3b82f6; box-shadow: 0 0 5px #3b82f6; }
    .dot-purple { background: #8b5cf6; box-shadow: 0 0 5px #8b5cf6; }
    .dot-green { background: #22c55e; box-shadow: 0 0 5px #22c55e; }
    .dot-orange { background: #f59e0b; box-shadow: 0 0 5px #f59e0b; }
    .agent-name { font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); }
    .agent-desc { font-size: 0.73rem; color: var(--text-muted); margin-left: auto; }

    .fmt-card {
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.18s ease;
    }
    .fmt-card.active {
        border-color: var(--accent);
        background: rgba(59,130,246,0.07);
    }
    .fmt-card:hover { border-color: var(--border-bright); }
    .fmt-icon { font-size: 1.4rem; margin-bottom: 0.35rem; }
    .fmt-title { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
    .fmt-desc { font-size: 0.73rem; color: var(--text-muted); margin-top: 0.15rem; }

    .status-log {
        background: var(--bg-surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        font-family: 'DM Mono', monospace;
        font-size: 0.78rem;
        color: var(--text-secondary);
        line-height: 1.7;
        max-height: 200px;
        overflow-y: auto;
    }
    .status-log .log-line { display: flex; gap: 0.5rem; }
    .log-arrow { color: #3b82f6; }

    .banner-success {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        background: var(--success-bg);
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 12px;
        padding: 0.9rem 1.25rem;
        color: #86efac;
        font-weight: 500;
        font-size: 0.9rem;
        margin: 1rem 0;
    }
    .banner-error {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        background: var(--error-bg);
        border: 1px solid rgba(248,113,113,0.3);
        border-radius: 12px;
        padding: 0.9rem 1.25rem;
        color: #fca5a5;
        font-weight: 500;
        font-size: 0.9rem;
        margin: 1rem 0;
    }

    .divider {
        height: 1px;
        background: var(--border);
        margin: 1.75rem 0;
    }

    .stat-bar {
        display: flex;
        gap: 1.5rem;
        align-items: center;
        padding: 0.6rem 1rem;
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: 9px;
        font-size: 0.78rem;
        color: var(--text-muted);
    }
    .stat-item { display: flex; align-items: center; gap: 0.35rem; }
    .stat-item b { color: var(--text-secondary); }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ──────────────────────────────────────────────────────────

def get_api_key() -> Optional[str]:
    """Get Groq API key from env or session state."""
    return st.session_state.get("groq_api_key") or os.getenv("GROQ_API_KEY")


def render_status_log(messages: list):
    """Render a scrollable status log."""
    if not messages:
        return
    lines = "".join(
        f'<div class="log-line"><span class="log-arrow">▶</span><span>{m}</span></div>'
        for m in messages
    )
    st.markdown(f'<div class="status-log">{lines}</div>', unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1.5rem;">
            <span style="font-size:1.3rem;">⚡</span>
            <span style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;color:#e8effc;letter-spacing:-0.01em;">DocGen</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<p class="section-label">API Key</p>', unsafe_allow_html=True)

        api_key_env = os.getenv("GROQ_API_KEY", "")
        if api_key_env:
            st.markdown("""
            <div style="display:flex;align-items:center;gap:0.5rem;background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);border-radius:8px;padding:0.55rem 0.8rem;font-size:0.8rem;color:#86efac;margin-bottom:1rem;">
                <span>✓</span><span>GROQ_API_KEY loaded</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            key_input = st.text_input(
                "Groq API Key",
                type="password",
                placeholder="gsk_...",
                help="Get your key at console.groq.com",
            )
            if key_input:
                st.session_state["groq_api_key"] = key_input

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p class="section-label">AI Agents</p>', unsafe_allow_html=True)

        st.markdown("""
        <div class="agent-row">
            <div class="agent-item">
                <div class="agent-dot dot-blue"></div>
                <span class="agent-name">Analyzer</span>
                <span class="agent-desc">Understands code</span>
            </div>
            <div class="agent-item">
                <div class="agent-dot dot-purple"></div>
                <span class="agent-name">DocGen</span>
                <span class="agent-desc">Writes docs</span>
            </div>
            <div class="agent-item">
                <div class="agent-dot dot-green"></div>
                <span class="agent-name">Examples</span>
                <span class="agent-desc">Creates examples</span>
            </div>
            <div class="agent-item">
                <div class="agent-dot dot-orange"></div>
                <span class="agent-name">Validator</span>
                <span class="agent-desc">Improves quality</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p class="section-label">Output Formats</p>', unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex;flex-direction:column;gap:0.4rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.8rem;color:#8ba3c7;">
                <span>📝</span><span>Markdown — Raw <code style="background:#1c2d4a;padding:0.1rem 0.3rem;border-radius:4px;font-size:0.73rem;">.md</code> file</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.8rem;color:#8ba3c7;">
                <span>🌐</span><span>HTML — Interactive docs site</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.8rem;color:#8ba3c7;">
                <span>🗂️</span><span>JSON — Structured data</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.caption("Powered by Groq LLM + RAG")


# ── Main UI ───────────────────────────────────────────────────────────────────

def main():
    render_sidebar()

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-eyebrow">⚡ AI-powered · Multi-agent · RAG-enhanced</div>
        <div class="hero-title">Generate <span>Professional Docs</span><br>from Any Codebase</div>
        <div class="hero-sub">Upload your source code and let AI agents analyze, write, and validate production-ready documentation.</div>
        <div class="pill-row">
            <span class="pill">🔍 RAG-enhanced</span>
            <span class="pill">🤖 Multi-agent</span>
            <span class="pill">⚡ Groq LLM</span>
            <span class="pill">🌐 Interactive HTML</span>
            <span class="pill">📦 ZIP / Files / Git</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Input section ─────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">01 · Input Source</p>', unsafe_allow_html=True)

    input_type = st.radio(
        "Select input method:",
        ["📦 ZIP File", "📄 Individual Files", "🔗 Git Repository"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    files = None
    project_name = "my_project"
    ingest_error = None

    # ── ZIP Upload ────────────────────────────────────────────────────────────
    if input_type == "📦 ZIP File":
        st.markdown("""
        <div class="card">
            <div class="card-title">📦 Upload ZIP Archive</div>
            <div class="card-desc">Upload a .zip file containing your project source code.</div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            zip_file = st.file_uploader(
                "Choose a ZIP file",
                type=["zip"],
                label_visibility="collapsed",
            )
            if zip_file:
                project_name = Path(zip_file.name).stem
                st.info(f"📦 Ready: **{zip_file.name}** — {zip_file.size:,} bytes")

    # ── Individual Files ──────────────────────────────────────────────────────
    elif input_type == "📄 Individual Files":
        st.markdown("""
        <div class="card">
            <div class="card-title">📄 Upload Source Files</div>
            <div class="card-desc">Upload one or more source code files directly.</div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            uploaded_files = st.file_uploader(
                "Choose files",
                accept_multiple_files=True,
                label_visibility="collapsed",
            )
            if uploaded_files:
                st.info(f"📄 {len(uploaded_files)} file(s) selected: {', '.join(f.name for f in uploaded_files[:5])}")
            project_name = st.text_input("Project name", value="my_project", placeholder="my_project")

    # ── Git Repository ────────────────────────────────────────────────────────
    elif input_type == "🔗 Git Repository":
        st.markdown("""
        <div class="card">
            <div class="card-title">🔗 Clone Git Repository</div>
            <div class="card-desc">Provide a public or private repository URL to clone and document.</div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                repo_url = st.text_input(
                    "Repository URL",
                    placeholder="https://github.com/owner/repository",
                )
            with col2:
                branch = st.text_input("Branch (optional)", placeholder="main")

            git_token = st.text_input(
                "🔒 Git Token (for private repos)",
                type="password",
                placeholder="ghp_... (optional)",
                help="GitHub Personal Access Token for private repositories",
            )

            if not git_token:
                git_token = os.getenv("GIT_TOKEN")

            if repo_url:
                st.info(f"🔗 Repository: `{repo_url}`" + (f" · branch: `{branch}`" if branch else ""))

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Output format ──────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">02 · Output Format</p>', unsafe_allow_html=True)

    if "output_format" not in st.session_state:
        st.session_state["output_format"] = "markdown"

    fmt_col1, fmt_col2, fmt_col3 = st.columns(3)
    with fmt_col1:
        md_selected = st.button("📝 Markdown", use_container_width=True)
    with fmt_col2:
        html_selected = st.button("🌐 HTML (Interactive)", use_container_width=True)
    with fmt_col3:
        json_selected = st.button("🗂️ JSON", use_container_width=True)

    if md_selected:
        st.session_state["output_format"] = "markdown"
    elif html_selected:
        st.session_state["output_format"] = "html"
    elif json_selected:
        st.session_state["output_format"] = "json"

    fmt = st.session_state["output_format"]
    fmt_labels = {"markdown": "📝 Markdown", "html": "🌐 HTML (Interactive)", "json": "🗂️ JSON"}
    fmt_descs = {"markdown": "Raw .md file, ideal for GitHub READMEs", "html": "Standalone interactive docs site", "json": "Structured data for programmatic use"}

    st.markdown(f"""
    <div style="margin-top:0.75rem;display:flex;align-items:center;gap:0.75rem;padding:0.65rem 1rem;background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.2);border-radius:10px;">
        <span style="font-size:1.1rem;">{fmt_labels[fmt].split()[0]}</span>
        <div>
            <div style="font-size:0.85rem;font-weight:600;color:#e8effc;">{fmt_labels[fmt]}</div>
            <div style="font-size:0.76rem;color:#4a6484;">{fmt_descs[fmt]}</div>
        </div>
        <span style="margin-left:auto;font-size:0.72rem;color:#3b82f6;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">Selected</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Generate button ────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">03 · Generate</p>', unsafe_allow_html=True)

    api_key = get_api_key()
    if not api_key:
        st.warning("⚠️ No Groq API key found. Add `GROQ_API_KEY` to your `.env` file or enter it in the sidebar.")

    generate_btn = st.button(
        "⚡ Generate Documentation",
        use_container_width=True,
        disabled=not api_key,
    )

    # ── Pipeline execution ─────────────────────────────────────────────────────
    if generate_btn:
        if api_key and not api_key.startswith("gsk_"):
            st.warning("⚠️ Groq API keys typically start with 'gsk_'. Proceeding anyway...")

        status_messages = []
        progress_bar = st.progress(0)
        status_placeholder = st.empty()

        def update_progress(msg: str, pct: int):
            status_messages.append(msg)
            progress_bar.progress(pct / 100)
            with status_placeholder.container():
                render_status_log(status_messages[-8:])

        try:
            from ingestion.ingestor import Ingestor
            from pipeline import DocumentationPipeline

            ingestor = Ingestor()

            update_progress("Ingesting source files...", 2)

            if input_type == "📦 ZIP File":
                if not zip_file:
                    st.error("❌ Please upload a ZIP file first.")
                    st.stop()
                files, project_name = ingestor.ingest_zip(zip_file.read())

            elif input_type == "📄 Individual Files":
                if not uploaded_files:
                    st.error("❌ Please upload at least one file.")
                    st.stop()
                files, _ = ingestor.ingest_files(uploaded_files)
                if not project_name.strip():
                    project_name = "my_project"

            elif input_type == "🔗 Git Repository":
                if not repo_url:
                    st.error("❌ Please enter a repository URL.")
                    st.stop()
                files, project_name = ingestor.ingest_git(
                    repo_url=repo_url,
                    branch=branch if branch else None,
                    token=git_token if git_token else None,
                )

            update_progress(f"✅ Ingested {len(files)} files from '{project_name}'", 5)

            pipeline = DocumentationPipeline(groq_api_key=api_key)

            result = pipeline.run(
                files=files,
                project_name=project_name,
                output_format=fmt,
                progress_callback=update_progress,
            )

            st.session_state["generated_doc"] = result
            st.session_state["generated_fmt"] = fmt
            st.session_state["generated_project"] = project_name

            ingestor.cleanup()

            progress_bar.progress(1.0)
            st.markdown(
                '<div class="banner-success"><span>✓</span><span>Documentation generated successfully!</span></div>',
                unsafe_allow_html=True,
            )

        except ValueError as e:
            st.markdown(f'<div class="banner-error"><span>✕</span><span>Input Error: {e}</span></div>', unsafe_allow_html=True)
            logger.error(f"Input error: {e}")
        except RuntimeError as e:
            if "authentication" in str(e).lower() or "401" in str(e) or "403" in str(e):
                st.markdown(
                    '<div class="banner-error"><span>✕</span><span>Groq API authentication failed. Check your GROQ_API_KEY.</span></div>',
                    unsafe_allow_html=True,
                )
            elif "rate" in str(e).lower():
                st.markdown(
                    '<div class="banner-error"><span>⚠</span><span>Groq rate limit hit. Please wait a moment and try again.</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<div class="banner-error"><span>✕</span><span>LLM Error: {e}</span></div>', unsafe_allow_html=True)
            logger.error(f"Runtime error: {e}\n{traceback.format_exc()}")
        except Exception as e:
            st.markdown(
                f'<div class="banner-error"><span>✕</span><span>Unexpected error: {e}</span></div>',
                unsafe_allow_html=True,
            )
            with st.expander("🔍 Error details"):
                st.code(traceback.format_exc())
            logger.error(f"Unexpected: {e}\n{traceback.format_exc()}")

    # ── Result display ─────────────────────────────────────────────────────────
    if "generated_doc" in st.session_state:
        doc = st.session_state["generated_doc"]
        doc_fmt = st.session_state["generated_fmt"]
        doc_project = st.session_state["generated_project"]

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p class="section-label">04 · Output</p>', unsafe_allow_html=True)

        ext_map = {"markdown": "md", "html": "html", "json": "json"}
        mime_map = {
            "markdown": "text/markdown",
            "html": "text/html",
            "json": "application/json",
        }
        filename = f"{doc_project}_docs.{ext_map[doc_fmt]}"

        col_dl, col_clear = st.columns([4, 1])
        with col_dl:
            st.download_button(
                label=f"⬇️ Download {ext_map[doc_fmt].upper()}",
                data=doc.encode("utf-8"),
                file_name=filename,
                mime=mime_map[doc_fmt],
                use_container_width=True,
            )
        with col_clear:
            if st.button("🗑️ Clear", use_container_width=True):
                del st.session_state["generated_doc"]
                del st.session_state["generated_fmt"]
                del st.session_state["generated_project"]
                st.rerun()

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["👁️ Preview", "📋 Raw Source"])

        with tab1:
            if doc_fmt == "html":
                st.markdown("*Rendering interactive HTML preview:*")
                st.components.v1.html(doc, height=700, scrolling=True)
            elif doc_fmt == "markdown":
                st.markdown(doc)
            else:
                st.json(doc)

        with tab2:
            st.code(doc, language=doc_fmt if doc_fmt != "markdown" else "markdown", line_numbers=True)

        st.markdown(f"""
        <div class="stat-bar" style="margin-top:0.75rem;">
            <div class="stat-item">📄 <b>{len(doc):,}</b> characters</div>
            <div class="stat-item">📏 <b>{len(doc.splitlines()):,}</b> lines</div>
            <div class="stat-item">🗂️ Format: <b>{doc_fmt.upper()}</b></div>
            <div class="stat-item">📁 File: <b>{filename}</b></div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()