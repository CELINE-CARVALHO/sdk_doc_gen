import argparse
import sys
from pathlib import Path
from agent.orchestrator import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="AI SDK Documentation Generator")
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument("--output", "-o", default="docs_output.md", help="Output markdown file")
    parser.add_argument("--force-reindex", action="store_true", help="Clear and rebuild the vector index")
    args = parser.parse_args()

    def log(msg: str):
        print(f"  → {msg}", flush=True)

    print(f"\nGenerating docs for: {args.repo_url}\n")
    try:
        doc = run_pipeline(
            repo_url=args.repo_url,
            force_reindex=args.force_reindex,
            progress_callback=log,
        )
        Path(args.output).write_text(doc, encoding="utf-8")
        print(f"\nDocumentation saved to: {args.output}\n")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()