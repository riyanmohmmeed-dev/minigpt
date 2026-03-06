"""
Compile raw quadruplet JSONL into SFT-ready JSONL (messages format for TRL SFTTrainer).
Usage:
  python scripts/to_jsonl.py --raw data/raw --out data/processed/code_sft.jsonl [--include-reasoning]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def quadruplet_to_messages(record: dict, include_reasoning: bool = True) -> dict:
    """
    Convert one quadruplet into TRL conversational format: {"messages": [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]}.
    Assistant content can be "reasoning + code + verification" or just "code" depending on include_reasoning.
    """
    instruction = record.get("instruction", "")
    reasoning = record.get("reasoning", "")
    code = record.get("code", "")
    verification = record.get("verification", "")

    if include_reasoning and (reasoning or verification):
        parts = []
        if reasoning:
            parts.append(f"Reasoning:\n{reasoning}")
        parts.append(f"Code:\n```\n{code}\n```")
        if verification:
            parts.append(f"Verification:\n{verification}")
        assistant_content = "\n\n".join(parts)
    else:
        assistant_content = code if code else ""

    return {
        "messages": [
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Compile raw quadruplets to SFT JSONL")
    ap.add_argument("--raw", type=Path, default=Path("data/raw"), help="Directory containing expanded.jsonl (or path to jsonl file)")
    ap.add_argument("--out", type=Path, default=Path("data/processed/code_sft.jsonl"), help="Output JSONL path")
    ap.add_argument("--include-reasoning", action="store_true", default=True, help="Include reasoning and verification in assistant message")
    ap.add_argument("--no-include-reasoning", action="store_false", dest="include_reasoning", help="Assistant message is code only")
    args = ap.parse_args()

    raw = args.raw.resolve()
    if raw.is_dir():
        raw_file = raw / "expanded.jsonl"
    else:
        raw_file = raw

    if not raw_file.exists():
        print(f"Input not found: {raw_file}", file=sys.stderr)
        sys.exit(1)

    args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(raw_file, encoding="utf-8") as fin, open(args.out, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            sft = quadruplet_to_messages(record, include_reasoning=args.include_reasoning)
            fout.write(json.dumps(sft, ensure_ascii=False) + "\n")
            count += 1

    print(f"Wrote {count} SFT examples to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
