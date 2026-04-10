# Báo Cáo Lab 7: Embedding & Vector Store
 
**Họ tên:** Nguyễn Quốc Khánh
**Nhóm:** C401_D6
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Khi hai chunk văn bản có độ tương đồng cosine cao, nghĩa là góc giữa hai vector biễu diễn chúng rất nhỏ, thể hiện rằng cấu trúc và ý nghĩa ngữ nghĩa (semantic meaning) của chúng rất giống nhau.

**Ví dụ HIGH similarity:**
- Câu A: "Hôm nay tôi đi tập gym để rèn luyện sức khỏe."

- Câu B: "Tôi đến phòng tập thể hình vào sáng nay để nâng cao thể lực."

- Giải thích: Hai câu này dùng từ ngữ khác nhau nhưng cùng mô tả một hành động và mục đích trong cùng một ngữ cảnh.

**Ví dụ LOW similarity:**
- Câu A: "Lập trình Python rất thú vị cho việc xử lý dữ liệu."

- Câu B: "Thời tiết hôm nay ở Hà Nội khá oi bức và có thể có mưa."

- Giải thích: Hai câu này thuộc hai chủ đề hoàn toàn khác nhau (Công nghệ thông tin vs. Thời tiết), các vector của chúng sẽ chỉ về hai hướng cách xa nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

Trong xử lý ngôn ngữ tự nhiên, Cosine Similarity được ưu tiên hơn vì nó không bị ảnh hưởng bởi độ dài văn bản (Magnitude invariance).

Vấn đề của Euclidean Distance: Khoảng cách này đo độ dài đường thẳng giữa hai đầu mút vector. Nếu có hai đoạn văn bản cùng chủ đề nhưng một đoạn dài (nhiều từ) và một đoạn ngắn (ít từ), đầu mút của đoạn dài sẽ nằm rất xa gốc tọa độ. Khi đó, Euclidean Distance sẽ rất lớn, khiến máy tính hiểu lầm là chúng không liên quan đến nhau.

Ưu điểm của Cosine Similarity: Nó chỉ đo góc giữa hai vector. Dù một bài báo dài 1000 chữ và một câu tóm tắt 10 chữ nói về cùng một chủ đề, góc giữa chúng vẫn sẽ rất nhỏ. Điều này giúp hệ thống nhận diện đúng sự tương đồng về nội dung mà không bị đánh lừa bởi số lượng từ ngữ.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Phép tính sẽ là `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25`, số lượng chunk sẽ tăng lên. Việc tăng overlap giúp tránh tình trạng cắt ngang một câu hoặc một cụm từ mang ý nghĩa quan trọng, giúp duy trì ngữ cảnh (context) liền mạch giữa các chunk kề nhau, nhờ đó hệ thống RAG ít bỏ sót thông tin tại điểm bị cắt.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Vietnamese ICT & AI Legal Documents

**Tại sao nhóm chọn domain này?**
> Nhóm chọn domain "Luật Công nghệ thông tin và Chuyển đổi số Việt Nam" vì đây là nền tảng pháp lý cực kỳ quan trọng đối với các kỹ sư và chuyên gia AI. Việc hiểu rõ các quy định về Trí tuệ nhân tạo, Bảo vệ dữ liệu cá nhân và Công nghệ cao giúp chúng ta phát triển các hệ thống vừa tối ưu về kỹ thuật, vừa đảm bảo tính tuân thủ pháp luật.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | 65_CNTT.md | thuvienphapluat.vn | ~89,000 | doc_id: 65-2006-QH11, source: Quốc hội, year: 2006, category: luat |
| 2 | 71_CNCNS.md | thuvienphapluat.vn | ~83,000 | doc_id: 71-2025-QH15, source: Quốc hội, year: 2025, category: luat |
| 3 | 91_BVDLCN.md | thuvienphapluat.vn | ~71,000 | doc_id: 91-2025-QH15, source: Quốc hội, year: 2025, category: luat |
| 4 | 125_NDKH.md | thuvienphapluat.vn | ~93,000 | doc_id: 125-2026-ND-CP, source: Chính phủ, year: 2026, category: nghi-dinh |
| 5 | 133_CNC.md | thuvienphapluat.vn | ~88,000 | doc_id: 133-2025-QH15, source: Quốc hội, year: 2025, category: luat |
| 6 | 134_TTNT.md | thuvienphapluat.vn | ~65,000 | doc_id: 134-2025-QH15, source: Quốc hội, year: 2025, category: luat |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | "luat-134-2025" | Định danh duy nhất để xóa hoặc cập nhật chính xác tài liệu trong cơ sở dữ liệu. |
| `source` | string | "Quốc hội" | Cho phép lọc tài liệu theo cơ quan ban hành (nguồn luật). |
| `year` | integer | 2025 | Hỗ trợ lọc theo mốc thời gian hoặc tìm văn bản mới nhất. |
| `category` | string | "luat", "nghi-dinh" | Giúp người dùng giới hạn phạm vi tìm kiếm theo phân tầng văn bản pháp quy. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu (với `chunk_size=1000`):

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| 134_TTNT.md | FixedSizeChunker (`fixed_size`) | 52 | 992.3 | Kém (Vì cắt tuỳ ý ở chữ bất kỳ) |
| 134_TTNT.md | SentenceChunker (`by_sentences`) | 121 | 404.3 | Yếu (Các điều luật dài bị gãy đôi) |
| 134_TTNT.md | RecursiveChunker (`recursive`) | 67 | 730.8 | Khá tốt (Giữ được đoạn văn nguyên vẹn) |
| 71_CNCNS.md | FixedSizeChunker (`fixed_size`) | 66 | 992.0 | Kém |
| 71_CNCNS.md | SentenceChunker (`by_sentences`) | 140 | 443.4 | Yếu |
| 71_CNCNS.md | RecursiveChunker (`recursive`) | 91 | 682.4 | Khá tốt |

### Strategy Của Tôi

**Loại:** Custom RecursiveChunker (Tối ưu cho văn bản pháp luật)

**Mô tả cách hoạt động:**
> *Strategy này kế thừa `RecursiveChunker` nhưng tuỳ biến lại trọng số danh sách ngăn cách (separators). Nó ưu tiên cắt dựa theo thẻ Heading riêng của văn bản pháp luật trước như `\n## Điều ` hoặc `\n### Khoản `, sau đó mới fallback xuống cắt đoạn `\n\n` hoặc câu `.` khi các điều khoản quá dài. Điều này giúp các nội dung chung một "Điều" được gom vào chung một Chunk, giảm thiểu việc mất ngữ cảnh.*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Văn bản Luật Việt Nam có cấu trúc rất đặc thù và phân cấp rõ ràng theo Điều, Khoản, Điểm. Nếu cắt ngẫu nhiên, các "Khoản" sẽ dễ bị tách rời khỏi "Điều", tạo context đứt gãy khiến RAG không hiểu đây là quy định của khoản mục nào. Strategy chuyên biệt này khai thác tối đa cấu trúc markdown đã gán tự động của văn bản để sinh chunks hội tụ cụm ý nghĩa một cách hoàn chỉnh.*

**Code snippet (nếu custom):**
```python
from src.chunking import RecursiveChunker

class LawRecursiveChunker(RecursiveChunker):
    """
    Custom strategy tailored for Vietnamese legal documents formatted in Markdown.
    Prioritizes splitting by Markdown headers matching "Điều" and "Khoản".
    """
    def __init__(self, chunk_size=1000):
        # Ưu tiên các thẻ markdown của Điều và Khoản trước, sau đó mới dùng default
        separators = ["\n## Điều ", "\n### Khoản ", "\n\n", "\n", ". ", " "]
        super().__init__(separators=separators, chunk_size=chunk_size)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| 134_TTNT.md | best baseline (`recursive`) | 67 | 730.8 | Tốt nhưng đôi khi tự cắt ngang giữa "Khoản" |
| 134_TTNT.md | **của tôi** | 68 | 720.5 | Cực tốt (Context bắt nguyên "Điều" hoặc "Khoản") |
| 71_CNCNS.md | best baseline (`recursive`) | 91 | 682.4 | Tốt |
| 71_CNCNS.md | **của tôi** | 93 | 660.1 | Rất ổn định, dễ truy xuất thông tin logic |

### So Sánh Với Thành Viên Khác
Nhóm C401_D6

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| **Quốc Khánh** | `LawRecursiveChunker(1000)` + Gemini | **8.3 / 10** | Bảo toàn cấu trúc luật (Điều/Khoản), hiểu ngữ nghĩa tiếng Việt cực tốt. | Chunk cấp Điều (1000 chars) đôi khi vẫn còn hơi rộng, gây "pha loãng" ý chính. |
| **Quế Sơn** | `SentenceChunker(6)` + OpenAI Large | **7.5 / 10** | Dùng model mạnh nhất thế giới, giữ mạch văn tự nhiên theo câu. | Không có cấu trúc logic của văn bản luật, dễ gộp nhầm các quy định khác nhau. |
| **Tuấn Khải** | `FixedSize(600/150)` + Gemini | **6.5 / 10** | Chồng lấp (overlap) giúp không mất thông tin ở biên các chunk. | Cắt ngang xương câu hoặc điều luật một cách cơ học, làm hỏng tính toàn vẹn. |
| **Văn Tấn** | `FixedSize(500/100)` + Local Model | **5.0 / 10** | Tốc độ xử lý nhanh, hoàn toàn in-memory và không tốn phí API. | Model local nhỏ (MiniLM) và chunk fixed-size khiến khả năng retrieval kém nhất nhóm. |
| **Công Thành** | `Recursive(1000)` + Local Model | **7.0 / 10** | Linh hoạt hơn fixed-size nhờ khả năng tách đệ quy theo đoạn văn. | Model local chưa hiểu sâu các thuật ngữ pháp lý chuyên ngành phức tạp. |
| **Hồng Nhật** | `Sentence(2)` + OpenAI Small | **8.5 / 10** | Cực kỳ tinh gọn, giúp trả về kết quả rất sát với từ khóa và ý chính. | Thiếu ngữ cảnh bao quát, đôi khi Agent không đủ thông tin để giải thích đầy đủ. |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Chiến lược mang lại hiệu quả cao nhất (Retrieval Score tốt nhất) là **`Sentence(2)`** kết hợp với **OpenAI Small**. Việc chia nhỏ đến mức tối thiều (2 câu) giúp giảm thiểu hoàn toàn hiện tượng "pha loãng" ngữ nghĩa, cho phép Vector Search tìm thấy chính xác vị trí chứa quy định pháp lý mà không bị nhiễu bởi các đoạn văn xung quanh.*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Sử dụng regex `(?<=[.!?])\s+|(?<=\.)\n` để tách các câu dựa trên các dấu câu kết thúc như `.` `!` `?` hoặc xuống dòng sau dấu chấm. Sau khi tách, tôi duyệt qua từng câu, loại bỏ các khoảng trắng thừa và gom chúng thành một chuỗi (chunk) dài bằng với tham số giới hạn `max_sentences_per_chunk`.*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Sử dụng một hàm đệ quy `_split`: lấy separator đứng đầu tiên để chia tách nội dung. Nếu một phần văn bản chia ra bị lớn hơn `chunk_size`, thuật toán sẽ tự gọi đệ quy với danh sách các separators còn lại. Khi hết ds separator (Base case), thuật toán fallback dùng `FixedSizeChunker` để chia nhỏ chính xác.*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Tôi sử dụng một list in-memory `self._store` chứa các dict lưu cấu trúc đầy đủ của từng chunk (`id`, `content`, `metadata`, `embedding`). Tính năng `search` đơn giản là map câu query ra `query_emb`, gọi list tính dot product (dựa vào `_dot` và magnitude) với toàn bộ memory, sort điểm giảm dần và lấy ra `top_k` chunk lớn nhất.*

**`search_with_filter` + `delete_document`** — approach:
> *Trong hàm tìm kiếm `search_with_filter`, tôi kiểm tra dict các trường metadata để "lọc (filter) trước", sau đó list rút gọn này mới được đút vào hàm tính điểm similarity để tiết kiệm tài nguyên. `delete_document` sử dụng duyệt list comprehension để loại bỏ toàn bộ những record có `id` hoặc metadata sinh ra từ `doc_id` tương ứng được cung cấp.*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Agent nhận string câu hỏi, đi tìm các top chunks bằng `store.search()`. Sau đó, văn bản trong các chunks này sẽ được format thẳng hàng đính kèm số thứ tự (ví dụ: `[Chunk 1]: ...`) để gộp chung thành một mảng context injection. Kết thúc, text context nằm trong template `Context:\n...\n\nQuestion: ...\nAnswer:` và trigger llm callback đưa ra đáp án.*

### Test Results

```
=========================================== test session starts ============================================
platform darwin -- Python 3.12.11, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/khanhnq35/Documents/AI_Vin/assignments/2A202600199-Nguyen_Quoc_Khanh--Day07
collected 42 items

tests/test_solution.py ..........................................                                    [100%]

============================================ 42 passed in 0.04s ============================================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khoản 2 Điều 24 quy định về xử lý dữ liệu trẻ em từ đủ 7 tuổi. | Trẻ em từ 7 tuổi trở lên khi xử lý dữ liệu cần có sự đồng ý của bản thân và người đại diện. | High | `-0.1442` | Sai hoàn toàn |
| 2 | Doanh nghiệp khởi nghiệp AI được hỗ trợ từ Quỹ phát triển trí tuệ nhân tạo quốc gia. | Các công ty startup trong lĩnh vực trí tuệ nhân tạo nhận ưu đãi từ quỹ quốc gia. | High | `-0.0688` | Sai hoàn toàn |
| 3 | Mùa thu ở Hà Nội rất đẹp và lãng mạn. | Hệ thống RAG giúp cải thiện chất lượng truy xuất dữ liệu pháp luật. | Low | `0.2178` | Sai (Cao nhất bảng) |
| 4 | Pháp luật về viễn thông và báo chí là bắt buộc tuân thủ. | Các tổ chức phải thực hiện quy định về báo chí, viễn thông. | High | `0.0416` | Sai |
| 5 | Bảo vệ dữ liệu cá nhân là trách nhiệm của tổ chức. | Cơ quan, tổ chức có nghĩa vụ bảo mật thông tin cá nhân. | High | `0.0134` | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Điều bất ngờ nhất là **100% dự đoán của một con người đều "sai bét"**. Cặp Pair 3 (hoàn toàn không liên quan về nghĩa) lại cho điểm số cao nhất `0.2178`, trong khi các câu paraphrase có nghĩa giống hệt nhau (Pair 1, 2) lại có Cosine Similarity âm.*
> *Điều này xảy ra là do code `_mock_embed` trong lab thực chất đang khởi tạo vector bằng cách băm chuỗi qua `hashlib.md5()` và lấy pseudo-Random. Nó chứng tỏ một bài học quan trọng: Nếu hàm embedding biểu diễn sai, thì thuật toán toán học (Cosine Similarity) có chạy đúng đến đâu cũng trả về kết quả hoàn toàn vô nghĩa và RAG sẽ sụp đổ.*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5-6 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Theo quy định của Luật Bảo vệ dữ liệu cá nhân, việc xử lý dữ liệu cá nhân của trẻ em từ đủ 07 tuổi trở lên nhằm công bố thông tin bí mật đời tư bắt buộc phải có điều kiện gì, căn cứ khoản nào, điều nào? | Việc xử lý này phải có sự đồng ý của trẻ em đó và của người đại diện theo pháp luật (Căn cứ khoản 2 Điều 24). |
| 2 | Tỷ lệ trích tối thiểu từ nguồn thu học phí của các cơ sở giáo dục đại học để phục vụ hoạt động khoa học, công nghệ và đổi mới sáng tạo được quy định như thế nào? | Cơ sở giáo dục đại học thực hiện trích từ nguồn thu học phí với tỷ lệ tối thiểu 8% đối với đại học và 5% đối với cơ sở giáo dục đại học khác. |
| 3 | Công ty tôi đang có kế hoạch đầu tư một nhà máy sản xuất sản phẩm nằm trong Danh mục sản phẩm công nghệ chiến lược. Theo quy định mới nhất, dự án này của chúng tôi sẽ được hưởng ưu đãi đặc biệt gì về đầu tư? | Dự án được hưởng chính sách ưu đãi, hỗ trợ đầu tư đặc biệt theo quy định của pháp luật về đầu tư. Ngoài ra, còn được hưởng các mức ưu đãi, hỗ trợ cao nhất về thuế, đất đai và các chính sách khác có liên quan. |
| 4 | Doanh nghiệp khởi nghiệp sáng tạo trong lĩnh vực trí tuệ nhân tạo được Nhà nước hỗ trợ những nội dung gì? | Được hỗ trợ chi phí đánh giá sự phù hợp, hạ tầng tính toán (LLM, dữ liệu dùng chung), tư vấn kỹ thuật kiểm thử rủi ro, và ưu tiên hỗ trợ từ Quỹ phát triển trí tuệ nhân tạo quốc gia cùng nhiều chính sách hợp tác với viện/trường mở rộng. |
| 5 | Khi tiến hành hoạt động phát thanh và truyền hình trên môi trường mạng, các tổ chức, cá nhân bắt buộc phải tuân thủ những quy định của các loại pháp luật nào? | Phải thực hiện tuân thủ: 1. Pháp luật về viễn thông; 2. Pháp luật về báo chí; 3. Tổ chức và cá nhân phải tuân thủ các quy định của Luật Công nghệ thông tin. |
| 6 | Theo Luật Công nghiệp công nghệ số, một công ty công nghệ nước ngoài cung cấp dịch vụ quản lý dữ liệu số phục vụ riêng cho hoạt động cơ yếu bảo vệ bí mật nhà nước tại Việt Nam thì có thuộc phạm vi điều chỉnh không? | Công ty công nghệ nước ngoài cung cấp dịch vụ trên không thuộc phạm vi điều chỉnh của đối với hoạt động cụ thể phục vụ cơ yếu đó.|

### Kết Quả Của Tôi

> **Embedder:** `gemini-embedding-001` (Google Gemini API) — 3072 chiều
> **Chunker:** `LawRecursiveChunker` (custom, chunk_size=1000)
> **Tổng chunks ingested:** ~490 chunks từ 6 văn bản luật

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Nhận xét |
|---|-------|--------------------------------|-------|-----------|----------|
| 1 | Theo quy định Luật BV DLCN, xử lý DLCN trẻ em từ đủ 07 tuổi... (Filter: `year=2025, category=luat`) | **Điều 24. Bảo vệ dữ liệu cá nhân của trẻ em**, người bị mất hoặc hạn chế NLHV dân sự... (từ `91_BVDLCN.md`) | **0.8811** | ✓ Có | Top-1 trả về đúng Điều 24, chứa quy định về sự đồng ý của trẻ em + người đại diện |
| 2 | Tỷ lệ trích tối thiểu từ nguồn thu học phí của các CSGDĐH... (Không filter) | **Cơ sở giáo dục đại học trích từ nguồn thu học phí, với tỷ lệ tối thiểu 8% đối với đại học và 5%**... (từ `125_NDKH.md`) | **0.9187** | ✓ Có | Score **cao nhất** trong 6 queries, top-1 chứa chính xác nội dung gold answer |
| 3 | Đầu tư nhà máy sx sản phẩm công nghệ chiến lược, ưu đãi đặc biệt gì? (Không filter) | **Dự án đầu tư sản xuất sản phẩm công nghệ chiến lược** thuộc Danh mục... được hưởng chính sách ưu đãi, hỗ trợ đầu tư đặc biệt... (từ `133_CNC.md`) | **0.8788** | ✓ Có | Chunk top-1 trùng khớp gần tuyệt đối với gold answer |
| 4 | DN khởi nghiệp sáng tạo lĩnh vực TTNT được Nhà nước hỗ trợ gì? (Filter: `category=luat`) | **Doanh nghiệp có năng lực R&D và đổi mới sáng tạo trong lĩnh vực trí tuệ nhân tạo** được ưu tiên tham gia nhiệm vụ... (từ `134_TTNT.md`) | **0.8785** | ✓ Một phần | Top-1 đúng chủ đề (DN + TTNT) nhưng chỉ đề cập ưu tiên tham gia chương trình KH-CN, chưa đầy đủ như gold answer |
| 5 | Phát thanh và truyền hình trên mạng, phải tuân thủ pháp luật nào? (Không filter) | Tổ chức, cá nhân tiến hành hoạt động **văn hóa, báo chí trên môi trường mạng** phải tuân thủ quy định của Luật này và PL về báo chí... (từ `65_CNTT.md`) | **0.8274** | △ Một phần | Chunk đề cập "báo chí trên môi trường mạng" nhưng nói về hoạt động **văn hóa**, không phải **phát thanh truyền hình**. Thiếu mention "pháp luật về viễn thông" |
| 6 | Công ty nước ngoài cung cấp dịch vụ quản lý dữ liệu số phục vụ cơ yếu, có thuộc phạm vi ĐC? (Filter: `category=luat`) | **Điều 1. Phạm vi điều chỉnh** — Luật này quy định về phát triển công nghiệp công nghệ số, công nghiệp bán dẫn, TTNT... (từ `71_CNCNS.md`) | **0.8454** | ✓ Có | Chunk top-1 đúng Điều 1 của Luật CNCNS, chứa nội dung loại trừ hoạt động cơ yếu |

**Bao nhiêu queries trả về chunk relevant trong top-3?** **5 / 6** (Query 5 chỉ relevant một phần)

### Phân Tích Tổng Quan Kết Quả

| Metric | Giá trị |
|--------|---------|
| Avg Top-1 Score | **0.8717** |
| Min Top-1 Score | 0.8274 (Query 5) |
| Max Top-1 Score | 0.9187 (Query 2) |
| Top-1 Relevant Rate | 4/6 hoàn toàn đúng, 1/6 một phần, 1/6 lệch |
| Top-3 Relevant Rate | 5/6 có ít nhất 1 chunk relevant |

**Nhận xét chung:** Việc chuyển từ `MockEmbedder` (0/6 queries đúng) sang `GeminiEmbedder` (5/6 queries đúng) đã cải thiện retrieval quality **tăng từ 0% lên 83%**. Điều này chứng minh rằng chất lượng embedding model là yếu tố **quyết định** nhất trong pipeline RAG, quan trọng hơn cả chiến lược chunking.

---

## 7. Failure Analysis (Exercise 3.5)

### Failure Case 1: Query 5 — Retrieval Lệch Ngữ Cảnh

**Query:** *"Khi tiến hành hoạt động phát thanh và truyền hình trên môi trường mạng, các tổ chức, cá nhân bắt buộc phải tuân thủ những quy định của các loại pháp luật nào?"*

**Expected:** Chunk chứa Khoản 3, Điều 13 của Luật CNTT (65/2006/QH11), đề cập rõ ràng 3 loại pháp luật: viễn thông, báo chí, và Luật CNTT.

**Actual Retrieved (Top-1):** *"Tổ chức, cá nhân tiến hành hoạt động **văn hóa, báo chí** trên môi trường mạng phải tuân thủ quy định của Luật này và các quy định của pháp luật về báo chí, văn hóa - thông tin."* (Score: `0.8274`)

**Top-2:** *"...thu thập, xử lý và sử dụng thông tin cá nhân..."* (Score: `0.8133`) — Không liên quan.

**Top-3:** *"...Xâm phạm quyền sở hữu trí tuệ trong hoạt động CNTT..."* (Score: `0.8067`) — Không liên quan.

### Phân Tích Nguyên Nhân

1. **Chunk Coherence (Vấn đề chính):** Khoản 3 Điều 13 nói riêng về "phát thanh, truyền hình" bị gộp chung trong một chunk lớn hơn xoay quanh Điều 13 "Ứng dụng CNTT trên mạng". Khi chunk bao gồm quá nhiều khoản (1, 2, 3...), embedding vector bị "pha loãng" (diluted) bởi nội dung đa chủ đề, khiến xếp hạng semantic bị sai lệch.

2. **Semantic Overlap:** Các cụm từ "báo chí trên môi trường mạng" (Top-1, Khoản 2) và "phát thanh truyền hình trên môi trường mạng" (Khoản 3 — chunk đúng) rất gần nhau về mặt ngữ nghĩa. Embedding model không đủ phân biệt hai khái niệm pháp lý khác nhau này.

3. **Thiếu Metadata Granular:** Metadata hiện tại chỉ có `doc_id`, `year`, `category` — ở cấp tài liệu. Nếu có thêm metadata ở cấp **Điều** (ví dụ: `article: "Điều 13"`, `topic: "phát thanh truyền hình"`), filter sẽ giúp thu hẹp phạm vi tìm kiếm hiệu quả hơn.

### Đề Xuất Cải Thiện

1. **Giảm Chunk Size / Tăng Granularity:** Thay vì chunk theo "Điều" (có thể rất dài), thử chunk theo "Khoản" để mỗi chunk chỉ chứa **chính xác 1 quy định**. Điều này giảm dilution effect nhưng tăng số lượng chunks.

2. **Hybrid Search (BM25 + Vector):** Tích hợp BM25 exact-match song song cùng vector search. Từ khóa "phát thanh truyền hình" sẽ được BM25 bắt trực tiếp, giải quyết trường hợp semantic embedding bị "mờ" giữa các khoản gần nghĩa.

3. **Metadata Enrichment:** Bổ sung metadata chi tiết hơn ở cấp chunk:
   - `article`: Số điều (VD: "Điều 13")
   - `topic`: Chủ đề chính của chunk (VD: "phát thanh truyền hình trên mạng")
   - `chapter`: Chương chứa điều luật

4. **Query Expansion:** Mở rộng câu query trước khi embed bằng cách thêm các từ khóa pháp lý liên quan (VD: "phát thanh truyền hình" → "phát thanh, truyền hình, viễn thông, báo chí") để kéo đúng chunk lên top.

### So Sánh Mock vs Gemini: Bài Học Rút Ra

| Tiêu chí | MockEmbedder | GeminiEmbedder |
|----------|-------------|----------------|
| Score range | 0.01 – 0.44 (random) | 0.80 – 0.92 (có ngữ nghĩa) |
| Top-1 Relevant | 0/6 (0%) | 4/6 hoàn toàn + 1/6 một phần (83%) |
| Failure mode | Hoàn toàn ngẫu nhiên | Chỉ lỗi khi semantic gần nhau |
| Bài học | Hash ≠ Embedding | Chất lượng model quyết định toàn bộ RAG pipeline |

> **Kết luận quan trọng:** Trong pipeline RAG, yếu tố ảnh hưởng lớn nhất đến retrieval quality theo thứ tự là: **(1) Embedding Model > (2) Chunking Strategy > (3) Metadata Filtering**. Một embedding model tốt (Gemini) có thể "cứu" chunking chưa tối ưu, nhưng chunking tốt không thể bù đắp cho embedding kém (Mock).

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| Retrieval Quality | Nhóm | 8 / 10 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 3 / 5 |
| **Tổng** | | **95 / 100** |
