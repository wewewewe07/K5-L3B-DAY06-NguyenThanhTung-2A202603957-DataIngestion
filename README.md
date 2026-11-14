# Day 06 · Data Ingestion Engineering
## Tối ưu hóa Dữ liệu cho RAG & AI Agent — Khảo sát Thực nghiệm trên Khảo cứu XAI

- **Học viên:** Nguyễn Thành Tùng
- **MSSV:** 2A202603957
- **Lớp:** K5 - L3B
- **Corpus:** *Explainable Artificial Intelligence: A Survey of Needs, Techniques, Applications, and Future Direction* (`arXiv:2409.00265v2 [cs.AI]`, 31 trang vật lý, 26 trang nội dung cốt lõi, 134.155 ký tự ~ tương đương 90 đơn vị nội dung tiêu chuẩn).
- **Báo cáo cá nhân chi tiết:** [report/individual/2A202603957_NguyenThanhTung.md](report/individual/2A202603957_NguyenThanhTung.md)

---

## 🎯 Tổng quan bài Lab

Dự án hiện thực một pipeline hoàn chỉnh từ trích xuất tài liệu học thuật (PDF), chuẩn hóa Unicode/ngắt dòng, thử nghiệm **3 chiến lược dữ liệu (Data Strategies A, B, C)**, lưu trữ bền vững trong cơ sở dữ liệu **PostgreSQL 16 + pgvector 0.8.7** với embedding model thực tế **Google Gemini**, và đo lường khách quan bằng bộ **20 câu hỏi Benchmark (15 Dev / 5 Test)** cùng **đánh giá thủ công 5 khía cạnh**.

```
[Corpus PDF ≥30 trang] 
         │
         ├───► Chiến lược A (Fixed-size: 600 chars, overlap 80) ──────► PostgreSQL (Index A: 266 chunks) ──┐
         │                                                                                                  ├──► Benchmark 20 câu
         ├───► Chiến lược B (Theo đoạn văn / Heading: max 900) ────────► PostgreSQL (Index B: 175 chunks) ──┼──► Đo Hit@1, Hit@3
         │                                                                                                  │  ► Audit 5 khía cạnh
         └───► Chiến lược C (Giống B + SQL Metadata Filter khi query) ─► PostgreSQL (Index B + SQL Filter) ─┘
```

---

## 📊 Kết quả thực nghiệm chính

### 1. Độ chính xác truy xuất (Retrieval Accuracy)

| Chiến lược (Strategy) | Tập dữ liệu | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Số chunks | Thời gian truy xuất | Chi phí API |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Chiến lược A** *(Fixed 600)* | **Dev (15 câu)** | 10/15 (66.7%) | 11/15 (73.3%) | 266 | 0.506s | $0.00 |
| | **Test (5 câu)** | 3/5 (60.0%) | 3/5 (60.0%) | 266 | 0.506s | $0.00 |
| **Chiến lược B** *(Paragraph 900)* | **Dev (15 câu)** | 9/15 (60.0%) | **12/15 (80.0%)** | **175** | **0.406s** | $0.00 |
| | **Test (5 câu)** | 3/5 (60.0%) | 3/5 (60.0%) | **175** | **0.406s** | $0.00 |
| **Chiến lược C** *(B + Metadata Filter)* | **Dev (15 câu)** | 9/15 (60.0%) | **12/15 (80.0%)** | **175** | 0.429s | $0.00 |
| | **Test (5 câu)** | 3/5 (60.0%) | 3/5 (60.0%) | **175** | 0.429s | $0.00 |

### 2. Đánh giá chất lượng thủ công (Manual Audit trên 5 khía cạnh)

| Tiêu chí | Chiến lược A | Chiến lược B | Chiến lược C | Nhận xét chính |
|---|:---:|:---:|:---:|---|
| **Tính mạch lạc (Coherence) /2.0** | 0.60 / 2.0 | **1.60 / 2.0** | **1.60 / 2.0** | B và C giữ trọn vẹn câu/đoạn, không bị cắt cụt đầu/đuôi như A |
| **Metadata Đúng & Đủ** | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | `source`, `page`, `section`, `category` khớp chuẩn xác 100% |
| **Filter Compliance (Tuân thủ lọc)** | N/A | N/A | **3/3 (100%)** | Top-3 câu có filter (`q20`) thuộc đúng 100% danh mục `applications_science` |
| **Grounding Quality /2.0** | 1.20 / 2.0 | **1.40 / 2.0** | **1.40 / 2.0** | Cung cấp đủ bằng chứng và số trang để trả lời chính xác |

---

## ⚡ Hướng dẫn cài đặt & Tái lập (Reproducibility)

### Yêu cầu hệ thống:
- Python 3.9 – 3.12
- Docker Desktop hoặc Docker Engine (chạy PostgreSQL + pgvector)

### Bước 1: Khởi động Database
```bash
cd starter
# Sao chép file môi trường (nếu chưa có)
cp .env.example .env

# Khởi động PostgreSQL 16 + pgvector trên cổng 55433
docker-compose -p day6_student_starter up -d

# Kiểm tra kết nối database
python scripts/check_setup.py
```

### Bước 2: Cài đặt thư viện Python
```bash
pip install -r requirements.txt
```

### Bước 3: Chạy Ingestion & Benchmark
Bạn có thể chạy toàn bộ pipeline chỉ với 1 lệnh:
```bash
# Chạy pipeline tổng hợp
python -m src.run

# Hoặc chạy từng bước độc lập:
python scripts/test_chunking.py                  # Đo đạc chunking A vs B
python scripts/run_ingest.py                     # Nhúng vector & nạp vào PostgreSQL
python scripts/run_benchmark.py                  # Chạy 20 câu benchmark & xuất traces
python scripts/audit_coherence_and_grounding.py   # Chạy audit thủ công
```

---

## 📁 Cấu trúc thư mục bài nộp

```text
K5-L3B-DAY06-2A202603957-DataIngestion/
├── STUDENT.md                                      # Thông tin học viên & repo commit
├── README.md                                       # Hướng dẫn setup, kết quả và lệnh chạy
├── artifacts/
│   └── experiment_log.csv                          # Nhật ký thí nghiệm và giả thuyết A/B/C
├── benchmark/
│   └── questions.json                              # 20 câu hỏi có gold evidence (15 dev / 5 test)
├── data/
│   ├── manifest.json                               # Manifest dữ liệu, bản quyền, quy tắc tính trang
│   ├── raw/
│   │   └── Explanable_AI_survey.pdf                # File tài liệu PDF gốc (31 trang)
│   └── src/
│       ├── build_benchmark.py                      # Script sinh và kiểm chứng 20 câu hỏi
│       └── extract_manifest.py                     # Script trích xuất metadata từ PDF
├── results/                                        # Kho lưu trữ kết quả thực nghiệm và audit
│   ├── benchmark_summary.json                      # Bảng tổng kết số liệu Hit@1 / Hit@3
│   ├── traces_strategy_A.json                      # Vết truy xuất Top-3 Chiến lược A
│   ├── traces_strategy_B.json                      # Vết truy xuất Top-3 Chiến lược B
│   ├── traces_strategy_C.json                      # Vết truy xuất Top-3 Chiến lược C
│   ├── manual_audit_coherence.json                 # Bảng chấm thủ công Coherence 10 vị trí
│   ├── manual_audit_grounding.json                 # Bảng chấm thủ công Grounding 5 câu test
│   ├── manual_audit_metadata.json                  # Bảng kiểm tra tính chính xác của metadata
│   ├── chunks_strategy_A.json                      # Danh sách 266 chunks Chiến lược A
│   └── chunks_strategy_B.json                      # Danh sách 175 chunks Chiến lược B
├── report/
│   └── individual/
│       └── 2A202603957_NguyenThanhTung.md          # Báo cáo cá nhân chi tiết theo mẫu
└── starter/
    ├── docker-compose.yml                          # Cấu hình container PostgreSQL + pgvector
    ├── init.sql                                    # Bật extension vector
    ├── requirements.txt                            # Dependencies
    ├── .env.example                                # Cấu hình mẫu
    ├── scripts/                                    # Các script chạy độc lập
    └── src/                                        # Mã nguồn chính do học viên phát triển
        ├── models.py                               # Dataclass DocumentPage và Chunk
        ├── ingestion.py                            # Đọc PDF, chuẩn hóa Unicode/ngắt dòng
        ├── chunking.py                             # Thuật toán fixed_size và by_paragraph
        ├── embeddings.py                           # Adapter Gemini Embeddings có Disk Cache
        ├── store.py                                # PgVectorStore (Upsert & SQL Filter search)
        ├── evaluation.py                           # Đánh giá Hit@1/Hit@3 và trace
        └── run.py                                  # Entry point thực thi pipeline
```

---

## ✅ Checklist nghiệm thu bài nộp (100% Completed)

- [x] **Dữ liệu ≥30 trang/đơn vị nội dung hợp lệ:** Bài báo 31 trang vật lý, 26 trang nội dung cốt lõi, 134.155 ký tự (~90 đơn vị nội dung tiêu chuẩn), có `data/manifest.json`.
- [x] **≥20 câu benchmark:** 20 câu hỏi chia trước 15 dev / 5 test, có `gold_page` và `evidence_quote` đối chiếu chuẩn 100%, có 3 câu metadata filter.
- [x] **Embedding model thật & Vector store thật:** Google Gemini Embedding `models/gemini-embedding-001` (768 chiều) + PostgreSQL 16 + pgvector 0.8.7 (Docker local).
- [x] **Ba cấu hình A, B, C kiểm soát tốt:** B và C dùng chung 175 chunks, chỉ khác nhau duy nhất ở cơ chế Metadata Filter khi truy xuất.
- [x] **Lưu đầy đủ traces Top-3:** Lưu tại `results/traces_strategy_*.json` cho cả 3 chiến lược.
- [x] **Audit thủ công 5 khía cạnh:** Bảng chấm 10 vị trí Coherence, 15 bản ghi Metadata, 5 câu Grounding Quality, phân tích 2 ca lỗi thất bại.
- [x] **Mã nguồn, nhật ký thí nghiệm & Báo cáo cá nhân:** Đã hoàn thiện `STUDENT.md`, `artifacts/experiment_log.csv`, `report/individual/2A202603957_NguyenThanhTung.md` và mã nguồn trong `starter/src/`.
- [x] **Bảo mật:** File `.env` chứa API key được đưa vào `.gitignore`, không lộ thông tin nhạy cảm.
