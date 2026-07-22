"""Copilot service: orchestrates hybrid retrieval + GPT generation for RAG answers."""
from __future__ import annotations

import re

from app.core.config import get_settings
from app.core.logging import logger
from app.schemas.copilot import Citation, CopilotChatResponse
from app.services.rag.prompt_templates import build_copilot_prompt
from app.services.rag.retriever import HybridRetriever

CONFIDENCE_LINE_PATTERN = re.compile(r"CONFIDENCE:\s*([0-9.]+)", re.IGNORECASE)
CITATION_PATTERN = re.compile(r"\[Doc:\s*([^,]+),\s*p\.(\d+)\]")


class CopilotService:
    def __init__(self):
        from openai import OpenAI

        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_chat_model
        self._retriever = HybridRetriever()

    def ask(self, question: str, equipment_tag: str | None = None, top_k: int = 6) -> CopilotChatResponse:
        detected_tag = equipment_tag or self._retriever.detect_equipment_tag(question)

        chunks = self._retriever.retrieve_chunks(question, top_k=top_k, equipment_tag=detected_tag)
        graph_data = self._retriever.retrieve_graph_facts(detected_tag)

        chunk_excerpts = self._retriever.format_chunk_excerpts(chunks)
        graph_facts = self._retriever.format_graph_facts(graph_data)

        messages = build_copilot_prompt(graph_facts, chunk_excerpts, question)

        try:
            response = self._client.chat.completions.create(
                model=self._model, messages=messages, temperature=0.1
            )
            answer_raw = response.choices[0].message.content or ""
        except Exception as exc:
            logger.error(f"Copilot generation failed: {exc}")
            return CopilotChatResponse(
                answer="I wasn't able to generate an answer right now. Please try again.",
                citations=[],
                confidence=0.0,
                source_documents=[],
            )

        confidence = self._extract_confidence(answer_raw)
        answer_clean = CONFIDENCE_LINE_PATTERN.sub("", answer_raw).strip()

        citations = self._build_citations(answer_clean, chunks)
        source_documents = sorted({c.document_id for c in citations})

        return CopilotChatResponse(
            answer=answer_clean,
            citations=citations,
            confidence=confidence,
            source_documents=source_documents,
        )

    @staticmethod
    def _extract_confidence(text: str) -> float:
        match = CONFIDENCE_LINE_PATTERN.search(text)
        if not match:
            return 0.5
        try:
            return max(0.0, min(1.0, float(match.group(1))))
        except ValueError:
            return 0.5

    @staticmethod
    def _build_citations(answer_text: str, chunks) -> list[Citation]:
        cited_pairs = CITATION_PATTERN.findall(answer_text)
        citations: list[Citation] = []
        seen = set()
        for filename, page in cited_pairs:
            filename = filename.strip()
            page_num = int(page)
            key = (filename, page_num)
            if key in seen:
                continue
            seen.add(key)
            match = next(
                (c for c in chunks if c.filename == filename and c.page_number == page_num), None
            )
            if match:
                citations.append(
                    Citation(
                        document_id=match.document_id,
                        filename=match.filename,
                        page_number=match.page_number,
                        excerpt=match.content[:300],
                    )
                )
        # Fall back: if the model didn't emit inline citation tags, cite the top chunks.
        if not citations and chunks:
            for c in chunks[:3]:
                citations.append(
                    Citation(
                        document_id=c.document_id,
                        filename=c.filename,
                        page_number=c.page_number,
                        excerpt=c.content[:300],
                    )
                )
        return citations
