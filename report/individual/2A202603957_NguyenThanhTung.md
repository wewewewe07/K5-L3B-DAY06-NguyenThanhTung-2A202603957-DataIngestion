# Báo cáo cá nhân — Day 6 · Data Ingestion Engineering

- **Học viên:** Nguyễn Thành Tùng
- **MSSV:** 2A202603957
- **Lớp:** K5 - L3B
- **Corpus:** *Explainable Artificial Intelligence: A Survey of Needs, Techniques, Applications, and Future Direction* (arXiv:2409.00265v2)
- **Repo bài nộp:** https://github.com/wewewewe07/K5-L3B-DAY06-2A202603957-DataIngestion

---

## 1. Dữ liệu và pipeline

### 1.1. Chủ đề, nguồn/quyền, số trang và quy tắc tính trang
- **Chủ đề tài liệu:** Bài báo khoa học tổng quan (Survey Paper) toàn diện về Trí tuệ nhân tạo có thể giải thích (Explainable AI - XAI), bao gồm cơ sở lý thuyết, phân loại kỹ thuật (Perturbation vs Gradient), ứng dụng đa ngành (Y tế, Thị giác máy tính, Xe tự hành, Chuỗi thời gian), phương pháp đánh giá và hướng nghiên cứu tương lai.
- **Nguồn và bản quyền:** 
  - Nguồn gốc: arXiv preprint, mã số `arXiv:2409.00265v2 [cs.AI]` (cập nhật ngày 13/01/2025).
  - Tác giả: Melkamu Mersha, Khang Lam, Joseph Wood, Ali AlShami, Jugal Kalita (University of Colorado Colorado Springs & Đại học Cần Thơ).
  - Bản quyền / Giấy phép: arXiv Open Access (giấy phép phi độc quyền phân phối và sử dụng cho mục đích học thuật, nghiên cứu).
- **Số trang vật lý và quy tắc tính trang hợp lệ:**
  - Tổng số trang vật lý của file PDF: **31 trang** (176.118 ký tự thô).
  - Các trang nội dung cốt lõi: **26 trang** (từ Trang 1 đến Trang 26, bao gồm 8 phân mục chính từ Section 1 Introduction đến Section 8 Conclusion, tổng cộng **134.155 ký tự nội dung đã chuẩn hóa**).
  - Các trang loại trừ: **5 trang** (từ Trang 27 đến Trang 31, chỉ chứa danh mục tài liệu tham khảo 205 trích dẫn `[1]–[205]`).
  - **Quy tắc tính:** Theo hướng dẫn `GUIDE.md`, với 134.155 ký tự nội dung chuẩn hóa, tương đương **~90 đơn vị nội dung tiêu chuẩn** (1.500 ký tự/đơn vị), vượt xa yêu cầu tối thiểu ≥ 30 trang/đơn vị nội dung của bài Lab. Toàn bộ thông tin được ghi nhận minh bạch tại [data/manifest.json](../../data/manifest.json).

### 1.2. Chuẩn hóa dữ liệu, xử lý lỗi và giới hạn
- **Quy trình chuẩn hóa (`normalize_text` trong `starter/src/ingestion.py`):**
  - Chuẩn hóa Unicode về dạng chuẩn dựng sẵn `NFC` (`unicodedata.normalize('NFC', text)`).
  - Nối liền các từ bị ngắt dòng do bố cục PDF 2 cột sử dụng Regex: `re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)` (ví dụ: `inter-\npretability` ➔ `interpretability`, `trans-\nparent` ➔ `transparent`).
  - Xử lý các lỗi dính khoảng trắng do font ligature của LaTeX: sửa `di fference` ➔ `difference`, `e ffective` ➔ `effective`, `e fficient` ➔ `efficient`, `su fficient` ➔ `sufficient`.
  - Thay thế các ngắt dòng mềm (soft-wrap) bên trong đoạn văn thành khoảng trắng đơn, trong khi bảo toàn các dấu ngắt đoạn tự nhiên `\n\n` để phục vụ thuật toán chunking.
- **Xử lý lỗi và giới hạn:**
  - Không có trang nào bị rỗng text hoàn toàn (0 trang lỗi).
  - Giới hạn: Một số bảng biểu lớn (như Table 3 ở Trang 20 và Table 4 ở Trang 22) có cấu trúc dạng bảng phức tạp, khi trích xuất text dạng dòng thì các cột bị dàn phẳng; thuật toán chunking đã được tinh chỉnh để ngắt bảng theo từng khối nhỏ dưới 900 ký tự nhằm tránh tạo ra chunk khổng lồ.

### 1.3. Embedding Model, Vector Store, Metric, Lệnh chạy và Chi phí
- **Embedding Model:** Google Gemini `models/gemini-embedding-001` qua API chính thức.
  - Số chiều: **768 dimensions** (chuẩn hóa qua tham số `outputDimensionality: 768`).
  - Tách biệt tác vụ: `taskType: "RETRIEVAL_DOCUMENT"` khi nhúng chunks và `taskType: "RETRIEVAL_QUERY"` khi nhúng câu hỏi.
  - Tích hợp bộ nhớ đệm ổ đĩa ([embeddings_cache.json](../../starter/results/embeddings_cache.json)) và cơ chế Adaptive Backoff xử lý giới hạn 15 RPM.
- **Vector Store:** **PostgreSQL 16.16 + pgvector 0.8.7** chạy trên Docker container local.
  - Cổng kết nối: `127.0.0.1:55433` | Database: `day6_lab`.
  - Bảng lưu trữ: `document_chunks` với cột `embedding vector(768)`.
  - Chỉ mục (Indexes): Chỉ mục B-tree trên `strategy`, `category` và `page`.
  - Similarity Metric: Cosine Distance (`<=>`), điểm tương đồng Cosine Similarity = `1.0 - distance`.
- **Lệnh chạy:**
  - Khởi động DB: `docker-compose -p day6_student_starter up -d`
  - Ingest dữ liệu: `python starter/scripts/run_ingest.py`
  - Chạy Benchmark: `python starter/scripts/run_benchmark.py`
- **Chi phí:** **$0.00** (Hoàn toàn nằm trong hạn mức Gemini API Free Tier).

### 1.4. Metadata bắt buộc và trường lọc bổ sung
- **Metadata bắt buộc:** `document_id` (`XAI_survey_2025`), `source` (`data/raw/Explanable_AI_survey.pdf`), `page` (từ 1 đến 31).
- **Trường lọc bổ sung (`category`):**
  - Các giá trị hợp lệ: `introduction`, `background`, `taxonomy`, `techniques_perturbation`, `techniques_gradient`, `techniques_transformers`, `techniques_rl`, `applications_nlp`, `applications_cv`, `applications_timeseries`, `applications_healthcare`, `applications_science`, `evaluation`, `future_directions`.
  - Nguồn giá trị: Trích xuất trực tiếp từ các tiêu đề chương mục chính của bài báo.
  - Lý do chọn: Giúp AI Agent hoặc người dùng có thể khoanh vùng tìm kiếm trong các bài toán domain cụ thể (ví dụ: chỉ tìm kỹ thuật XAI trong y tế `applications_healthcare` hoặc đánh giá độ tin cậy `evaluation`), loại bỏ 100% các trang tài liệu không liên quan.

---

## 2. Cấu hình và benchmark

### 2.1. Ba cấu hình A / B / C (Khác biệt duy nhất B–C)
- **Cấu hình A (Fixed-size Window):**
  - Kích thước chunk: Cố định **600 ký tự**, overlap **80 ký tự**.
  - Cắt trượt cơ học, không quan tâm ranh giới câu hay đoạn. Sinh ra **266 chunks**.
  - Truy xuất: Tìm kiếm vector thuần túy, **không áp dụng metadata filter**.
- **Cấu hình B (Structure-aware Paragraph):**
  - Kích thước chunk: Tách theo đoạn văn `\n\n`, ngắt câu thông minh tại dấu chấm câu với giới hạn trần **900 ký tự**.
  - Bảo toàn trọn vẹn ngữ nghĩa từng luận điểm. Sinh ra **175 chunks** (giảm 34.2% so với A).
  - Truy xuất: Tìm kiếm vector thuần túy, **không áp dụng metadata filter**.
- **Cấu hình C (Structure-aware + Metadata Filter):**
  - Dữ liệu chunk: **Giống hệt Cấu hình B 100%** (dùng chung index 175 chunks trong PostgreSQL).
  - **Khác biệt duy nhất B–C:** Khi câu hỏi có metadata filter, Cấu hình C kích hoạt mệnh đề SQL `AND category = %s` để lọc cứng trước khi xếp hạng vector. Với các câu hỏi không có filter, C chạy giống hệt B.

### 2.2. Bộ câu hỏi Benchmark (≥20 câu, 15 Dev / 5 Test)
- Xây dựng 20 câu hỏi độc lập được chốt cố định trong [benchmark/questions.json](../../benchmark/questions.json) trước khi chạy pipeline:
  - **15 câu Dev (`q01` – `q15`):** Dùng để thử nghiệm và phân tích. Có 2 câu kiểm tra metadata filter (`q14`, `q15`).
  - **5 câu Test (`q16` – `q20`):** Giữ nguyên làm tập kiểm tra mù (Holdout). Có 1 câu kiểm tra metadata filter (`q20`).
- Phân bố dạng câu hỏi: 10 câu trực tiếp (`truc_tiep`), 3 câu diễn đạt lại (`dien_dat_lai`), 4 câu điều kiện/ngoại lệ (`dieu_kien`), 3 câu lọc (`metadata_filter`).
- Toàn bộ 20 câu hỏi đều có `gold_page` và `evidence_quote` được script [verify_questions.py](../../data/src/verify_questions.py) kiểm chứng tồn tại chính xác nguyên văn 100% trên trang nguồn.

### 2.3. Tiêu chí chọn chiến lược chốt trước khi xem Test
1. **Tiêu chí 1 (Chất lượng):** Ưu tiên cấu hình có `Evidence Hit@3` cao nhất trên tập Dev.
2. **Tiêu chí 2 (Ngữ cảnh):** Ưu tiên tính mạch lạc của chunk (Chunk Coherence) để tránh hiện tượng cắt cụt câu làm suy giảm khả năng trả lời của LLM sau này.
3. **Tiêu chí 3 (Tài nguyên):** Ưu tiên số lượng chunk ít hơn để tiết kiệm chi phí lưu trữ vector và tăng tốc độ truy vấn.

---

## 3. Kết quả

### 3.1. Bảng đo lường Retrieval Accuracy (Tập Dev & Tập Test)

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian truy xuất | Chi phí API |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** *(Fixed 600)* | Dev (15) | 10/15 (66.7%) | 11/15 (73.3%) | 266 | 0.506s | $0.00 |
| **A** *(Fixed 600)* | Test (5) | 3/5 (60.0%) | 3/5 (60.0%) | 266 | 0.506s | $0.00 |
| **B** *(Paragraph 900)* | Dev (15) | 9/15 (60.0%) | **12/15 (80.0%)** | **175** | **0.406s** | $0.00 |
| **B** *(Paragraph 900)* | Test (5) | 3/5 (60.0%) | 3/5 (60.0%) | **175** | **0.406s** | $0.00 |
| **C** *(B + Filter)* | Dev (15) | 9/15 (60.0%) | **12/15 (80.0%)** | **175** | 0.429s | $0.00 |
| **C** *(B + Filter)* | Test (5) | 3/5 (60.0%) | 3/5 (60.0%) | **175** | 0.429s | $0.00 |

### 3.2. Bảng kết quả Audit thủ công 4 khía cạnh chất lượng

| Strategy | Coherence trung bình /2.0 (n=10) | Metadata đủ và đúng (n/15) | Filter tuân thủ (n/N) | Grounding Quality 0/1/2 và Trung bình /2.0 |
|:---:|:---:|:---:|:---:|:---:|
| **A** | 0.60 / 2.0 (n=10) | 15/15 (100.0%) | N/A *(Không lọc)* | 2 câu mức 0, 0 câu mức 1, 3 câu mức 2 ➔ **1.20 / 2.0** |
| **B** | **1.60 / 2.0** (n=10) | 15/15 (100.0%) | N/A *(Không lọc)* | 1 câu mức 0, 1 câu mức 1, 3 câu mức 2 ➔ **1.40 / 2.0** |
| **C** | **1.60 / 2.0** (n=10) | 15/15 (100.0%) | **3/3 (100.0%)** | 1 câu mức 0, 1 câu mức 1, 3 câu mức 2 ➔ **1.40 / 2.0** |

- **Đường dẫn artifacts kiểm chứng:**
  - Trace chi tiết: [traces_strategy_A.json](../../starter/results/traces_strategy_A.json), [traces_strategy_B.json](../../starter/results/traces_strategy_B.json), [traces_strategy_C.json](../../starter/results/traces_strategy_C.json).
  - Bảng chấm Coherence 10 vị trí: [manual_audit_coherence.json](../../starter/results/manual_audit_coherence.json).
  - Bảng chấm Grounding 5 câu Test: [manual_audit_grounding.json](../../starter/results/manual_audit_grounding.json).
  - Nhật ký thí nghiệm: [experiment_log.csv](../../artifacts/experiment_log.csv).

---

## 4. Phân tích và kết luận

### 4.1. So sánh chi tiết A–B và B–C

#### So sánh A vs B (Tác động của kỹ thuật Chunking):
- **Evidence Hit@3 tăng từ 73.3% lên 80.0% trên tập Dev:** Chiến lược B đã phục hồi thành công các câu hỏi khó như `q06` (các thuộc tính của SHAP ở Trang 8) và `q11` (công cụ TSViz ở Trang 18). Ở Chiến lược A, định nghĩa của TSViz bị cắt vụn qua 2 cửa sổ trượt khiến vector search trượt top-3. Ở Chiến lược B, đoạn văn hoàn chỉnh được giữ nguyên vẹn giúp vector embedding thể hiện chính xác ngữ nghĩa tổng thể.
- **Tính mạch lạc (Coherence) tăng từ 0.60 lên 1.60 / 2.0:** Đây là bước tiến lớn nhất. Các chunk của A thường xuyên bị cụt đầu hoặc cụt đuôi câu (ví dụ chunk `A_p05_c09` bắt đầu bằng `"...l techniques are challenging"`). Ngược lại, chunk của B luôn bắt đầu và kết thúc bằng câu trọn vẹn, người đọc và AI agent có thể hiểu độc lập mà không cần chắp vá.
- **Tiết kiệm tài nguyên:** Chiến lược B giảm từ 266 xuống 175 chunks (**giảm 34.2%** số lượng bản ghi), giúp giảm thời gian truy vấn từ 0.506s xuống 0.406s.

#### So sánh B vs C (Tác động của Metadata Filtering):
- **Độ tuân thủ bộ lọc tuyệt đối (100% Filter Compliance):** Trên câu test `q20`, Chiến lược C lọc cứng theo `category = 'applications_science'`, toàn bộ 3/3 chunks trả về đều nằm đúng trong phần Xe tự hành và Khoa học, loại bỏ 100% các chunk gây nhiễu từ các chương khác.
- **Đánh đổi (Trade-off):** Metadata Filtering mang lại độ chính xác phạm vi tuyệt đối khi câu hỏi có chủ đích rõ ràng. Tuy nhiên, nếu câu hỏi của người dùng mơ hồ, hoặc hệ thống gán nhãn metadata sai, nó sẽ triệt tiêu khả năng tìm thấy bằng chứng (Zero-recall risk).

### 4.2. Phân tích 2 ca lỗi thực tế (Failure Cases)

1. **Ca lỗi 1: Câu `q01` (Tập Dev, Trang 1 - Cả A, B, C đều miss Top-3):**
   - *Câu hỏi:* *"Why do artificial intelligence models encounter significant challenges in safety-critical domains such as healthcare and autonomous vehicles?"*
   - *Gold Evidence:* Câu mở đầu phần Abstract tại Trang 1: *"Artificial intelligence models encounter significant challenges due to their black-box nature, particularly in safety-critical domains..."*
   - *Thực tế trả về của Top-1:* Chunk `B_XAI_survey_2025_p01_c04` (Trang 1, Score 0.7614): *"The AI system does not usually provide any information about how it arrives at the decisions it makes. The systems and processes used in decision-making are complex..."*
   - *Nguyên nhân:* Cả Top-1 và Top-2 trả về đều nằm ở đúng Trang 1, nhưng mô hình embedding ưu tiên các đoạn văn ở phần thân (Introduction) có chứa nhiều từ ngữ mô tả chi tiết cơ chế ra quyết định hơn là câu tuyên bố ngắn gọn trong phần Abstract. Bằng chứng vẫn nằm ở trang 1 nhưng bị đẩy xuống Rank 4.

2. **Ca lỗi 2: Câu `q17` (Tập Test, Trang 25 - Cả A, B, C đều miss Top-3):**
   - *Câu hỏi:* *"How does high architectural complexity in deep neural networks impact the effectiveness of XAI techniques?"*
   - *Gold Evidence:* Section 7.1 Trang 25: *"XAI techniques are often less effective with highly complex models [48]. Developing AI models by reducing complexity without compromising much on accuracy is a challenging task."*
   - *Thực tế trả về của Top-1:* Chunk `B_XAI_survey_2025_p03_c04` (Trang 3, Score 0.7484): *"The black-box nature of AI models can be attributed to various factors, including model complexity, optimization algorithms, and high-dimensional parameter spaces..."*
   - *Nguyên nhân (Topic Scattering):* Chủ đề "Model Complexity" xuất hiện ở cả Chương 2 (Background, Trang 3) và Chương 7 (Future Directions, Trang 25). Do câu hỏi mang tính khái niệm chung, Embedding model đã ghép cặp câu hỏi với đoạn văn phân tích căn nguyên ở Trang 3 thay vì đoạn bàn về hạn chế ở Trang 25.

### 4.3. Chiến lược được lựa chọn & Điều kiện áp dụng
- **Chiến lược được chọn:** **Chiến lược B (kết hợp cơ chế lọc có điều kiện của C)**.
- **Lý do chọn:** 
  - Đạt điểm Evidence Hit@3 cao nhất (80.0% trên Dev).
  - Điểm Coherence vượt trội (1.60/2.0), đảm bảo chunk đưa vào LLM giữ trọn vẹn ngữ cảnh.
  - Số lượng chunk gọn nhẹ nhất (175 chunks), tiết kiệm 34.2% chi phí lưu trữ vector.
- **Điều kiện áp dụng:** Rất phù hợp cho tài liệu học thuật, tài liệu kỹ thuật, báo cáo thường niên có cấu trúc phân đoạn và tiêu đề phân minh. Kích hoạt bộ lọc Metadata (Chiến lược C) khi truy vấn đến từ giao diện người dùng có chọn sẵn chuyên mục, hoặc khi AI Agent phân loại được ý định (Intent Recognition) trước khi tìm kiếm.

### 4.4. Hạn chế của thực nghiệm
1. **Kích thước tập Test nhỏ (5 câu):** Do tập Test gồm 5 câu, mỗi câu chiếm tới 20% tỷ trọng nên độ nhạy thống kê cao; cần mở rộng lên 50–100 câu khi triển khai sản xuất thực tế.
2. **Hiện tượng phân tán chủ đề (Topic Scattering):** Trong bài báo khoa học 30 trang, một thuật ngữ (như *LIME, SHAP, Complexity*) xuất hiện lặp lại ở nhiều chương, khiến tìm kiếm vector thuần túy đôi khi bắt nhầm đoạn nhắc đến khái niệm thay vì đoạn giải thích cốt lõi.

### 4.5. Hướng cải tiến nếu làm tiếp
1. **Tìm kiếm lai (Hybrid Retrieval - BM25 + Dense Vector):** Kết hợp tìm kiếm từ khóa chính xác BM25 với vector embedding để giải quyết triệt để các câu hỏi chứa tên thuật ngữ độc nhất (như *PDC, TSViz, LRP*).
2. **Thêm bước Reranking (Cross-Encoder / Cohere Rerank):** Sử dụng một model Cross-Encoder để chấm điểm lại Top-10 chunks trước khi lấy Top-3, giúp phân biệt chính xác đoạn văn chứa câu trả lời trực tiếp so với đoạn chỉ nhắc thoáng qua.
3. **Phân đoạn ngữ nghĩa tự động (Semantic Chunking):** Thay vì chỉ ngắt theo `\n\n`, sử dụng khoảng cách cosine giữa các câu liên tiếp để tìm điểm chuyển ý tự nhiên của tác giả.

