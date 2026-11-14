"""PostgreSQL + pgvector vector store implementation with idempotency and metadata filtering."""

from __future__ import annotations
import json
from typing import Any
import psycopg
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        """Create extension and document_chunks table with vector and metadata columns."""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        chunk_id VARCHAR(64) PRIMARY KEY,
                        strategy VARCHAR(16) NOT NULL,
                        document_id VARCHAR(64) NOT NULL,
                        source VARCHAR(255) NOT NULL,
                        page INT NOT NULL,
                        section VARCHAR(128),
                        category VARCHAR(64),
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL,
                        embedding vector({self.dimensions}) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_chunks_strat ON document_chunks(strategy);
                    CREATE INDEX IF NOT EXISTS idx_chunks_strat_cat ON document_chunks(strategy, category);
                    CREATE INDEX IF NOT EXISTS idx_chunks_strat_page ON document_chunks(strategy, page);
                """)
                conn.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Insert or replace chunks with stable IDs and embeddings, ensuring idempotency."""
        if len(chunks) != len(vectors):
            raise ValueError(
                f"Count mismatch between chunks ({len(chunks)}) and vectors ({len(vectors)})"
            )

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                # Remove obsolete chunks for this strategy to guarantee idempotency and clean re-ingest
                cur.execute("DELETE FROM document_chunks WHERE strategy = %s;", (strategy,))

                insert_sql = f"""
                    INSERT INTO document_chunks (
                        chunk_id, strategy, document_id, source, page, section, category, text, metadata, embedding
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector
                    )
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        text = EXCLUDED.text,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding;
                """

                rows_to_insert = []
                for ch, vec in zip(chunks, vectors):
                    if len(vec) != self.dimensions:
                        raise ValueError(
                            f"Vector dimension {len(vec)} does not match store dimension {self.dimensions}"
                        )
                    section = ch.metadata.get("section", "General")
                    category = ch.metadata.get("category", "general")
                    rows_to_insert.append((
                        ch.chunk_id,
                        strategy,
                        ch.document_id,
                        ch.source,
                        ch.page,
                        section,
                        category,
                        ch.text,
                        json.dumps(ch.metadata),
                        vec
                    ))

                cur.executemany(insert_sql, rows_to_insert)
                conn.commit()

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Filter metadata in SQL, rank by cosine distance (<=>), and return top-k matches."""
        if len(query_vector) != self.dimensions:
            raise ValueError(
                f"Query vector dimension {len(query_vector)} does not match store dimension {self.dimensions}"
            )

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                where_clauses = ["strategy = %s"]
                params: list[Any] = [strategy]

                # Apply metadata filters (essential for Strategy C)
                if filters:
                    for key, val in filters.items():
                        if key == "category":
                            where_clauses.append("category = %s")
                            params.append(str(val))
                        elif key == "page":
                            where_clauses.append("page = %s")
                            params.append(int(val))
                        else:
                            where_clauses.append("(metadata->>%s) = %s")
                            params.extend([key, str(val)])

                where_sql = " AND ".join(where_clauses)
                query_sql = f"""
                    SELECT chunk_id, document_id, source, page, section, category, text, metadata,
                           (embedding <=> %s::vector) AS distance
                    FROM document_chunks
                    WHERE {where_sql}
                    ORDER BY distance ASC
                    LIMIT %s;
                """
                # Query vector is parameter 1 in SELECT, followed by WHERE params, and finally LIMIT top_k
                exec_params = [query_vector] + params + [top_k]

                cur.execute(query_sql, exec_params)
                rows = cur.fetchall()

                results = []
                for r in rows:
                    dist = float(r[8])
                    results.append({
                        "chunk_id": r[0],
                        "document_id": r[1],
                        "source": r[2],
                        "page": r[3],
                        "section": r[4],
                        "category": r[5],
                        "text": r[6],
                        "metadata": r[7],
                        "distance": dist,
                        "score": round(1.0 - dist, 4)  # Cosine similarity
                    })

                return results
