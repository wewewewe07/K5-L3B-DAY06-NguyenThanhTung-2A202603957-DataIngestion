#!/usr/bin/env python3
"""Script to extract metadata, page-level information, and generate data/manifest.json

from data/raw/Explanable_AI_survey.pdf.

Usage:
    python data/src/extract_manifest.py
"""

from __future__ import annotations
import json
from pathlib import Path
import pypdf


def generate_manifest() -> Path:
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent.parent  # K5-L3B-DAY06-2A202603957-DataIngestion

    pdf_path = base_dir / "data" / "raw" / "Explanable_AI_survey.pdf"
    manifest_path = base_dir / "data" / "manifest.json"

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    reader = pypdf.PdfReader(str(pdf_path))
    total_physical_pages = len(reader.pages)

    # Detailed section and category mapping for every physical page
    page_sections = {
        1: ("1. Introduction", "introduction"),
        2: ("2. Background and Motivation", "background"),
        3: ("2. Background and Motivation (Terminology & Need)", "background"),
        4: ("2. Background and Motivation (Stakeholders & Interpretability)", "background"),
        5: ("3. Categories of Explainability Techniques", "taxonomy"),
        6: ("3. Categories of Explainability Techniques (Perturbation & Gradient)", "taxonomy"),
        7: ("4. Detailed Discussions on XAI Techniques (LIME, SHAP)", "techniques_perturbation"),
        8: ("4. Detailed Discussions on XAI Techniques (CFE & Taxonomy Tree)", "techniques_perturbation"),
        9: ("4. Detailed Discussions on XAI Techniques (Saliency Map, LRP)", "techniques_gradient"),
        10: ("4. Detailed Discussions on XAI Techniques (CAM & Integrated Gradients)", "techniques_gradient"),
        11: ("4. Detailed Discussions on XAI Techniques (Transformers & Attention)", "techniques_transformers"),
        12: ("4. Detailed Discussions on XAI Techniques (Reinforcement Learning) & Summary", "techniques_rl"),
        13: ("5. XAI Techniques in Application Areas (Overview & Summary Table)", "applications_nlp"),
        14: ("5. XAI Techniques in Application Areas (NLP & Fine-Tuning)", "applications_nlp"),
        15: ("5. XAI Techniques in Application Areas (Prompting & Attention in NLP)", "applications_nlp"),
        16: ("5. XAI Techniques in Application Areas (Computer Vision & CNNs)", "applications_cv"),
        17: ("5. XAI Techniques in Application Areas (Vision Transformers & Time Series)", "applications_cv_timeseries"),
        18: ("5. XAI Techniques in Application Areas (Time Series Methods)", "applications_timeseries"),
        19: ("5. XAI Techniques in Application Areas (Time Series Case Studies & Healthcare)", "applications_healthcare"),
        20: ("5. XAI Techniques in Application Areas (Healthcare Summary & Autonomous Vehicles)", "applications_healthcare_av"),
        21: ("5. XAI Techniques in Application Areas (Autonomous Vehicles, Chemistry, Physics)", "applications_science"),
        22: ("5. XAI Techniques in Application Areas (AV Summary & Key Insights)", "applications_science"),
        23: ("6. XAI Evaluation Methods (Human & Computer-Centered)", "evaluation"),
        24: ("6. XAI Evaluation Methods (Fidelity, Consistency, Robustness, Efficiency)", "evaluation"),
        25: ("7. Future Research Direction (Complexity, Evaluation, Security)", "future_directions"),
        26: ("7. Future Research Direction (Multilingual) & 8. Conclusion", "future_directions_conclusion"),
        27: ("References ([1]-[39])", "references"),
        28: ("References ([40]-[97])", "references"),
        29: ("References ([98]-[153])", "references"),
        30: ("References ([154]-[198])", "references"),
        31: ("References ([199]-[205])", "references"),
    }

    pages_list = []
    total_chars = 0
    content_chars = 0

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        raw_text = page.extract_text() or ""
        chars = len(raw_text)
        total_chars += chars

        is_content = page_num <= 26
        if is_content:
            content_chars += chars

        sec, cat = page_sections.get(page_num, ("Unknown", "general"))
        pages_list.append({
            "page": page_num,
            "section": sec,
            "category": cat,
            "characters": chars,
            "is_content_page": is_content,
            "preview": raw_text.strip()[:100].replace("\n", " "),
        })

    manifest = {
        "source_id": "XAI_survey_2025",
        "title": "Explainable Artificial Intelligence: A Survey of Needs, Techniques, Applications, and Future Direction",
        "authors": [
            "Melkamu Mersha",
            "Khang Lam",
            "Joseph Wood",
            "Ali AlShami",
            "Jugal Kalita",
        ],
        "affiliations": [
            "College of Engineering and Applied Science, University of Colorado Colorado Springs, CO, USA",
            "College of Information and Communication Technology, Can Tho University, Can Tho, Vietnam",
        ],
        "source_path": "data/raw/Explanable_AI_survey.pdf",
        "source_url": "https://arxiv.org/abs/2409.00265",
        "arxiv_id": "arXiv:2409.00265v2 [cs.AI]",
        "publication_date": "2025-01-13",
        "license_or_permission": "arXiv.org perpetual non-exclusive license / Open Access for academic and research evaluation",
        "accessed_at": "2026-11-14",
        "total_physical_pages": total_physical_pages,
        "valid_content_pages": 26,
        "content_pages_range": "1-26",
        "reference_pages_count": 5,
        "reference_pages_range": "27-31",
        "page_counting_rule": (
            "Pages 1-26 represent core survey body text across 8 primary sections "
            "(Introduction, Background, Taxonomy, XAI Techniques, Applications in NLP/CV/TimeSeries/Healthcare/AV/Science, "
            "Evaluation, Future Directions, Conclusion). Pages 27-31 are bibliographic reference entries [1]-[205]. "
            "Total narrative content equals 135,650 characters, equivalent to ~90 standardized 1,500-char content units."
        ),
        "total_characters": total_chars,
        "content_characters": content_chars,
        "metadata_fields": [
            "document_id",
            "source",
            "page",
            "section",
            "category",
        ],
        "supported_filter_categories": [
            "introduction",
            "background",
            "taxonomy",
            "techniques_perturbation",
            "techniques_gradient",
            "techniques_transformers",
            "techniques_rl",
            "applications_nlp",
            "applications_cv",
            "applications_timeseries",
            "applications_healthcare",
            "applications_science",
            "evaluation",
            "future_directions",
        ],
        "pages": pages_list,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Manifest created successfully at: {manifest_path}")
    return manifest_path


if __name__ == "__main__":
    generate_manifest()

