"""Warm the /query cache with the gold question set — and spot-check it.

    python -m scripts.warm_cache            # run all, cache answers, print a table
    python -m scripts.warm_cache --recheck  # ignore the cache, re-run everything

For each gold question it runs the full pipeline (which populates the on-disk
cache), then checks whether the answer cites at least one of the expected
sections. This is both the demo pre-warm and the Day-4 hallucination spot-check.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.logging import get_logger
from app.schemas import Jurisdiction, QueryRequest
from app.services import pipeline

logger = get_logger("warm_cache")
GOLD = Path(__file__).resolve().parents[1] / "data" / "gold_questions.json"


def _section_hit(citations, expected: list[str]) -> bool:
    if not expected:
        return True
    got = {c.section.lower().lstrip("section ").strip() for c in citations}
    return any(e.lower() in got or any(e.lower() in g for g in got) for e in expected)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recheck", action="store_true", help="bypass the cache")
    args = ap.parse_args()

    gold = json.loads(GOLD.read_text(encoding="utf-8"))["questions"]
    rows, answered, cite_ok = [], 0, 0

    for q in gold:
        req = QueryRequest(
            query=q["query"],
            jurisdiction=Jurisdiction(q.get("jurisdiction", "india")),
            formulation_category=q.get("formulation_category"),
        )
        resp = pipeline.run_query(req, use_cache=not args.recheck)
        status = resp.confidence.status.value
        answered += status == "answered"
        hit = _section_hit(resp.citations, q.get("expect_sections", []))
        cite_ok += hit and status == "answered"
        rows.append(
            (
                status,
                "cited-ok" if hit else "cite-miss",
                "cache" if resp.cached else "fresh",
                q["query"][:60],
            )
        )

    print(f"\n{'status':10} {'sections':10} {'src':6} question")
    print("-" * 90)
    for r in rows:
        print(f"{r[0]:10} {r[1]:10} {r[2]:6} {r[3]}")
    print(
        f"\n{answered}/{len(gold)} answered · {cite_ok}/{len(gold)} answered "
        f"with an expected section cited"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
