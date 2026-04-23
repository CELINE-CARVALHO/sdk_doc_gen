"""
GitHub loader — fetches source files via GitHub REST API (no git clone).
Requires no git installation. Works with any public repo.
For private repos, set GITHUB_TOKEN in .env.
"""

import os
import base64
import requests
from config import SUPPORTED_EXTENSIONS

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    _HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def _parse_owner_repo(repo_url: str) -> tuple[str, str]:
    parts = repo_url.rstrip("/").replace(".git", "").split("/")
    try:
        idx = parts.index("github.com")
        return parts[idx + 1], parts[idx + 2]
    except (ValueError, IndexError):
        raise ValueError(f"Cannot parse GitHub URL: {repo_url}")


def _get_default_branch(owner: str, repo: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(url, headers=_HEADERS, timeout=15)
    r.raise_for_status()
    return r.json().get("default_branch", "main")


def _get_file_tree(owner: str, repo: str, branch: str) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    r = requests.get(url, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("truncated"):
        print("Warning: repo tree truncated by GitHub API (very large repo).")
    return [
        item for item in data.get("tree", [])
        if item["type"] == "blob"
        and any(item["path"].endswith(ext) for ext in SUPPORTED_EXTENSIONS)
        and not any(part.startswith(".") for part in item["path"].split("/"))
    ]


def _fetch_file(owner: str, repo: str, path: str) -> str | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=_HEADERS, timeout=15)
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return data.get("content", "")


def load_repo(repo_url: str) -> list[dict]:
    owner, repo = _parse_owner_repo(repo_url)
    branch = _get_default_branch(owner, repo)
    tree = _get_file_tree(owner, repo, branch)

    files = []
    for item in tree:
        source = _fetch_file(owner, repo, item["path"])
        if source and source.strip():
            ext = "." + item["path"].rsplit(".", 1)[-1]
            files.append({
                "path": item["path"],
                "source": source,
                "language": ext.lstrip("."),
            })

    return files