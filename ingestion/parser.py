import ast
import re


def _parse_python(source: str, file_path: str) -> list[dict]:
    units = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [{"type": "module", "name": file_path, "source": source, "file_path": file_path}]

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            units.append({
                "type": "function",
                "name": node.name,
                "source": ast.get_source_segment(source, node) or "",
                "file_path": file_path,
                "docstring": ast.get_docstring(node) or "",
                "args": [a.arg for a in node.args.args],
            })
        elif isinstance(node, ast.ClassDef):
            units.append({
                "type": "class",
                "name": node.name,
                "source": ast.get_source_segment(source, node) or "",
                "file_path": file_path,
                "docstring": ast.get_docstring(node) or "",
            })

    if not units:
        units.append({"type": "module", "name": file_path, "source": source, "file_path": file_path})
    return units


def _parse_generic(source: str, file_path: str, language: str) -> list[dict]:
    patterns = {
        "javascript": r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
        "typescript": r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
        "go": r"^func\s+(\w+)\s*\(",
        "java": r"(?:public|private|protected|static|final|\s)+[\w<>\[\]]+\s+(\w+)\s*\(",
        "ruby": r"def\s+(\w+)",
        "rust": r"(?:pub\s+)?fn\s+(\w+)\s*\(",
    }
    pattern = patterns.get(language)
    units = []
    if pattern:
        lines = source.splitlines()
        for i, line in enumerate(lines):
            m = re.search(pattern, line, re.MULTILINE)
            if m:
                snippet = "\n".join(lines[i: i + 30])
                units.append({
                    "type": "function",
                    "name": m.group(1),
                    "source": snippet,
                    "file_path": file_path,
                    "docstring": "",
                    "args": [],
                })
    if not units:
        units.append({"type": "module", "name": file_path, "source": source, "file_path": file_path})
    return units


def parse_file(file_info: dict) -> list[dict]:
    source = file_info["source"]
    path = file_info["path"]
    language = file_info["language"]

    if language == "py":
        return _parse_python(source, path)
    return _parse_generic(source, path, language)


def parse_files(files: list[dict]) -> list[dict]:
    units = []
    for f in files:
        units.extend(parse_file(f))
    return [u for u in units if u.get("source", "").strip()]