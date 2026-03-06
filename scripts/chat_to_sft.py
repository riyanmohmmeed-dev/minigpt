"""
Harvest conversation artifacts (implementation plans, fix guides, walkthroughs,
code demos) from the Antigravity brain directory and convert them into SFT
training examples.

Each markdown artifact becomes one or more user/assistant pairs:
  - The title/heading becomes the user's instruction.
  - The body (code blocks, explanations, analysis) becomes the assistant's
    response.

Usage (from repo root):
  python scripts/chat_to_sft.py --brain ~/.gemini/antigravity/brain --out data/processed/chat_history_sft.jsonl
  python scripts/chat_to_sft.py  # uses defaults

Combine with repo code data:
  cat data/processed/repo_code_sft.jsonl data/processed/chat_history_sft.jsonl > data/processed/combined_sft.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Skip binary/media/metadata files
SKIP_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".webm", ".svg"}
SKIP_PATTERNS = {".metadata.json", ".resolved", ".gitkeep"}

# Minimum content length (characters) to be worth training on
MIN_CONTENT_LENGTH = 200


def should_skip(path: Path) -> bool:
    """Skip media, metadata, and tiny files."""
    name = path.name.lower()
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    for pattern in SKIP_PATTERNS:
        if pattern in name:
            return True
    if name.startswith("."):
        return True
    return False


def extract_title(content: str, filename: str) -> str:
    """Extract the first H1/H2 heading from markdown, or fall back to filename."""
    match = re.search(r"^#{1,2}\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Fall back to cleaned filename
    stem = Path(filename).stem
    return stem.replace("_", " ").replace("-", " ").title()


def split_into_sections(content: str) -> list[tuple[str, str]]:
    """
    Split a markdown document into (heading, body) sections.
    Each H2 or H3 heading starts a new section.
    Returns at least one section (the whole document if no sub-headings).
    """
    pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    if not matches:
        return [("", content.strip())]

    sections: list[tuple[str, str]] = []

    # Content before the first heading
    preamble = content[: matches[0].start()].strip()
    if len(preamble) >= MIN_CONTENT_LENGTH:
        sections.append(("Overview", preamble))

    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        if len(body) >= MIN_CONTENT_LENGTH // 2:
            sections.append((heading, body))

    return sections


def artifact_to_examples(filepath: Path, conversation_id: str) -> list[dict]:
    """Convert one artifact markdown file into SFT training examples."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    if len(content) < MIN_CONTENT_LENGTH:
        return []

    title = extract_title(content, filepath.name)
    sections = split_into_sections(content)
    examples = []

    if len(sections) <= 2:
        # Small artifact → one example
        instruction = f"Explain: {title}"
        assistant_content = content.strip()
        # Keep only printable content (fpdf-safe) but don't strip actual content
        if len(assistant_content) >= MIN_CONTENT_LENGTH:
            examples.append({
                "messages": [
                    {"role": "user", "content": instruction},
                    {"role": "assistant", "content": assistant_content},
                ],
                "meta": {
                    "source": "chat_history",
                    "conversation_id": conversation_id,
                    "artifact": filepath.name,
                },
            })
    else:
        # Large artifact → one example per section
        for heading, body in sections:
            if len(body) < MIN_CONTENT_LENGTH // 2:
                continue
            section_instruction = f"{title}: {heading}" if heading else f"Explain: {title}"
            examples.append({
                "messages": [
                    {"role": "user", "content": section_instruction},
                    {"role": "assistant", "content": body},
                ],
                "meta": {
                    "source": "chat_history",
                    "conversation_id": conversation_id,
                    "artifact": filepath.name,
                    "section": heading,
                },
            })

    return examples


def scan_brain_directory(brain_dir: Path) -> list[dict]:
    """Walk all conversation directories and extract SFT examples from artifacts."""
    all_examples: list[dict] = []

    for conv_dir in sorted(brain_dir.iterdir()):
        if not conv_dir.is_dir():
            continue
        conversation_id = conv_dir.name
        if conversation_id == "tempmediaStorage":
            continue

        # Scan all markdown files in the conversation directory (non-recursive first level)
        for artifact in sorted(conv_dir.glob("*.md")):
            if should_skip(artifact):
                continue
            examples = artifact_to_examples(artifact, conversation_id)
            all_examples.extend(examples)

    return all_examples


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert conversation artifacts into SFT JSONL for training"
    )
    ap.add_argument(
        "--brain",
        type=Path,
        default=Path.home() / ".gemini" / "antigravity" / "brain",
        help="Path to the Antigravity brain directory",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/chat_history_sft.jsonl"),
        help="Output JSONL file",
    )
    ap.add_argument(
        "--min-length",
        type=int,
        default=MIN_CONTENT_LENGTH,
        help=f"Minimum content length (default {MIN_CONTENT_LENGTH})",
    )
    args = ap.parse_args()

    brain_dir = args.brain.resolve()
    if not brain_dir.is_dir():
        print(f"Brain directory not found: {brain_dir}", file=sys.stderr)
        sys.exit(1)

    examples = scan_brain_directory(brain_dir)
    if not examples:
        print("No training examples extracted.", file=sys.stderr)
        sys.exit(1)

    # Resolve output path relative to repo root
    out_path = args.out
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parent.parent / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Extracted {len(examples)} SFT examples from {brain_dir}", file=sys.stderr)
    print(f"Written to {out_path}", file=sys.stderr)

    # Print breakdown by conversation
    from collections import Counter
    conv_counts = Counter(ex["meta"]["conversation_id"] for ex in examples)
    print(f"\nBreakdown by conversation ({len(conv_counts)} conversations):", file=sys.stderr)
    for cid, count in conv_counts.most_common():
        print(f"  {cid}: {count} examples", file=sys.stderr)


if __name__ == "__main__":
    main()
