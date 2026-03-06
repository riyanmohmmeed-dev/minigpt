"""
Expand seed problems into quadruplets (instruction, reasoning, code, verification) using a teacher model API.
Usage:
  python scripts/expand_dataset.py --seeds data/seeds --out data/raw [--limit N] [--backend openai]
Requires OPENAI_API_KEY for OpenAI backend.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Quadruplet schema (for SFT / OpenCodeInstruct-style data)
# ---------------------------------------------------------------------------

QUADRUPLET_PROMPT = """You are a coding instructor. For the following programming task, produce exactly four parts in your response, using these exact section headers (copy them as-is).

TASK:
{instruction}

Respond with exactly these four sections, each starting with the header on its own line:

## Instruction
(Rephrase or keep the task as a clear user instruction in one or two sentences.)

## Reasoning
(Step-by-step logic: what approach to take, edge cases, then outline the solution. Use short bullet points or numbered steps.)

## Code
(Full code snippet in {language}. Use a fenced code block with language tag.)

## Verification
(Either a short test case / example input and expected output, or a one-sentence explanation of why the code is correct.)

Do not add any text before ## Instruction or after ## Verification."""


def load_seeds(seeds_dir: Path) -> list[dict]:
    """Load all seed items from JSON files in seeds_dir."""
    items = []
    for path in sorted(seeds_dir.glob("*.json")):
        if path.name.startswith("."):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: skip {path}: {e}", file=sys.stderr)
            continue
        if isinstance(data, list):
            items.extend(data)
        else:
            items.append(data)
    return items


def parse_quadruplet(response: str, language: str) -> dict | None:
    """Parse teacher response into instruction, reasoning, code, verification."""
    sections = {}
    current = None
    buffer = []

    for line in response.split("\n"):
        if line.strip().startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            raw = line.strip()[3:].strip().lower()
            if "instruction" in raw:
                current = "instruction"
            elif "reasoning" in raw:
                current = "reasoning"
            elif "code" in raw:
                current = "code"
            elif "verification" in raw:
                current = "verification"
            else:
                current = None
            buffer = []
        elif current is not None:
            buffer.append(line)

    if current is not None:
        sections[current] = "\n".join(buffer).strip()

    # Extract code from fenced block if present
    if "code" in sections:
        code = sections["code"]
        match = re.search(r"```(?:\w+)?\s*\n(.*?)```", code, re.DOTALL)
        if match:
            sections["code"] = match.group(1).strip()

    if set(sections) >= {"instruction", "reasoning", "code", "verification"}:
        return {
            "instruction": sections["instruction"],
            "reasoning": sections["reasoning"],
            "code": sections["code"],
            "verification": sections["verification"],
        }
    return None


def expand_with_openai(seed: dict, language: str, api_key: str) -> dict | None:
    """Call OpenAI API to generate a quadruplet. Returns one record or None."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Install openai: pip install openai", file=sys.stderr)
        return None

    client = OpenAI(api_key=api_key)
    prompt = QUADRUPLET_PROMPT.format(
        instruction=seed.get("instruction", ""),
        language=seed.get("language", "python"),
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048,
    )
    content = (resp.choices[0].message.content or "").strip()
    if not content:
        return None
    parsed = parse_quadruplet(content, seed.get("language", "python"))
    if not parsed:
        return None
    return {
        "seed_id": seed.get("id", ""),
        **parsed,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Expand seed dataset into quadruplets via teacher API")
    ap.add_argument("--seeds", type=Path, default=Path("data/seeds"), help="Directory of seed JSON files")
    ap.add_argument("--out", type=Path, default=Path("data/raw"), help="Output directory for raw JSONL")
    ap.add_argument("--limit", type=int, default=0, help="Max number of seeds to process (0 = all)")
    ap.add_argument("--backend", choices=["openai"], default="openai", help="Teacher API backend")
    args = ap.parse_args()

    seeds_dir = args.seeds.resolve()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    items = load_seeds(seeds_dir)
    if not items:
        print("No seed items found under", seeds_dir, file=sys.stderr)
        sys.exit(1)

    if args.limit > 0:
        items = items[: args.limit]

    api_key = os.environ.get("OPENAI_API_KEY")
    if args.backend == "openai" and not api_key and len(items) > 0:
        print("Set OPENAI_API_KEY for OpenAI backend.", file=sys.stderr)
        sys.exit(2)

    out_path = out_dir / "expanded.jsonl"
    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for i, seed in enumerate(items):
            if args.backend == "openai" and api_key:
                record = expand_with_openai(seed, seed.get("language", "python"), api_key)
            else:
                record = None
            if record:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(items)} ...", file=sys.stderr)

    print(f"Wrote {count} quadruplets to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
