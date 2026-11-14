#!/usr/bin/env python3
"""Stage 4 Execution Script: Generate embeddings and ingest into PostgreSQL + pgvector.

Executes:
1. Connects to PostgreSQL, ensures pgvector extension and creates schema.
2. Ingests Strategy A (266 chunks) with real Gemini embeddings (768 dimensions).
3. Ingests Strategy B (175 chunks) with real Gemini embeddings (768 dimensions).
4. Verifies row counts and tests sample queries for A, B, and C (with metadata filter).
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

from src.ingestion import load_pdf
from src.chunking import fixed_size, by_paragraph
from src.embeddings import MyEmbedder
from src.store import PgVectorStore


def main() -> None:
    starter_dir = Path(__file__).resolve().parents[1]
    root_dir = starter_dir.parent

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL missing from starter/.env")

    pdf_path = root_dir / "data" / "raw" / "Explanable_AI_survey.pdf"
    manifest_path = root_dir / "data" / "manifest.json"

    print("=================================================================")
    print("      STAGE 4: VECTOR STORE INGESTION (PostgreSQL + pgvector)    ")
    print("=================================================================")

    # 1. Initialize Embedder & Vector Store
    model_name = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    dimensions = 768
    print(f"\n[1] Initializing Embedder ({model_name}, dim={dimensions})...")
    embedder = MyEmbedder(model_name=model_name, dimensions=dimensions)

    print(f"\n[2] Connecting to PostgreSQL and creating schema...")
    store = PgVectorStore(database_url=db_url, dimensions=dimensions)
    store.create_schema()
    print("  -> Schema initialized OK.")

    # 2. Load PDF Pages
    print(f"\n[3] Loading and chunking corpus...")
    pages = load_pdf(
        path=pdf_path,
        document_id="XAI_survey_2025",
        source="data/raw/Explanable_AI_survey.pdf",
        manifest_path=manifest_path
    )
    content_pages = [p for p in pages if p.metadata.get("is_content_page", True)]

    chunks_a = []
    for p in content_pages:
        chunks_a.extend(fixed_size(p, size=600, overlap=80))

    chunks_b = []
    for p in content_pages:
        chunks_b.extend(by_paragraph(p, max_size=900))

    print(f"  -> Strategy A Chunks: {len(chunks_a)}")
    print(f"  -> Strategy B Chunks: {len(chunks_b)}")

    # 3. Embed & Ingest Strategy A
    print(f"\n[4] Generating Embeddings for Strategy A ({len(chunks_a)} chunks)...")
    start_time_a = time.time()
    texts_a = [c.text for c in chunks_a]
    vectors_a = embedder.embed_documents(texts_a, batch_size=50)
    embed_time_a = time.time() - start_time_a
    print(f"  -> Completed in {embed_time_a:.2f}s (Got {len(vectors_a)} vectors)")

    print(f"  -> Upserting Strategy A into PostgreSQL...")
    store.upsert(strategy="A", chunks=chunks_a, vectors=vectors_a)
    print("  -> Upsert Strategy A OK.")

    # 4. Embed & Ingest Strategy B
    print(f"\n[5] Generating Embeddings for Strategy B ({len(chunks_b)} chunks)...")
    start_time_b = time.time()
    texts_b = [c.text for c in chunks_b]
    vectors_b = embedder.embed_documents(texts_b, batch_size=50)
    embed_time_b = time.time() - start_time_b
    print(f"  -> Completed in {embed_time_b:.2f}s (Got {len(vectors_b)} vectors)")

    print(f"  -> Upserting Strategy B into PostgreSQL...")
    store.upsert(strategy="B", chunks=chunks_b, vectors=vectors_b)
    print("  -> Upsert Strategy B OK.")

    # 5. Sanity Test Queries for A, B, and C
    print(f"\n[6] Running Sample Test Queries...")
    test_question = "Why do artificial intelligence models encounter significant challenges in safety-critical domains such as healthcare and autonomous vehicles?"
    test_query_vec = embedder.embed_query(test_question)

    hits_a = store.search(strategy="A", query_vector=test_query_vec, top_k=1)
    hits_b = store.search(strategy="B", query_vector=test_query_vec, top_k=1)

    # Strategy C with category filter
    filter_q = "Why is healthcare considered a critical domain requiring explainable decision-making?"
    filter_vec = embedder.embed_query(filter_q)
    hits_c = store.search(
        strategy="B",
        query_vector=filter_vec,
        top_k=1,
        filters={"category": "applications_healthcare"}
    )

    print(f"\n  [Sample Strategy A Top-1 Match]:")
    print(f"   ID: {hits_a[0]['chunk_id']} | Page: {hits_a[0]['page']} | Score: {hits_a[0]['score']}")
    print(f"   Text preview: {hits_a[0]['text'][:150]}...")

    print(f"\n  [Sample Strategy B Top-1 Match]:")
    print(f"   ID: {hits_b[0]['chunk_id']} | Page: {hits_b[0]['page']} | Score: {hits_b[0]['score']}")
    print(f"   Text preview: {hits_b[0]['text'][:150]}...")

    print(f"\n  [Sample Strategy C Top-1 Match with Filter (category='applications_healthcare')]:")
    print(f"   ID: {hits_c[0]['chunk_id']} | Page: {hits_c[0]['page']} | Category: {hits_c[0]['category']} | Score: {hits_c[0]['score']}")
    print(f"   Text preview: {hits_c[0]['text'][:150]}...")

    # Save log of ingestion
    log_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_name": model_name,
        "dimensions": dimensions,
        "strategy_A": {
            "chunk_count": len(chunks_a),
            "embed_time_seconds": round(embed_time_a, 2),
            "cost_usd": 0.0  # Free tier
        },
        "strategy_B": {
            "chunk_count": len(chunks_b),
            "embed_time_seconds": round(embed_time_b, 2),
            "cost_usd": 0.0
        }
    }
    log_file = starter_dir / "results" / "ingestion_log.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)
    print(f"\nSaved ingestion summary to: {log_file}")

    print("\n=================================================================")
    print("               STAGE 4 COMPLETED SUCCESSFULLY!                   ")
    print("=================================================================")


if __name__ == "__main__":
    main()

