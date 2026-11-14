#!/usr/bin/env python3
"""Stage 3 Test & Verification Script.

Executes Ingestion and Chunking for Strategy A and Strategy B.
Computes metrics, verifies evidence retrieval coverage, and displays comparison samples.
"""

from __future__ import annotations
import json
from pathlib import Path
import re
import sys

# Ensure starter/ can import src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion import load_pdf
from src.chunking import fixed_size, by_paragraph


def normalize_match(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def run_stage_3_verification():
    starter_dir = Path(__file__).resolve().parents[1]
    root_dir = starter_dir.parent

    pdf_path = root_dir / "data" / "raw" / "Explanable_AI_survey.pdf"
    manifest_path = root_dir / "data" / "manifest.json"
    benchmark_path = root_dir / "benchmark" / "questions.json"
    results_dir = starter_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("           STAGE 3: INGESTION & CHUNKING VERIFICATION            ")
    print("=================================================================")

    # 1. Ingestion
    print("\n[1] Reading and Normalizing PDF...")
    pages = load_pdf(
        path=pdf_path,
        document_id="XAI_survey_2025",
        source="data/raw/Explanable_AI_survey.pdf",
        manifest_path=manifest_path
    )
    content_pages = [p for p in pages if p.metadata.get("is_content_page", True)]
    total_chars = sum(len(p.text) for p in content_pages)

    print(f"  - Total Physical Pages Loaded: {len(pages)}")
    print(f"  - Content Pages (1-26): {len(content_pages)}")
    print(f"  - Total Normalized Characters: {total_chars:,}")

    # 2. Chunking - Strategy A (Fixed size: 600, overlap: 80)
    print("\n[2] Executing Strategy A (Fixed-size: 600 chars, overlap: 80)...")
    chunks_a = []
    for p in content_pages:
        chunks_a.extend(fixed_size(p, size=600, overlap=80))

    lengths_a = [len(c.text) for c in chunks_a]
    avg_len_a = sum(lengths_a) / len(lengths_a) if lengths_a else 0
    print(f"  - Strategy A Total Chunks: {len(chunks_a)}")
    print(f"  - Lengths: Min = {min(lengths_a)}, Max = {max(lengths_a)}, Avg = {avg_len_a:.1f} chars")

    # 3. Chunking - Strategy B & C (Structure-aware by paragraph: max_size 900)
    print("\n[3] Executing Strategy B & C (Structure-aware: max_size 900 chars)...")
    chunks_b = []
    for p in content_pages:
        chunks_b.extend(by_paragraph(p, max_size=900))

    lengths_b = [len(c.text) for c in chunks_b]
    avg_len_b = sum(lengths_b) / len(lengths_b) if lengths_b else 0
    print(f"  - Strategy B/C Total Chunks: {len(chunks_b)}")
    print(f"  - Lengths: Min = {min(lengths_b)}, Max = {max(lengths_b)}, Avg = {avg_len_b:.1f} chars")

    # 4. Save artifacts for Stage 4 & auditing
    file_a = results_dir / "chunks_strategy_A.json"
    file_b = results_dir / "chunks_strategy_B.json"

    with open(file_a, "w", encoding="utf-8") as f:
        json.dump([{
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "page": c.page,
            "text": c.text,
            "metadata": c.metadata
        } for c in chunks_a], f, indent=2, ensure_ascii=False)

    with open(file_b, "w", encoding="utf-8") as f:
        json.dump([{
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "page": c.page,
            "text": c.text,
            "metadata": c.metadata
        } for c in chunks_b], f, indent=2, ensure_ascii=False)

    print(f"\n[4] Saved chunk artifacts:")
    print(f"  --> {file_a} ({len(chunks_a)} chunks)")
    print(f"  --> {file_b} ({len(chunks_b)} chunks)")

    # 5. Benchmark Coverage Sanity Check
    if benchmark_path.exists():
        print("\n[5] Checking Evidence Coverage against 20 Benchmark Questions...")
        with open(benchmark_path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        found_in_a = 0
        found_in_b = 0
        for q in questions:
            ev = normalize_match(q["evidence_quote"])[:50]
            gold_p = q["gold_page"]

            in_a = any(ev in normalize_match(c.text) for c in chunks_a if c.page == gold_p)
            in_b = any(ev in normalize_match(c.text) for c in chunks_b if c.page == gold_p)

            if in_a:
                found_in_a += 1
            if in_b:
                found_in_b += 1

        print(f"  - Strategy A Evidence Coverage: {found_in_a}/{len(questions)} ({found_in_a/len(questions)*100:.1f}%)")
        print(f"  - Strategy B Evidence Coverage: {found_in_b}/{len(questions)} ({found_in_b/len(questions)*100:.1f}%)")

    # 6. Sample Comparison Preview
    print("\n[6] Visual Comparison Sample (Page 5: Ante-hoc vs Post-hoc)...")
    sample_a = [c for c in chunks_a if c.page == 5 and "ante-hoc" in c.text.lower()]
    sample_b = [c for c in chunks_b if c.page == 5 and "ante-hoc" in c.text.lower()]

    if sample_a:
        print("\n--- Strategy A Chunk (Fixed Window) ---")
        print(f"ID: {sample_a[0].chunk_id} | Length: {len(sample_a[0].text)}")
        print(f"Preview:\n{sample_a[0].text[:300]}...")

    if sample_b:
        print("\n--- Strategy B Chunk (Paragraph Structure) ---")
        print(f"ID: {sample_b[0].chunk_id} | Length: {len(sample_b[0].text)}")
        print(f"Preview:\n{sample_b[0].text[:300]}...")

    print("\n=================================================================")
    print("               STAGE 3 COMPLETED SUCCESSFULLY!                   ")
    print("=================================================================")


if __name__ == "__main__":
    run_stage_3_verification()
