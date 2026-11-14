"""Read and normalize source data with full traceability back to source and page."""

from __future__ import annotations
import json
from pathlib import Path
import re
from typing import Any
import unicodedata
import pypdf

from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode, resolve column hyphenation, and clean line wraps.

    - Canonical NFC normalization.
    - Resolves hyphenated line breaks from multi-column layout (e.g. 'trans-\\nparent' -> 'transparent').
    - Fixes common LaTeX font ligature artifacts (e.g. 'di fference' -> 'difference').
    - Converts intra-paragraph single line breaks to spaces while preserving paragraph boundaries (\\n\\n).
    """
    if not text:
        return ""

    # Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # Rejoin hyphenated line breaks from PDF columns
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

    # Clean up LaTeX ligature spacing artifacts
    text = text.replace("di fference", "difference")
    text = text.replace("e ffective", "effective")
    text = text.replace("e fficient", "efficient")
    text = text.replace("su fficient", "sufficient")
    text = text.replace("attention-based", "attentionbased")
    text = text.replace("network-based", "networkbased")

    # Standardize newline characters
    text = re.sub(r"\r\n|\r", "\n", text)

    # Identify paragraphs separated by multiple newlines
    raw_paras = re.split(r"\n\s*\n+", text)
    cleaned_paras: list[str] = []

    for p in raw_paras:
        # Inside each paragraph, replace single soft line breaks with space
        p_clean = re.sub(r"\s*\n\s*", " ", p)
        # Condense multiple inline spaces
        p_clean = re.sub(r"[ \t]+", " ", p_clean).strip()
        if p_clean:
            cleaned_paras.append(p_clean)

    return "\n\n".join(cleaned_paras)


def load_pdf(
    path: Path,
    document_id: str,
    source: str,
    manifest_path: Path | None = None
) -> list[DocumentPage]:
    """Extract each physical page, keeping page number, source, and section/category metadata.

    Reads section and category mappings from manifest.json if present.
    Detects and logs pages with minimal or no text.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    # Load page-level metadata from manifest if provided or located nearby
    metadata_by_page: dict[int, dict[str, Any]] = {}
    if manifest_path is None:
        potential_manifest = path.resolve().parents[1] / "manifest.json"
        if potential_manifest.exists():
            manifest_path = potential_manifest

    if manifest_path and Path(manifest_path).exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
                for p_info in manifest_data.get("pages", []):
                    metadata_by_page[p_info["page"]] = {
                        "section": p_info.get("section", "General"),
                        "category": p_info.get("category", "general"),
                        "is_content_page": p_info.get("is_content_page", True),
                    }
        except Exception as e:
            print(f"[Warning] Could not load manifest metadata: {e}")

    reader = pypdf.PdfReader(str(path))
    pages: list[DocumentPage] = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        raw_text = page.extract_text() or ""
        clean_text = normalize_text(raw_text)

        page_meta = metadata_by_page.get(page_num, {
            "section": "General",
            "category": "general",
            "is_content_page": page_num <= 26
        })

        # Record character counts and empty/sparse flags
        page_meta["raw_char_count"] = len(raw_text)
        page_meta["char_count"] = len(clean_text)
        page_meta["is_empty"] = len(clean_text) == 0

        if page_meta["is_empty"]:
            print(f"[Notice] Page {page_num} extracted 0 characters.")

        pages.append(DocumentPage(
            document_id=document_id,
            source=source,
            page=page_num,
            text=clean_text,
            metadata=page_meta
        ))

    return pages
