"""
Build SFT dataset from code in the repo (no API key). Scans directories for code files
and turns each into a user/assistant message pair for local training.

Usage (from repo root):
  python scripts/build_dataset_from_repo.py --root . --out data/processed/repo_code_sft.jsonl
  python scripts/build_dataset_from_repo.py --root /path/to/GitTime --out data/processed/repo_code_sft.jsonl

Then train locally (no API key):
  python training/run_sft.py --dataset data/processed/repo_code_sft.jsonl --output_dir training/output
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Extensions to include as code (treatreport, Solvency2 ticket, mini-chatgpt-coding, etc.)
CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".html", ".css", ".scss", ".md", ".json", ".yaml", ".yml",
    ".sh", ".bash", ".sql", ".go", ".rs", ".java", ".kt",
    ".cshtml", ".cs", ".vb", ".fs",
}

# Directories to skip (no API key, just local paths)
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".next", "venv", ".venv",
    "dist", "build", ".cache", "coverage", ".pytest_cache", ".cursor",
}


def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS or part.startswith(".") and part != ".env.example":
            return True
    return False


def collect_code_files(root: Path, max_file_size: int = 100_000) -> list[tuple[Path, str]]:
    """Return list of (path, content) for code files under root."""
    out = []
    root = root.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path):
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(content) > max_file_size:
            content = content[:max_file_size] + "\n# ... truncated\n"
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        out.append((rel, content))
    return out


def file_to_messages(rel_path: Path, content: str) -> dict:
    """One code file -> one SFT example (messages format)."""
    path_str = str(rel_path).replace("\\", "/")
    instruction = f"Write or implement the code for {path_str}."
    return {
        "messages": [
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": content.strip() or "(empty file)"},
        ]
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build SFT JSONL from repo code (no API key)"
    )
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="Root directory to scan (default: GitTime workspace parent of mini-chatgpt-coding)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/repo_code_sft.jsonl"),
        help="Output JSONL path",
    )
    ap.add_argument(
        "--max-size",
        type=int,
        default=100_000,
        help="Max chars per file (default 100000)",
    )
    args = ap.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    files = collect_code_files(root, max_file_size=args.max_size)
    if not files:
        print("No code files found under", root, file=sys.stderr)
        sys.exit(1)

    out_path = args.out
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parent.parent / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for rel, content in files:
            rec = file_to_messages(rel, content)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    print(f"Wrote {count} examples to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
