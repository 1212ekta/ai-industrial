"""Splits parsed document pages into overlapping, page-aware text chunks."""
from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.parser import ParsedDocument


@dataclass
class TextChunk:
    chunk_index: int
    page_number: int | None
    content: str
    token_count: int


class TextChunker:
    """Approximate token-based chunker (word-count proxy, ~4 chars/token)."""

    def __init__(self, chunk_size_tokens: int = 500, overlap_tokens: int = 50):
        self.chunk_size_tokens = chunk_size_tokens
        self.overlap_tokens = overlap_tokens
        # crude approximation: 1 token ~= 0.75 words
        self.chunk_size_words = int(chunk_size_tokens * 0.75)
        self.overlap_words = int(overlap_tokens * 0.75)

    def chunk_document(self, parsed: ParsedDocument) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        chunk_index = 0

        for page in parsed.pages:
            words = page.text.split()
            if not words:
                continue

            start = 0
            while start < len(words):
                end = min(start + self.chunk_size_words, len(words))
                chunk_words = words[start:end]
                content = " ".join(chunk_words)
                chunks.append(
                    TextChunk(
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        content=content,
                        token_count=int(len(chunk_words) / 0.75),
                    )
                )
                chunk_index += 1
                if end == len(words):
                    break
                start = end - self.overlap_words

            # Append table content as its own chunk(s) so tabular data is searchable.
            for table in page.tables:
                table_text = self._table_to_text(table.rows)
                if table_text.strip():
                    chunks.append(
                        TextChunk(
                            chunk_index=chunk_index,
                            page_number=page.page_number,
                            content=table_text,
                            token_count=int(len(table_text.split()) / 0.75),
                        )
                    )
                    chunk_index += 1

        return chunks

    @staticmethod
    def _table_to_text(rows: list[list[str]]) -> str:
        lines = []
        for row in rows:
            clean_row = [str(cell) if cell is not None else "" for cell in row]
            lines.append(" | ".join(clean_row))
        return "\n".join(lines)
