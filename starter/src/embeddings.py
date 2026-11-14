"""Real embedding provider implementation using Gemini API with batching, caching, and rate limit backoff."""

from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Protocol
from dotenv import load_dotenv
import requests

# Load environment variables from starter/.env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Gemini API embedding adapter with local disk caching and adaptive rate-limit backoff."""

    def __init__(
        self,
        model_name: str = "models/gemini-embedding-001",
        dimensions: int = 768,
        api_key: str | None = None
    ) -> None:
        self.model_name = model_name
        self.dimensions = dimensions
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY missing from environment or starter/.env. "
                "Do not fall back to mock vectors."
            )

        self.api_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # Setup local cache file
        self.cache_dir = Path(__file__).resolve().parents[1] / "results"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "embeddings_cache.json"
        self.cache: dict[str, list[float]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def _save_cache(self) -> None:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"[Warning] Failed to save embeddings cache: {e}")

    def _hash_text(self, text: str, task: str) -> str:
        content = f"{self.model_name}_{self.dimensions}_{task}_{text}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def embed_documents(self, texts: list[str], batch_size: int = 40) -> list[list[float]]:
        """Embed a list of text chunks in batches using batchEmbedContents with disk cache."""
        if not texts:
            return []

        results: list[list[float] | None] = [None] * len(texts)
        missing_indices: list[int] = []

        # 1. Check disk cache
        for idx, t in enumerate(texts):
            h = self._hash_text(t, "RETRIEVAL_DOCUMENT")
            if h in self.cache:
                results[idx] = self.cache[h]
            else:
                missing_indices.append(idx)

        cached_count = len(texts) - len(missing_indices)
        if cached_count > 0:
            print(f"  -> Cache hit: {cached_count}/{len(texts)} embeddings loaded instantly from disk.")

        if not missing_indices:
            return [vec for vec in results if vec is not None]

        # 2. Fetch missing items in batches
        print(f"  -> Fetching remaining {len(missing_indices)} embeddings from Gemini API...")
        for i in range(0, len(missing_indices), batch_size):
            batch_indices = missing_indices[i:i + batch_size]
            batch_texts = [texts[idx] for idx in batch_indices]

            requests_payload = []
            for t in batch_texts:
                requests_payload.append({
                    "model": self.model_name,
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": self.dimensions,
                    "taskType": "RETRIEVAL_DOCUMENT"
                })

            url = f"{self.api_url}/{self.model_name}:batchEmbedContents?key={self.api_key}"

            max_retries = 8
            success = False
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json={"requests": requests_payload}, timeout=60)
                    if response.status_code == 200:
                        data = response.json()
                        embeddings = data.get("embeddings", [])
                        if len(embeddings) != len(batch_texts):
                            raise ValueError(f"Batch mismatch: sent {len(batch_texts)}, got {len(embeddings)}")

                        for b_idx, item in zip(batch_indices, embeddings):
                            vec = item.get("values", [])
                            results[b_idx] = vec
                            # Store in cache
                            h = self._hash_text(texts[b_idx], "RETRIEVAL_DOCUMENT")
                            self.cache[h] = vec

                        self._save_cache()
                        success = True
                        # Polite throttle to stay comfortably below 15 RPM
                        time.sleep(2)
                        break
                    elif response.status_code == 429:
                        wait_sec = 15 + attempt * 5  # Give Gemini quota bucket time to drain
                        print(f"[RateLimit] 429 received on batch {i//batch_size + 1}. Waiting {wait_sec}s for quota reset...")
                        time.sleep(wait_sec)
                    else:
                        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")
                except requests.RequestException as e:
                    wait_sec = 5 + attempt * 2
                    print(f"[Network] Connection warning ({e}), retrying in {wait_sec}s...")
                    time.sleep(wait_sec)

            if not success:
                raise RuntimeError(f"Failed to embed batch starting at index {i} after {max_retries} attempts.")

        return [vec for vec in results if vec is not None]

    def embed_query(self, question: str) -> list[float]:
        """Embed a single search query vector with cache."""
        if not question or not question.strip():
            raise ValueError("Query string cannot be empty.")

        q_clean = question.strip()
        h = self._hash_text(q_clean, "RETRIEVAL_QUERY")
        if h in self.cache:
            return self.cache[h]

        url = f"{self.api_url}/{self.model_name}:embedContent?key={self.api_key}"
        payload = {
            "content": {"parts": [{"text": q_clean}]},
            "outputDimensionality": self.dimensions,
            "taskType": "RETRIEVAL_QUERY"
        }

        max_retries = 5
        for attempt in range(max_retries):
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                vec = data.get("embedding", {}).get("values", [])
                if len(vec) != self.dimensions:
                    raise ValueError(f"Expected {self.dimensions} dim, got {len(vec)}")
                self.cache[h] = vec
                self._save_cache()
                return vec
            elif response.status_code == 429:
                wait_sec = 12 + attempt * 5
                print(f"[RateLimit] 429 on query embed. Waiting {wait_sec}s...")
                time.sleep(wait_sec)
            else:
                raise RuntimeError(f"Gemini API query error {response.status_code}: {response.text}")

        raise RuntimeError("Failed to embed query after retries.")
