#!/usr/bin/env python3
"""Build and strictly verify the 20 Benchmark questions for Day 06 Lab.

Requirements:
- >= 20 questions
- Split: 15 dev / 5 test
- Types: truc_tiep, dien_dat_lai, dieu_kien, metadata_filter
- At least 3 metadata_filter questions (with at least 1 in test)
- Every single evidence_quote is verified 100% against Explanable_AI_survey.pdf
"""

import json
from pathlib import Path
import re
import unicodedata
import pypdf


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    # Handle LaTeX ligatures and hyphenations
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    text = text.replace("di fference", "difference")
    text = text.replace("e ffective", "effective")
    text = text.replace("e fficient", "efficient")
    text = text.replace("su fficient", "sufficient")
    text = text.replace("attention-based", "attentionbased")
    text = text.replace("network-based", "networkbased")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def build_and_verify_benchmark():
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent.parent  # K5-L3B-DAY06-2A202603957-DataIngestion
    pdf_path = base_dir / "data" / "raw" / "Explanable_AI_survey.pdf"
    benchmark_dir = base_dir / "benchmark"
    benchmark_file = benchmark_dir / "questions.json"

    reader = pypdf.PdfReader(str(pdf_path))

    # Pre-extract normalized text for each page
    pages_text = {}
    for idx, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        pages_text[idx + 1] = normalize(raw)

    questions = [
        # --- DEV SET (15 questions: q01 - q15) ---
        {
            "id": "q01",
            "split": "dev",
            "type": "truc_tiep",
            "question": "Why do artificial intelligence models encounter significant challenges in safety-critical domains such as healthcare and autonomous vehicles?",
            "expected_answer": "Artificial intelligence models face major challenges due to their black-box nature, especially in safety-critical domains like healthcare, finance, and autonomous vehicles.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 1,
            "evidence_quote": "Artificial intelligence models encounter significant challenges due to their black-box nature, particularly in safety-critical domains such as healthcare, finance, and autonomous vehicles.",
            "filter": None
        },
        {
            "id": "q02",
            "split": "dev",
            "type": "truc_tiep",
            "question": "What role does XAI play in fostering social collaboration and human-machine interaction?",
            "expected_answer": "XAI plays a significant role by increasing trustworthiness, reliability, and responsibility of AI systems, helping reduce negative impacts such as unethical use, discrimination, and biases.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 4,
            "evidence_quote": "fostering social collaboration and human-machine interactions [2] by increasing the trustworthiness, reliability, and responsibility of AI systems, helping reduce the negative impacts such as unethical use of AI systems, discrimination, and biases.",
            "filter": None
        },
        {
            "id": "q03",
            "split": "dev",
            "type": "dien_dat_lai",
            "question": "What is the critical timing difference between ante-hoc and post-hoc explanation techniques?",
            "expected_answer": "The critical difference between them is the stage in which they are implemented during the AI system life cycle.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 5,
            "evidence_quote": "Ante-hoc and post-hoc explanation techniques are two different ways to explain the inner workings of AI systems. The critical difference between them is the stage in which they are implemented [7].",
            "filter": None
        },
        {
            "id": "q04",
            "split": "dev",
            "type": "truc_tiep",
            "question": "Why may model-specific post-hoc explanation techniques fail to generalize across different AI architectures?",
            "expected_answer": "Model-specific approaches explain decisions based on a specific model's internal structure and design, so they may not apply to other models with varying architectures.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 5,
            "evidence_quote": "Model-specific approaches provide explanations for the predictions or decisions made by a specific AI model, based on the model’s internal working structure and design. These techniques may not apply to other models with varying architectures",
            "filter": None
        },
        {
            "id": "q05",
            "split": "dev",
            "type": "truc_tiep",
            "question": "What do gradients represent in gradient-based XAI methods and how is feature importance determined?",
            "expected_answer": "Gradients reflect output sensitivity to input feature changes; higher gradient values imply greater importance for the prediction.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 7,
            "evidence_quote": "These gradients reflect the sensitivity of the model’s output to changes in each input feature [53]. A higher gradient value for an input feature implies greater importance for the model’s prediction.",
            "filter": None
        },
        {
            "id": "q06",
            "split": "dev",
            "type": "dieu_kien",
            "question": "What property must be satisfied by the explanation model g(x') under the local accuracy requirement of SHAP?",
            "expected_answer": "Local accuracy requires that the explanation model g(x') matches the original model f(x) for a given input x'.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 8,
            "evidence_quote": "“local accuracy” requires that the explanation modelg(x′) matches the original model f (x)",
            "filter": None
        },
        {
            "id": "q07",
            "split": "dev",
            "type": "truc_tiep",
            "question": "What does the conservation property mandate in Layer-wise Relevance Propagation (LRP)?",
            "expected_answer": "A neuron receiving a relevance score must redistribute that score to the lower layer in an equal amount.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 10,
            "evidence_quote": "LRP is subject to the conservation property, which means a neuron that receives the relevance score must be redistributed to the lower layer in an equal amount.",
            "filter": None
        },
        {
            "id": "q08",
            "split": "dev",
            "type": "dieu_kien",
            "question": "In what safety-critical areas can the failure of Reinforcement Learning agents lead to catastrophic consequences?",
            "expected_answer": "In safety-critical areas like autonomous vehicles, healthcare, and energy systems.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 12,
            "evidence_quote": "various domains, including safety-critical areas like autonomous vehicles, healthcare, and energy systems [70, 71]. In the domain of autonomous vehicles, RL is employed to refine adaptive cruise control and lane-keeping",
            "filter": None
        },
        {
            "id": "q09",
            "split": "dev",
            "type": "truc_tiep",
            "question": "Why are transparent models easy to interpret for human users in NLP tasks?",
            "expected_answer": "Because their internal mechanisms and decision-making processes are designed to be inherently understandable.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 14,
            "evidence_quote": "Transparent models are easy to interpret because their internal mechanisms and decision-making processes are designed to be inherently understandable [10].",
            "filter": None
        },
        {
            "id": "q10",
            "split": "dev",
            "type": "dien_dat_lai",
            "question": "Into what architectural categories are computer vision models classified for explainability purposes?",
            "expected_answer": "Convolutional Neural Network-based models (CNNs) and attention-based models such as Vision Transformers (ViTs).",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 16,
            "evidence_quote": "models can be categorized into Convolutional Neural Network-based models (CNNs) and attention-based models, such as Vision Transformers (ViTs), based on their architecture.",
            "filter": None
        },
        {
            "id": "q11",
            "split": "dev",
            "type": "truc_tiep",
            "question": "What is TSViz and what does it help users explore in time series data?",
            "expected_answer": "TSViz is a model-agnostic visualization toolkit that helps users explore and comprehend complex time series data regardless of model type.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 18,
            "evidence_quote": "TSViz (Time Series Visualization) is a model-agnostic set of visualization techniques that help users explore and comprehend complex time series data, regardless of the type of model used for analysis [125].",
            "filter": None
        },
        {
            "id": "q12",
            "split": "dev",
            "type": "dieu_kien",
            "question": "Into which two major categories are XAI system evaluation methods classified?",
            "expected_answer": "Human-centered and computer-centered categories based on applications and methodologies.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 23,
            "evidence_quote": "XAI system evaluation methods are classified into human-centered and computer-centered categories based on their applications and methodologies to judge",
            "filter": None
        },
        {
            "id": "q13",
            "split": "dev",
            "type": "truc_tiep",
            "question": "How is fidelity defined as a quantitative dimension in XAI evaluation?",
            "expected_answer": "Fidelity refers to how close the provided XAI explanations are to the actual decision made by a model.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 23,
            "evidence_quote": "Fidelity refers to how the provided XAI explanations are close to the actual decision made by a model focusing on the accuracy of representation",
            "filter": None
        },
        {
            "id": "q14",
            "split": "dev",
            "type": "metadata_filter",
            "question": "Why is healthcare considered a critical domain requiring explainable decision-making?",
            "expected_answer": "Due to the high risks and complexities of the medical decision-making process.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 19,
            "evidence_quote": "Healthcare is a critical domain due to the high risks and complexities of the medical decision-making process.",
            "filter": {"category": "applications_healthcare"}
        },
        {
            "id": "q15",
            "split": "dev",
            "type": "metadata_filter",
            "question": "How can explanation stability be quantitatively represented over multiple runs?",
            "expected_answer": "Stability can be represented by the variance in explanations over multiple runs with the same input.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 24,
            "evidence_quote": "Stability can be represented by the variance in explanations over multiple runs with the same input.",
            "filter": {"category": "evaluation"}
        },

        # --- TEST SET (5 questions: q16 - q20) ---
        {
            "id": "q16",
            "split": "test",
            "type": "truc_tiep",
            "question": "What does Percentage Drop in Confidence (PDC) measure in rationale sufficiency evaluation?",
            "expected_answer": "It measures the percentage decrease in confidence when using the rationale compared to the full input.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 24,
            "evidence_quote": "Percentage Drop in Confidence (PDC): It measures the percentage decrease in confidence when using the rationale compared to the full input.",
            "filter": None
        },
        {
            "id": "q17",
            "split": "test",
            "type": "dien_dat_lai",
            "question": "How does high architectural complexity in deep neural networks impact the effectiveness of XAI techniques?",
            "expected_answer": "XAI techniques are often less effective with highly complex models, making complexity reduction without sacrificing accuracy a major challenge.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 25,
            "evidence_quote": "XAI techniques are often less effective with highly complex models [48]. Developing AI models by reducing complexity without compromising much on accuracy is a challenging task.",
            "filter": None
        },
        {
            "id": "q18",
            "split": "test",
            "type": "dieu_kien",
            "question": "What data stream and latency conditions make real-time explanations in autonomous cars challenging?",
            "expected_answer": "Autonomous cars receive continuous data streams from sensors, lidars, and radars with strict latency constraints, demanding efficient real-time XAI algorithms.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 25,
            "evidence_quote": "autonomous cars have continuous and constant data streams from various sources, such as sensors, lidars, and radars with latency constraints.",
            "filter": None
        },
        {
            "id": "q19",
            "split": "test",
            "type": "truc_tiep",
            "question": "Why are multilingual and multicultural XAI methods necessary when deploying large AI models in diverse societal environments?",
            "expected_answer": "They provide meaningful explanations addressing cultural variations, regional preferences, and language diversities to mitigate harmful biases and uphold cultural norms.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 26,
            "evidence_quote": "suitable XAI methods are crucial to providing meaningful model explanations for cultural variations, regional preferences, and language diversities that allow us to address harmful biases and keep sensitive cultural norms in diverse societal environments.",
            "filter": None
        },
        {
            "id": "q20",
            "split": "test",
            "type": "metadata_filter",
            "question": "What sensor and communication modalities enhance AI-driven autonomous vehicle systems?",
            "expected_answer": "Visual, spatial, temporal, audio, environmental, communication, genetic, and textual modalities.",
            "gold_source_id": "XAI_survey_2025",
            "gold_page": 21,
            "evidence_quote": "autonomous vehicles, including visual, spatial, temporal, audio, environmental, communication, genetic, and textual. The advancements significantly enhance the AI-driven autonomous vehicle system",
            "filter": {"category": "applications_science"}
        }
    ]

    # Strict Verification
    print("--- Verifying all 20 questions against PDF text ---")
    verified_count = 0
    for q in questions:
        p_num = q["gold_page"]
        p_txt = pages_text[p_num]
        ev = normalize(q["evidence_quote"])
        if ev in p_txt:
            verified_count += 1
            print(f"[VERIFIED] {q['id']} ({q['split']:4s} | {q['type']:15s}) Page {p_num:2d} -> OK")
        else:
            print(f"[FAILED]   {q['id']} ({q['split']}) on Page {p_num}")
            print(f"   Missing text: {ev[:100]}...")

    if verified_count != len(questions):
        raise ValueError(f"Only {verified_count}/{len(questions)} verified! Fix failed questions before saving.")

    benchmark_dir.mkdir(parents=True, exist_ok=True)
    with open(benchmark_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"\nSUCCESS: All {len(questions)} questions strictly verified and saved to:")
    print(f"--> {benchmark_file}")
    return benchmark_file


if __name__ == "__main__":
    build_and_verify_benchmark()
