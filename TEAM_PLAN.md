# Kế Hoạch Làm Việc Nhóm — Lab 7: Embedding & Vector Store

**Dự án:** Ngày 7 — Nền Tảng Dữ Liệu: Embedding & Vector Store  
**Tổng điểm:** 100 (Cá nhân: 60 | Nhóm: 40)  
**Sản phẩm nộp:** `src/` hoàn chỉnh + `report/REPORT.md` (1 file/người)

---

## Tổng Quan 2 Phase

| Phase | Hình thức | Mục tiêu chính |
|-------|-----------|---------------|
| Phase 1 | Cá nhân | Implement toàn bộ `src/` và pass 42 tests |
| Phase 2 | Nhóm | Chọn tài liệu, thiết kế strategy, benchmark, so sánh |

---

## Phase 1 — Cá Nhân: Implement `src` Package

> Mỗi thành viên **tự làm độc lập**. Không copy code của nhau.

### Checklist implement (theo thứ tự)

- [ ] **`src/chunking.py`**
  - [ ] `SentenceChunker.chunk` — tách câu bằng regex (`. `, `! `, `? `, `.\n`), nhóm theo `max_sentences_per_chunk`
  - [ ] `RecursiveChunker.chunk` + `RecursiveChunker._split` — thử từng separator theo priority, đệ quy nếu chunk vẫn quá lớn
  - [ ] `compute_similarity` — công thức cosine: `dot(a,b) / (‖a‖ × ‖b‖)`, trả về `0.0` nếu vector rỗng
  - [ ] `ChunkingStrategyComparator.compare` — chạy 3 chunker, trả về dict với keys `fixed_size`, `by_sentences`, `recursive`; mỗi entry có `count`, `avg_length`, `chunks`

- [ ] **`src/store.py`** — class `EmbeddingStore`
  - [ ] `_make_record` — embed doc, tạo dict `{id, content, embedding, metadata}`
  - [ ] `_search_records` — dot product giữa query embedding và tất cả records, sort giảm dần, trả top-k
  - [ ] `add_documents` — embed + append vào `self._store`
  - [ ] `search` — embed query rồi gọi `_search_records`
  - [ ] `get_collection_size` — trả `len(self._store)`
  - [ ] `search_with_filter` — lọc theo metadata trước, rồi mới search
  - [ ] `delete_document` — xóa tất cả records có `metadata['doc_id'] == doc_id`, trả `bool`

- [ ] **`src/agent.py`** — class `KnowledgeBaseAgent`
  - [ ] `__init__` — lưu `self.store` và `self.llm_fn`
  - [ ] `answer` — retrieve top-k chunks → build prompt → gọi `llm_fn` → trả string

### Kiểm tra

```bash
pytest tests/ -v
# Mục tiêu: 42/42 PASSED
```

---

## Phase 2 — Nhóm: Strategy & Benchmark

### Bước 1 — Chọn Tài Liệu (cả nhóm thống nhất)

**Yêu cầu:** 5-10 tài liệu, cùng một domain rõ ràng, định dạng `.txt` hoặc `.md`, đặt vào `data/`.

**Gợi ý domain phù hợp với bộ tài liệu có sẵn (`law_word/`):**
- Luật pháp / văn bản quy phạm pháp luật (Luật 134-2025, Luật 71-2025, Nghị định 125-2026...)
- Nếu đổi domain: customer support FAQ, quy trình nội bộ, tài liệu kỹ thuật...

**Template thống nhất trong nhóm:**

| # | Tên tài liệu | Nguồn | Số ký tự ước tính | Metadata dự kiến |
|---|--------------|-------|-------------------|-----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Metadata schema nhóm thống nhất** (ví dụ cho domain luật):

| Trường | Kiểu | Ví dụ | Lý do cần |
|--------|------|-------|-----------|
| `doc_id` | str | `"luat-134-2025"` | Dùng để delete / filter |
| `source` | str | `"Quốc hội"` | Filter theo cơ quan ban hành |
| `year` | int | `2025` | Filter theo năm |
| `category` | str | `"luat"` / `"nghi-dinh"` | Filter theo loại văn bản |

---

### Bước 2 — Thống Nhất 5 Benchmark Queries (cả nhóm)

Mỗi query phải có **gold answer** (câu trả lời đúng đã biết trước) để chấm điểm retrieval.

| # | Query | Gold Answer | Ghi chú |
|---|-------|-------------|---------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

> **Tiêu chí query tốt:** câu hỏi cụ thể, có thể kiểm chứng được từ tài liệu, không quá rộng.

---

### Bước 3 — Mỗi Thành Viên Thiết Kế Strategy Riêng

Mỗi người **tự chọn và giải thích** strategy của mình trước khi chạy benchmark:

| Thành viên | Chunker chọn | Tham số | Metadata filter sẽ dùng | Lý do chọn |
|-----------|--------------|---------|--------------------------|-----------|
| [Tên 1] | | | | |
| [Tên 2] | | | | |
| [Tên 3] | | | | |
| [Tên 4] | | | | |

**Gợi ý strategy theo domain:**
- Văn bản pháp luật → `SentenceChunker` (câu văn pháp lý hoàn chỉnh) hoặc `RecursiveChunker` với `\n\n` separator (theo điều khoản)
- FAQ / tài liệu ngắn → `FixedSizeChunker` chunk nhỏ (200-300 ký tự)
- Tài liệu có cấu trúc rõ → `RecursiveChunker` với separator `\n\n` → `\n` → `. `

---

### Bước 4 — Chạy Benchmark Cá Nhân

Mỗi người chạy 5 queries trên strategy của mình và ghi lại kết quả:

```python
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.models import Document
from src.embeddings import get_embedder

# Khởi tạo store với embedder đã chọn
embedder = get_embedder("openai")   # hoặc "local" / "mock"
store = EmbeddingStore(embedding_fn=embedder)

# Load và chunk tài liệu, add vào store
# ...

# Chạy từng query
query = "..."
results = store.search(query, top_k=3)
for r in results:
    print(f"Score: {r['score']:.3f} | {r['content'][:100]}")
```

**Bảng kết quả cá nhân (điền vào REPORT.md):**

| # | Query | Top-1 Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|----------------------|-------|-----------|------------------------|
| 1 | | | | ✓ / ✗ | |
| 2 | | | | ✓ / ✗ | |
| 3 | | | | ✓ / ✗ | |
| 4 | | | | ✓ / ✗ | |
| 5 | | | | ✓ / ✗ | |

---

### Bước 5 — So Sánh Kết Quả Trong Nhóm

Sau khi mỗi người chạy xong, nhóm ngồi lại so sánh:

| Thành viên | Strategy | Queries đúng top-3 | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|-------------------|----------------------|-----------|----------|
| [Tên 1] | | / 5 | | | |
| [Tên 2] | | / 5 | | | |
| [Tên 3] | | / 5 | | | |
| [Tên 4] | | / 5 | | | |

**Câu hỏi thảo luận nhóm:**
1. Strategy nào cho precision cao nhất? Tại sao?
2. Query nào khó nhất cho tất cả mọi người? Tại sao?
3. Metadata filter có giúp ích không? Khi nào?
4. Nếu làm lại, data strategy sẽ thay đổi gì?

---

### Bước 6 — Chuẩn Bị Demo (5 điểm)

Demo ngắn (~5 phút/nhóm), bao gồm:

1. **Domain & tài liệu** — nhóm chọn gì, tại sao
2. **Các strategy đã thử** — mỗi người dùng gì, tham số thế nào
3. **Kết quả so sánh** — bảng so sánh trực quan
4. **Bài học rút ra** — strategy nào tốt cho domain này, khi nào retrieval thất bại
5. **Q&A** với các nhóm khác

---

## Tiêu Chí Tự Đánh Giá Retrieval

Sau mỗi query, đánh giá theo 5 góc nhìn:

| Góc nhìn | Câu hỏi kiểm tra |
|----------|-----------------|
| **Retrieval Precision** | Top-3 có chunk thật sự liên quan không? Score có phân biệt được tốt/xấu? |
| **Chunk Coherence** | Chunk có giữ ý trọn vẹn không, hay bị cắt giữa câu? |
| **Metadata Utility** | `search_with_filter()` có tăng precision không? Filter có quá chặt không? |
| **Grounding Quality** | Agent answer có thực sự dựa trên context hay "bịa"? |
| **Domain Fit** | Chunking strategy có phù hợp với loại tài liệu không? |

---

## Phân Công & Timeline Gợi Ý

| Thời gian | Hoạt động | Ai làm |
|-----------|-----------|--------|
| Đầu buổi (45 phút) | Phase 1: Implement `src/` | Mỗi người tự làm |
| Giữa buổi (15 phút) | Thống nhất domain, tài liệu, 5 queries | Cả nhóm |
| Giữa buổi (30 phút) | Mỗi người thiết kế + chạy strategy riêng | Mỗi người tự làm |
| Cuối buổi (15 phút) | So sánh kết quả, chuẩn bị demo | Cả nhóm |
| Demo | Trình bày (~5 phút) | Cả nhóm |

---

## Checklist Nộp Bài

- [ ] `src/chunking.py` — tất cả TODO đã implement
- [ ] `src/store.py` — tất cả TODO đã implement
- [ ] `src/agent.py` — tất cả TODO đã implement
- [ ] `pytest tests/ -v` — 42/42 PASSED
- [ ] `report/REPORT.md` — đã điền đầy đủ (cá nhân + nhóm)
  - [ ] Mục 1: Warm-up (cosine similarity + chunking math)
  - [ ] Mục 2: Document selection (nhóm)
  - [ ] Mục 3: Chunking strategy (cá nhân + so sánh nhóm)
  - [ ] Mục 4: My approach (giải thích từng phần implement)
  - [ ] Mục 5: Similarity predictions (5 cặp câu)
  - [ ] Mục 6: Results (5 benchmark queries)
  - [ ] Mục 7: What I learned
  - [ ] Tự đánh giá điểm

---

## Điểm Số Tham Khảo

| Hạng mục | Điểm | Ghi chú |
|----------|------|---------|
| Core implementation (42 tests pass) | 30 | Cá nhân |
| My approach (giải thích implement) | 10 | Cá nhân |
| Competition results (5 queries) | 10 | Cá nhân, cùng queries với nhóm |
| Warm-up | 5 | Cá nhân |
| Similarity predictions | 5 | Cá nhân |
| Strategy design + so sánh | 15 | Nhóm |
| Document set quality | 10 | Nhóm |
| Retrieval quality (5 queries × 2đ) | 10 | Nhóm |
| Demo | 5 | Nhóm |
| **Tổng** | **100** | |

> **Lưu ý quan trọng:** Strategy design (15đ) > Retrieval quality (10đ). Giải thích được *tại sao* strategy hoạt động quan trọng hơn điểm số thuần tuý.
