"""
Upload a SFT JSONL dataset to Hugging Face as a datasets.Dataset.
Usage:
  python scripts/upload_hf.py --dataset data/processed/code_sft.jsonl --repo USERNAME/repo-name [--private]
Requires: pip install datasets huggingface-hub; HF token in HUGGING_FACE_TOKEN or huggingface-cli login.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Upload SFT JSONL to Hugging Face Hub")
    ap.add_argument("--dataset", type=Path, required=True, help="Path to .jsonl file (messages format)")
    ap.add_argument("--repo", type=str, required=True, help="Hugging Face repo id, e.g. USERNAME/code-instruct-sft")
    ap.add_argument("--private", action="store_true", help="Create a private dataset")
    args = ap.parse_args()

    path = args.dataset.resolve()
    if not path.exists():
        print(f"Dataset not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        from datasets import Dataset
        from huggingface_hub import HfApi
    except ImportError:
        print("Install: pip install datasets huggingface-hub", file=sys.stderr)
        sys.exit(2)

    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not rows:
        print("No valid rows in dataset.", file=sys.stderr)
        sys.exit(3)

    # Build Dataset from list of dicts with "messages" key
    dataset = Dataset.from_list(rows)
    api = HfApi()
    dataset.push_to_hub(args.repo, private=args.private)
    print(f"Uploaded {len(rows)} examples to {args.repo}", file=sys.stderr)


if __name__ == "__main__":
    main()
