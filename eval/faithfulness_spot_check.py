"""Ask Claude for 20 fixed questions and write an ungraded manual-review CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app.config import get_settings
from app.rag.answer import answer_question


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("eval/faithfulness_review.csv"))
    args = parser.parse_args()
    settings = get_settings()
    if not settings.anthropic_api_key or not settings.claude_model:
        raise SystemExit("Set ANTHROPIC_API_KEY and CLAUDE_MODEL before running this optional real-API spot check.")
    questions = json.loads(Path(__file__).with_name("questions.json").read_text(encoding="utf-8"))
    selected = [item for item in questions if item["answerable"]][:20]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["question", "answer", "sources", "supported yes/no"])
        writer.writeheader()
        for item in selected:
            result = answer_question(item["question"])
            writer.writerow({"question": item["question"], "answer": result.answer,
                             "sources": json.dumps([source.__dict__ for source in result.sources], ensure_ascii=False),
                             "supported yes/no": ""})
    print(f"Wrote {len(selected)} ungraded answers to {args.output}. Fill in the support column manually.")


if __name__ == "__main__":
    main()
