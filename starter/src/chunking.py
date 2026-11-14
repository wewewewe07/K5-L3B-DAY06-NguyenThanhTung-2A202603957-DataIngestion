"""Implement fixed-size (Strategy A) and structure-aware (Strategy B & C) chunking."""

from __future__ import annotations
import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int = 600, overlap: int = 80) -> list[Chunk]:
    """Strategy A: Split text into fixed-size overlapping character windows.

    - Mechanical windowing without awareness of sentence or paragraph structure.
    - Preserves document_id, source, page, and filter metadata.
    - Stable chunk_id format: A_{doc_id}_p{page}_c{chunk_index}.
    """
    text = page.text
    if not text:
        return []

    if size <= overlap:
        raise ValueError(f"Chunk size ({size}) must be strictly greater than overlap ({overlap})")

    chunks: list[Chunk] = []
    step = size - overlap
    chunk_index = 0

    for start in range(0, len(text), step):
        end = min(start + size, len(text))
        window_text = text[start:end].strip()

        if window_text:
            chunk_id = f"A_{page.document_id}_p{page.page:02d}_c{chunk_index:02d}"
            metadata = {
                **page.metadata,
                "strategy": "A",
                "chunk_index": chunk_index,
                "char_length": len(window_text),
                "start_char": start,
                "end_char": end,
            }
            chunks.append(Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=window_text,
                metadata=metadata
            ))
            chunk_index += 1

        if end >= len(text):
            break

    return chunks


def _split_long_paragraph(text: str, max_size: int) -> list[str]:
    """Split an oversized paragraph into sentences, fallback to word boundaries if needed."""
    sentences = re.split(r"(?<=[.?!])\s+", text)
    sub_chunks: list[str] = []
    current_sentences: list[str] = []
    current_len = 0

    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue

        # If a single sentence itself is larger than max_size, split by words
        if len(s_clean) > max_size:
            if current_sentences:
                sub_chunks.append(" ".join(current_sentences))
                current_sentences = []
                current_len = 0

            words = s_clean.split(" ")
            w_buf: list[str] = []
            w_len = 0
            for w in words:
                if w_len + len(w) + 1 > max_size and w_buf:
                    sub_chunks.append(" ".join(w_buf))
                    w_buf = [w]
                    w_len = len(w)
                else:
                    w_buf.append(w)
                    w_len += len(w) + (1 if w_len > 0 else 0)
            if w_buf:
                sub_chunks.append(" ".join(w_buf))
            continue

        # Normal sentence grouping
        if current_len + len(s_clean) + 1 > max_size and current_sentences:
            sub_chunks.append(" ".join(current_sentences))
            current_sentences = [s_clean]
            current_len = len(s_clean)
        else:
            current_sentences.append(s_clean)
            current_len += len(s_clean) + (1 if current_len > 0 else 0)

    if current_sentences:
        sub_chunks.append(" ".join(current_sentences))

    return sub_chunks


def by_paragraph(page: DocumentPage, max_size: int = 900) -> list[Chunk]:
    """Strategy B & C: Structure-aware chunking respecting paragraph & sentence boundaries.

    - Splits on natural paragraph breaks (\\n\\n).
    - Merges consecutive small paragraphs up to max_size for topical cohesion.
    - Splits oversized paragraphs at sentence or word boundaries.
    - Stable chunk_id format: B_{doc_id}_p{page}_c{chunk_index}.
    """
    text = page.text
    if not text:
        return []

    raw_paragraphs = text.split("\n\n")
    paragraphs: list[str] = []

    # Flatten any oversized paragraphs into sentence/word-bounded pieces <= max_size
    for p in raw_paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        if len(p_clean) > max_size:
            paragraphs.extend(_split_long_paragraph(p_clean, max_size))
        else:
            paragraphs.append(p_clean)

    chunks: list[Chunk] = []
    chunk_index = 0
    current_group: list[str] = []
    current_len = 0

    for p in paragraphs:
        # Check if adding this paragraph exceeds max_size
        candidate_len = current_len + len(p) + (2 if current_group else 0)
        if candidate_len > max_size and current_group:
            combined = "\n\n".join(current_group).strip()
            chunk_id = f"B_{page.document_id}_p{page.page:02d}_c{chunk_index:02d}"
            metadata = {
                **page.metadata,
                "strategy": "B",  # Strategy C shares the exact same chunk corpus
                "chunk_index": chunk_index,
                "char_length": len(combined),
            }
            chunks.append(Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=combined,
                metadata=metadata
            ))
            chunk_index += 1
            current_group = [p]
            current_len = len(p)
        else:
            current_group.append(p)
            current_len += len(p) + (2 if current_len > 0 else 0)

    if current_group:
        combined = "\n\n".join(current_group).strip()
        chunk_id = f"B_{page.document_id}_p{page.page:02d}_c{chunk_index:02d}"
        metadata = {
            **page.metadata,
            "strategy": "B",
            "chunk_index": chunk_index,
            "char_length": len(combined),
        }
        chunks.append(Chunk(
            chunk_id=chunk_id,
            document_id=page.document_id,
            source=page.source,
            page=page.page,
            text=combined,
            metadata=metadata
        ))

    return chunks
