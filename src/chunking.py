from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # TODO: split into sentences, group into chunks
        # DONE
        if not text:
            return []
        
        # Split on ". ", "! ", "? " or ".\n"
        sentences = re.split(r'(?<=[.!?])\s+|(?<=\.)\n', text)
        
        chunks: list[str] = []
        current_chunk_sentences: list[str] = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                current_chunk_sentences.append(sentence)
                if len(current_chunk_sentences) == self.max_sentences_per_chunk:
                    chunks.append(" ".join(current_chunk_sentences))
                    current_chunk_sentences = []
                    
        if current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))
            
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        # TODO: implement recursive splitting strategy
        # DONE
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # TODO: recursive helper used by RecursiveChunker.chunk
        # DONE
        if not remaining_separators:
            # Fallback when no separators are left
            return FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(current_text)
            
        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]
        
        # Split using the current separator
        parts = current_text.split(separator)
        
        chunks: list[str] = []
        current_chunk = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # If a single part is larger than chunk size, recurse on it
            if len(part) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Recursively split this large part
                chunks.extend(self._split(part, next_separators))
                continue
                
            # Check if adding this part would exceed chunk size
            expected_len = len(current_chunk) + len(separator) + len(part) if current_chunk else len(part)
            if expected_len > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                current_chunk = current_chunk + separator + part if current_chunk else part
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks


class LawRecursiveChunker(RecursiveChunker):
    """Custom strategy tailored for Vietnamese legal documents formatted in Markdown.

    Prioritizes splitting by Markdown headers matching "Điều" and "Khoản",
    then falls back to paragraph/sentence/word separators.

    Design rationale:
        Vietnamese legal texts follow a strict hierarchy (Điều → Khoản → Điểm).
        Cutting arbitrarily loses this structure, so using header-based separators
        ensures each chunk corresponds to a complete legal provision.
    """

    def __init__(self, chunk_size: int = 1000) -> None:
        separators = ["\n## Điều ", "\n### Khoản ", "\n\n", "\n", ". ", " "]
        super().__init__(separators=separators, chunk_size=chunk_size)


class LawClauseChunker:
    """Clause-level chunker for Vietnamese legal documents.

    Splits text into individual clauses (Khoản) within each article (Điều),
    prepending the parent article header to each clause chunk for context.

    This results in smaller, more focused chunks compared to LawRecursiveChunker,
    reducing the semantic "dilution" effect when multiple clauses cover
    different topics within the same article.

    Design rationale:
        Query 5 of the benchmark showed that article-level chunks can mix
        semantically distinct clauses (e.g., "văn hóa, báo chí" vs
        "phát thanh, truyền hình"), causing retrieval misses. Clause-level
        chunking ensures each chunk covers exactly one legal provision.
    """

    # Regex to detect article headers: "#### Điều X." or "## Điều X."
    _ARTICLE_RE = re.compile(r"(#{2,4}\s*Điều\s+\d+[^#\n]*)")
    # Regex to detect clause starts: "\n1. ", "\n2. ", etc.
    _CLAUSE_RE = re.compile(r"\n(?=\d+\.\s)")

    def __init__(self, chunk_size: int = 600, overlap: int = 0) -> None:
        """Initialize LawClauseChunker.

        Args:
            chunk_size: Maximum characters per chunk. Clauses exceeding this
                are further split by sentence boundaries.
            overlap: Not used (kept for API compatibility).
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        """Split legal text into clause-level chunks.

        Args:
            text: Full legal document text in Markdown format.

        Returns:
            List of chunk strings, each containing one clause with its
            parent article header prepended.
        """
        if not text:
            return []

        # Split by article headers while keeping the headers
        parts = self._ARTICLE_RE.split(text)
        chunks: list[str] = []
        current_header = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if this part is an article header
            if self._ARTICLE_RE.fullmatch(part):
                current_header = part
                continue

            # Split the article body into individual clauses
            clauses = self._CLAUSE_RE.split(part)

            for clause in clauses:
                clause = clause.strip()
                if not clause:
                    continue

                # Build chunk: header + clause content
                if current_header:
                    chunk_text = f"{current_header}\n{clause}"
                else:
                    chunk_text = clause

                # If the chunk is still too large, split by sentences
                if len(chunk_text) > self.chunk_size:
                    sub_chunks = self._split_long_clause(chunk_text)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(chunk_text)

        return chunks

    def _split_long_clause(self, text: str) -> list[str]:
        """Split an oversized clause by sentence boundaries.

        Args:
            text: A clause text that exceeds chunk_size.

        Returns:
            List of sub-chunks, each within chunk_size.
        """
        sentences = re.split(r'(?<=[.;])\s+', text)
        result: list[str] = []
        current = ""

        for sent in sentences:
            if current and len(current) + len(sent) + 1 > self.chunk_size:
                result.append(current.strip())
                current = sent
            else:
                current = f"{current} {sent}" if current else sent

        if current.strip():
            result.append(current.strip())

        return result


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # TODO: implement cosine similarity formula
    # DONE
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))
    
    if mag_a == 0 or mag_b == 0:
        return 0.0
        
    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # TODO: call each chunker, compute stats, return comparison dict
        # DONE
        results = {}
        
        chunkers = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size)
        }
        
        for name, chunker in chunkers.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0
            
            results[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks
            }
            
        return results
