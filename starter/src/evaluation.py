"""Evaluate retrieved evidence and preserve per-query traces."""

from __future__ import annotations
import re
from typing import Any
import unicodedata


def normalize_match(text: str) -> str:
    """Normalize string for robust text matching against retrieved chunks."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def is_evidence_hit(gold_page: int, evidence_quote: str, chunk: dict[str, Any]) -> bool:
    """Determine whether a retrieved chunk constitutes a verified evidence hit.

    Requirements:
    1. Chunk must originate from the gold page.
    2. Chunk must contain the substantive gold evidence quote (exact or >=80% keyword coverage).
    """
    if chunk.get("page") != gold_page:
        return False

    chunk_text = normalize_match(chunk.get("text", ""))
    norm_evidence = normalize_match(evidence_quote)

    # 1. Exact substring match
    if norm_evidence in chunk_text:
        return True

    # 2. Check first 40 chars prefix match
    if len(norm_evidence) >= 40 and norm_evidence[:40] in chunk_text:
        return True

    # 3. Keyword density match for long passages
    keywords = [w for w in re.split(r"\W+", norm_evidence) if len(w) > 3]
    if keywords:
        match_count = sum(1 for kw in keywords if kw in chunk_text)
        if match_count / len(keywords) >= 0.8:
            return True

    return False


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check gold page and evidence containment; record hit@1 and hit@3 trace."""
    gold_page = question["gold_page"]
    evidence_quote = question["evidence_quote"]

    annotated_hits = []
    for rank, h in enumerate(hits[:3], start=1):
        hit_flag = is_evidence_hit(gold_page, evidence_quote, h)
        annotated_hits.append({
            "rank": rank,
            "chunk_id": h.get("chunk_id"),
            "page": h.get("page"),
            "section": h.get("section"),
            "category": h.get("category"),
            "score": h.get("score"),
            "distance": h.get("distance"),
            "text": h.get("text"),
            "is_gold_hit": hit_flag
        })

    hit_at_1 = 1 if (len(annotated_hits) > 0 and annotated_hits[0]["is_gold_hit"]) else 0
    hit_at_3 = 1 if any(h["is_gold_hit"] for h in annotated_hits) else 0

    return {
        "question_id": question["id"],
        "split": question["split"],
        "type": question["type"],
        "question": question["question"],
        "expected_answer": question["expected_answer"],
        "gold_page": gold_page,
        "evidence_quote": evidence_quote,
        "filter": question.get("filter"),
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "top_3_hits": annotated_hits
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by split (dev / test)."""
    dev_traces = [t for t in traces if t["split"] == "dev"]
    test_traces = [t for t in traces if t["split"] == "test"]

    def calc_split(subset: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(subset)
        if n == 0:
            return {"hit1": "0/0 (0.0%)", "hit3": "0/0 (0.0%)", "hit1_count": 0, "hit3_count": 0, "total": 0}

        h1 = sum(t["hit_at_1"] for t in subset)
        h3 = sum(t["hit_at_3"] for t in subset)
        pct1 = (h1 / n) * 100
        pct3 = (h3 / n) * 100

        return {
            "hit1": f"{h1}/{n} ({pct1:.1f}%)",
            "hit3": f"{h3}/{n} ({pct3:.1f}%)",
            "hit1_count": h1,
            "hit3_count": h3,
            "total": n,
            "hit1_pct": round(pct1, 1),
            "hit3_pct": round(pct3, 1)
        }

    return {
        "dev": calc_split(dev_traces),
        "test": calc_split(test_traces),
        "total": calc_split(traces)
    }
