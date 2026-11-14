#!/usr/bin/env python3
"""Stage 5 Benchmark Execution Script.

Runs Top-3 retrieval across all 20 questions (15 dev / 5 test) for:
- Strategy A: Fixed-size 600 chars, no filter.
- Strategy B: Structure-aware paragraph 900 chars, no filter.
- Strategy C: Same paragraph chunks as B + SQL metadata filter when applicable.

Computes Hit@1 and Evidence Hit@3, outputs full traces, and generates summary tables.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import time

# Ensure starter/ can import src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from src.embeddings import MyEmbedder
from src.store import PgVectorStore
from src.evaluation import evaluate_query, summarize


def run_benchmark():
    starter_dir = Path(__file__).resolve().parents[1]
    root_dir = starter_dir.parent

    benchmark_file = root_dir / "benchmark" / "questions.json"
    results_dir = starter_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL missing from starter/.env")

    print("=================================================================")
    print("           STAGE 5: FULL BENCHMARK RETRIEVAL RUN                 ")
    print("=================================================================")

    # 1. Load benchmark questions
    with open(benchmark_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"\n[1] Loaded {len(questions)} questions from {benchmark_file}")
    dev_q = [q for q in questions if q["split"] == "dev"]
    test_q = [q for q in questions if q["split"] == "test"]
    print(f"    - Dev set:  {len(dev_q)} questions")
    print(f"    - Test set: {len(test_q)} questions")

    # 2. Connect store & embedder
    model_name = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    dimensions = 768
    embedder = MyEmbedder(model_name=model_name, dimensions=dimensions)
    store = PgVectorStore(database_url=db_url, dimensions=dimensions)

    # Pre-embed all questions (cached)
    print(f"\n[2] Pre-generating / loading query embeddings (20 queries)...")
    query_vectors = {}
    for q in questions:
        query_vectors[q["id"]] = embedder.embed_query(q["question"])
    print("    -> All 20 query vectors ready.")

    strategies = ["A", "B", "C"]
    summary_by_strategy = {}

    for strat in strategies:
        print(f"\n[3] Executing Strategy {strat}...")
        traces = []
        start_time = time.time()

        for q in questions:
            q_vec = query_vectors[q["id"]]

            if strat == "A":
                hits = store.search(strategy="A", query_vector=q_vec, top_k=3, filters=None)
            elif strat == "B":
                hits = store.search(strategy="B", query_vector=q_vec, top_k=3, filters=None)
            elif strat == "C":
                # Strategy C uses Strategy B index, with metadata filter if provided in question
                filters = q.get("filter")
                hits = store.search(strategy="B", query_vector=q_vec, top_k=3, filters=filters)

            trace_item = evaluate_query(question=q, hits=hits)
            traces.append(trace_item)

        exec_time = time.time() - start_time
        strat_summary = summarize(traces)
        strat_summary["execution_time_seconds"] = round(exec_time, 3)
        summary_by_strategy[strat] = strat_summary

        # Save per-strategy traces
        trace_path = results_dir / f"traces_strategy_{strat}.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(traces, f, indent=2, ensure_ascii=False)

        print(f"    -> Saved trace: {trace_path}")
        print(f"    -> Dev:  Hit@1 = {strat_summary['dev']['hit1']} | Hit@3 = {strat_summary['dev']['hit3']}")
        print(f"    -> Test: Hit@1 = {strat_summary['test']['hit1']} | Hit@3 = {strat_summary['test']['hit3']}")

    # 4. Save overall summary
    summary_path = results_dir / "benchmark_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_by_strategy, f, indent=2)

    # 5. Print Markdown Comparison Table
    print("\n=================================================================")
    print("                     BENCHMARK RESULTS TABLE                     ")
    print("=================================================================")
    print("| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunks | Thời gian |")
    print("|:---:|:---:|:---:|:---:|:---:|:---:|")
    for strat in ["A", "B", "C"]:
        s = summary_by_strategy[strat]
        ch_count = 266 if strat == "A" else 175
        t_sec = f"{s['execution_time_seconds']}s"
        print(f"| **{strat}** | Dev (15)  | {s['dev']['hit1']:12s} | {s['dev']['hit3']:18s} | {ch_count} | {t_sec} |")
        print(f"| **{strat}** | Test (5)  | {s['test']['hit1']:12s} | {s['test']['hit3']:18s} | {ch_count} | {t_sec} |")

    print("\nBenchmark complete! Full summary saved to results/benchmark_summary.json")
    return summary_by_strategy


if __name__ == "__main__":
    run_benchmark()

