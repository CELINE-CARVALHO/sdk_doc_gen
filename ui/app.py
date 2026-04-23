import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from agent.orchestrator import run_pipeline

st.set_page_config(page_title="SDK Doc Generator", page_icon="📄", layout="wide")

st.title("📄 AI SDK Documentation Generator")
st.caption("Powered by OpenAI · ChromaDB · Multi-Agent Pipeline")

with st.sidebar:
    st.header("Settings")
    force_reindex = st.toggle("Force re-index", value=False, help="Clear and rebuild the vector store for this run")
    st.divider()
    st.markdown("**How it works**")
    st.markdown(
        "1. Clones the GitHub repo\n"
        "2. Parses & chunks code\n"
        "3. Embeds into ChromaDB\n"
        "4. Analyzes public API\n"
        "5. Generates Markdown docs"
    )

repo_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/owner/repo",
    help="Public GitHub repository URL",
)

col1, col2 = st.columns([1, 5])
with col1:
    generate = st.button("Generate Docs", type="primary", disabled=not repo_url.strip())

if generate and repo_url.strip():
    log_container = st.empty()
    progress_lines: list[str] = []

    def update_log(msg: str):
        progress_lines.append(msg)
        log_container.info("\n".join(f"• {l}" for l in progress_lines))

    with st.spinner("Running pipeline..."):
        try:
            doc = run_pipeline(
                repo_url=repo_url.strip(),
                force_reindex=force_reindex,
                progress_callback=update_log,
            )
            log_container.empty()
            st.success("Documentation generated successfully.")

            tab_preview, tab_raw = st.tabs(["Preview", "Raw Markdown"])
            with tab_preview:
                st.markdown(doc)
            with tab_raw:
                st.code(doc, language="markdown")

            st.download_button(
                label="Download Markdown",
                data=doc,
                file_name="sdk_documentation.md",
                mime="text/markdown",
            )
        except Exception as e:
            log_container.empty()
            st.error(f"Pipeline failed: {e}")