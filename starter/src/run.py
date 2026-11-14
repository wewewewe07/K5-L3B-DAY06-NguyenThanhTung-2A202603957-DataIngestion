"""Main orchestrator for Day 06 Data Ingestion Pipeline.

Executes:
1. Ingestion of 26-page substantive content from Explanable_AI_survey.pdf.
2. Building Strategy A (fixed-size) and Strategy B & C (structure-aware).
3. Embedding via real Gemini API (768 dimensions) and upserting into PostgreSQL + pgvector.
4. Running the 20 benchmark questions across all 3 strategies.
5. Reporting the five core evaluation dimensions.

Usage:
    cd starter
    python -m src.run
"""

from __future__ import annotations
import os
from pathlib import Path
import sys

from .ingestion import load_pdf
from .chunking import fixed_size, by_paragraph
from .embeddings import MyEmbedder
from .store import PgVectorStore
from .evaluation import evaluate_query, summarize


def main() -> None:
    starter_dir = Path(__file__).resolve().parents[1]
    root_dir = starter_dir.parent

    print("=================================================================")
    print("      DAY 06: DATA INGESTION ENGINEERING - MAIN PIPELINE         ")
    print("=================================================================")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        from dotenv import load_dotenv
        load_dotenv(starter_dir / ".env")
        db_url = os.getenv("DATABASE_URL")

    if not db_url:
        sys.exit("DATABASE_URL missing: check starter/.env file.")

    pdf_path = root_dir / "data" / "raw" / "Explanable_AI_survey.pdf"
    manifest_path = root_dir / "data" / "manifest.json"
    benchmark_file = root_dir / "benchmark" / "questions.json"

    # 1. Ingestion
    print("\n[Step 1/4] Loading and normalizing corpus...")
    pages = load_pdf(
        path=pdf_path,
        document_id="XAI_survey_2025",
        source="data/raw/Explanable_AI_survey.pdf",
        manifest_path=manifest_path
    )
    content_pages = [p for p in pages if p.metadata.get("is_content_page", True)]
    print(f"  -> Total physical pages: {len(pages)}")
    print(f"  -> Content pages (1-26): {len(content_pages)}")

    # 2. Chunking
    print("\n[Step 2/4] Generating chunks for Strategy A, B, C...")
    chunks_a = []
    for p in content_pages:
        chunks_a.extend(fixed_size(p, size=600, overlap=80))

    chunks_b = []
    for p in content_pages:
        chunks_b.extend(by_paragraph(p, max_size=900))

    print(f"  -> Strategy A chunks (fixed 600, overlap 80): {len(chunks_a)}")
    print(f"  -> Strategy B & C chunks (paragraph max 900): {len(chunks_b)}")

    # 3. Vector Store & Embeddings
    print("\n[Step 3/4] Connecting to PostgreSQL + pgvector and embedding...")
    model_name = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    dimensions = 768
    embedder = MyEmbedder(model_name=model_name, dimensions=dimensions)
    store = PgVectorStore(database_url=db_url, dimensions=dimensions)
    store.create_schema()

    print("  -> Embedding & upserting Strategy A...")
    vectors_a = embedder.embed_documents([c.text for c in chunks_a])
    store.upsert("A", chunks_a, vectors_a)

    print("  -> Embedding & upserting Strategy B...")
    vectors_b = embedder.embed_documents([c.text for c in chunks_b])
    store.upsert("B", chunks_b, vectors_b)
    print("  -> Upsert completed.")

    # 4. Evaluation
    print("\n[Step 4/4] Running Benchmark retrieval across 20 questions...")
    import json
    with open(benchmark_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    for strat in ["A", "B", "C"]:
        traces = []
        for q in questions:
            q_vec = embedder.embed_query(q["question"])
            flt = q.get("filter") if strat == "C" else None
            hits = store.search(strategy="A" if strat == "A" else "B", query_vector=q_vec, top_k=3, filters=flt)
            traces.append(evaluate_query(q, hits))

        s = summarize(traces)
        print(f"  Strategy {strat}: Dev Hit@1 = {s['dev']['hit1']} | Hit@3 = {s['dev']['hit3']} | Test Hit@3 = {s['test']['hit3']}")

    print("\n=================================================================")
    print("               PIPELINE RUN FINISHED SUCCESSFULLY!               ")
    print("=================================================================")


if __name__ == "__main__":
    main()
