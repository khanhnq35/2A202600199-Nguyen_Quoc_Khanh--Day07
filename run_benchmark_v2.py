"""Benchmark runner V2: LawClauseChunker (Khoản-level) vs LawRecursiveChunker (Điều-level).

Runs the same 6 benchmark queries with clause-level granularity to compare
against the original article-level chunking results.

Usage:
    python run_benchmark_v2.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.chunking import LawClauseChunker
from src.embeddings import GeminiEmbedder
from src.models import Document
from src.store import EmbeddingStore


# ── Metadata registry (same as v1) ──────────────────────────────────────
FILE_METADATA: dict[str, dict[str, Any]] = {
    "65_CNTT.md": {
        "doc_id": "65-2006-QH11",
        "source": "Quốc hội",
        "year": 2006,
        "category": "luat",
    },
    "71_CNCNS.md": {
        "doc_id": "71-2025-QH15",
        "source": "Quốc hội",
        "year": 2025,
        "category": "luat",
    },
    "91_BVDLCN.md": {
        "doc_id": "91-2025-QH15",
        "source": "Quốc hội",
        "year": 2025,
        "category": "luat",
    },
    "125_NDKH.md": {
        "doc_id": "125-2026-ND-CP",
        "source": "Chính phủ",
        "year": 2026,
        "category": "nghi-dinh",
    },
    "133_CNC.md": {
        "doc_id": "133-2025-QH15",
        "source": "Quốc hội",
        "year": 2025,
        "category": "luat",
    },
    "134_TTNT.md": {
        "doc_id": "134-2025-QH15",
        "source": "Quốc hội",
        "year": 2025,
        "category": "luat",
    },
}

# ── Same 6 benchmark queries ────────────────────────────────────────────
BENCHMARK_QUERIES: list[dict[str, Any]] = [
    {
        "id": 1,
        "query": (
            "Theo quy định của Luật Bảo vệ dữ liệu cá nhân, "
            "việc xử lý dữ liệu cá nhân của trẻ em từ đủ 07 tuổi trở lên "
            "nhằm công bố thông tin bí mật đời tư bắt buộc phải có điều kiện gì?"
        ),
        "gold_answer": (
            "Việc xử lý này phải có sự đồng ý của trẻ em đó và của "
            "người đại diện theo pháp luật (Căn cứ khoản 2 Điều 24)."
        ),
        "metadata_filter": {"year": 2025, "category": "luat"},
    },
    {
        "id": 2,
        "query": (
            "Tỷ lệ trích tối thiểu từ nguồn thu học phí của các cơ sở "
            "giáo dục đại học để phục vụ hoạt động khoa học, công nghệ và "
            "đổi mới sáng tạo được quy định như thế nào?"
        ),
        "gold_answer": (
            "Cơ sở giáo dục đại học thực hiện trích từ nguồn thu học phí "
            "với tỷ lệ tối thiểu 8% đối với đại học và 5% đối với cơ sở "
            "giáo dục đại học khác."
        ),
        "metadata_filter": None,
    },
    {
        "id": 3,
        "query": (
            "Công ty tôi đang có kế hoạch đầu tư một nhà máy sản xuất sản phẩm "
            "nằm trong Danh mục sản phẩm công nghệ chiến lược. "
            "Theo quy định mới nhất, dự án này sẽ được hưởng ưu đãi đặc biệt gì về đầu tư?"
        ),
        "gold_answer": (
            "Dự án được hưởng chính sách ưu đãi, hỗ trợ đầu tư đặc biệt theo "
            "quy định của pháp luật về đầu tư. Ngoài ra, còn được hưởng các mức "
            "ưu đãi, hỗ trợ cao nhất về thuế, đất đai và các chính sách khác."
        ),
        "metadata_filter": None,
    },
    {
        "id": 4,
        "query": (
            "Doanh nghiệp khởi nghiệp sáng tạo trong lĩnh vực trí tuệ nhân tạo "
            "được Nhà nước hỗ trợ những nội dung gì?"
        ),
        "gold_answer": (
            "Được hỗ trợ chi phí đánh giá sự phù hợp, hạ tầng tính toán "
            "(LLM, dữ liệu dùng chung), tư vấn kỹ thuật kiểm thử rủi ro, "
            "và ưu tiên hỗ trợ từ Quỹ phát triển trí tuệ nhân tạo quốc gia."
        ),
        "metadata_filter": {"category": "luat"},
    },
    {
        "id": 5,
        "query": (
            "Khi tiến hành hoạt động phát thanh và truyền hình trên môi trường mạng, "
            "các tổ chức, cá nhân bắt buộc phải tuân thủ những quy định của "
            "các loại pháp luật nào?"
        ),
        "gold_answer": (
            "Phải thực hiện quy định của: 1. Pháp luật về viễn thông; "
            "2. Pháp luật về báo chí; 3. Các quy định của Luật Công nghệ thông tin."
        ),
        "metadata_filter": None,
    },
    {
        "id": 6,
        "query": (
            "Theo Luật Công nghiệp công nghệ số, một công ty công nghệ nước ngoài "
            "cung cấp dịch vụ quản lý dữ liệu số phục vụ riêng cho hoạt động cơ yếu "
            "bảo vệ bí mật nhà nước tại Việt Nam thì có thuộc phạm vi điều chỉnh không?"
        ),
        "gold_answer": (
            "Công ty công nghệ nước ngoài cung cấp dịch vụ trên "
            "không thuộc phạm vi điều chỉnh đối với hoạt động cụ thể phục vụ cơ yếu đó."
        ),
        "metadata_filter": {"category": "luat"},
    },
]


def ingest_all_documents(
    store: EmbeddingStore,
    chunker: LawClauseChunker,
    docs_dir: Path,
) -> int:
    """Load, chunk, and embed all law files into the store.

    Args:
        store: The EmbeddingStore to ingest into.
        chunker: The LawClauseChunker instance.
        docs_dir: Path to the law documents directory.

    Returns:
        Total number of chunks ingested.
    """
    law_files = sorted(docs_dir.glob("*.md"))
    total_chunks = 0

    for f in law_files:
        content = f.read_text(encoding="utf-8")
        metadata = FILE_METADATA.get(f.name, {"doc_id": f.stem})
        metadata["file"] = f.name

        chunks = chunker.chunk(content)
        print(f"  📄 {f.name}: {len(chunks)} chunks  ({len(content):,} chars)")

        for i, c in enumerate(chunks):
            doc = Document(
                id=f"{f.stem}_v2_chunk_{i}",
                content=c if isinstance(c, str) else str(c),
                metadata=metadata.copy(),
            )
            # Rate-limit for Gemini free tier
            time.sleep(0.5)
            try:
                store.add_documents([doc])
            except Exception as e:
                print(f"    ⚠ Error on chunk {i}: {e}. Retrying after 15s...")
                time.sleep(15)
                store.add_documents([doc])

            total_chunks += 1
            if total_chunks % 50 == 0:
                print(f"    ... ingested {total_chunks} chunks so far")

    return total_chunks


def run_queries(store: EmbeddingStore) -> list[dict[str, Any]]:
    """Run all benchmark queries and collect results.

    Args:
        store: The populated EmbeddingStore to query against.

    Returns:
        List of result dicts with query info and top-3 retrievals.
    """
    all_results: list[dict[str, Any]] = []

    for bq in BENCHMARK_QUERIES:
        time.sleep(1)
        mf = bq.get("metadata_filter")

        if mf:
            results = store.search_with_filter(bq["query"], top_k=3, metadata_filter=mf)
        else:
            results = store.search(bq["query"], top_k=3)

        entry: dict[str, Any] = {
            "id": bq["id"],
            "query": bq["query"],
            "gold_answer": bq["gold_answer"],
            "filter": mf,
            "top_3": [],
        }

        print(f"\n{'='*80}")
        print(f"  QUERY #{bq['id']}: {bq['query'][:100]}...")
        if mf:
            print(f"  FILTER: {mf}")
        print(f"  GOLD: {bq['gold_answer'][:120]}...")
        print(f"{'─'*80}")

        for rank, r in enumerate(results, 1):
            content = r.get("content", "")
            score = r.get("score", 0.0)
            entry["top_3"].append({
                "rank": rank,
                "score": round(score, 4),
                "content_preview": content[:200],
                "metadata": r.get("metadata", {}),
            })
            print(f"  [{rank}] score={score:.4f}")
            print(f"      {content[:150].replace(chr(10), ' ')}...")

        all_results.append(entry)

    return all_results


def main() -> None:
    """Entry point: ingest docs → run queries → save results."""
    load_dotenv()

    print("🚀 Benchmark Runner V2 — LawClauseChunker (Khoản-level)")
    print("=" * 80)

    # ── 1. Initialize Gemini embedder ─────────────────────────────────────
    print("\n1️⃣  Initializing Gemini Embedder...")
    try:
        embedder = GeminiEmbedder()
        store = EmbeddingStore(embedding_fn=embedder)
        print(f"   Backend: {embedder._backend_name}")
    except Exception as e:
        print(f"   ❌ Failed to init Gemini: {e}")
        return

    # ── 2. Ingest documents with LawClauseChunker ────────────────────────
    chunker = LawClauseChunker(chunk_size=600)
    docs_dir = Path("data/law")
    print(f"\n2️⃣  Ingesting documents from {docs_dir}/ with LawClauseChunker (chunk_size=600)...")
    total = ingest_all_documents(store, chunker, docs_dir)
    print(f"\n   ✅ Total chunks in store: {total}")

    # ── 3. Run benchmark queries ──────────────────────────────────────────
    print(f"\n3️⃣  Running {len(BENCHMARK_QUERIES)} benchmark queries...")
    results = run_queries(store)

    # ── 4. Save results to JSON ───────────────────────────────────────────
    out_path = Path("report/benchmark_results_v2_clause.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(results, fp, ensure_ascii=False, indent=2)

    print(f"\n4️⃣  Results saved to {out_path}")
    print("=" * 80)
    print("✅  Benchmark V2 complete!")


if __name__ == "__main__":
    main()
