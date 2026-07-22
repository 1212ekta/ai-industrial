"""LLM-based entity and relation extraction from document chunk text."""
from __future__ import annotations

import json
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import logger
from app.services.extraction.schema import ENTITY_TYPES, RELATION_TYPES

SYSTEM_PROMPT = f"""You are an information extraction engine for industrial engineering
documents (SOPs, inspection reports, maintenance logs, manuals, compliance docs).

Extract entities strictly from this taxonomy: {", ".join(ENTITY_TYPES)}
Extract relations strictly from this taxonomy: {", ".join(RELATION_TYPES)}

Rules:
- Only extract what is explicitly stated or unambiguously implied in the text.
- Normalize equipment tags to their canonical form (e.g. "Pump P-101" -> "P101").
- confidence is a float 0-1 reflecting how certain the extraction is.
- Respond with ONLY valid JSON matching this shape, no prose, no markdown fences:
{{
  "entities": [{{"type": "...", "value": "...", "confidence": 0.0}}],
  "relations": [{{"source": "...", "relation": "...", "target": "..."}}]
}}
If nothing relevant is found, return {{"entities": [], "relations": []}}.
"""


@dataclass
class ExtractedEntity:
    entity_type: str
    value: str
    confidence: float


@dataclass
class ExtractedRelation:
    source: str
    relation: str
    target: str


@dataclass
class ExtractionResult:
    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]


class EntityExtractionService:
    def __init__(self):
        from openai import OpenAI

        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_chat_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def extract(self, chunk_text: str, context_summary: str = "") -> ExtractionResult:
        """Extract entities/relations from a single chunk. `context_summary` is a
        short rolling summary of previously seen chunks to help resolve references
        like "the pump" to a concrete tag mentioned earlier in the document."""
        if not chunk_text.strip():
            return ExtractionResult(entities=[], relations=[])

        user_content = chunk_text
        if context_summary:
            user_content = f"Prior context summary: {context_summary}\n\nChunk text:\n{chunk_text}"

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            raw = response.choices[0].message.content
            parsed = json.loads(raw)
        except Exception as exc:
            logger.error(f"Entity extraction failed: {exc}")
            return ExtractionResult(entities=[], relations=[])

        entities = [
            ExtractedEntity(
                entity_type=e.get("type", "Equipment"),
                value=e.get("value", "").strip(),
                confidence=float(e.get("confidence", 0.5)),
            )
            for e in parsed.get("entities", [])
            if e.get("value", "").strip()
        ]
        relations = [
            ExtractedRelation(
                source=r.get("source", "").strip(),
                relation=r.get("relation", ""),
                target=r.get("target", "").strip(),
            )
            for r in parsed.get("relations", [])
            if r.get("source") and r.get("target") and r.get("relation")
        ]
        return ExtractionResult(entities=entities, relations=relations)

    @staticmethod
    def summarize_for_context(entities: list[ExtractedEntity]) -> str:
        """Cheap rolling-context summary: just list distinct equipment/engineer/vendor
        values seen so far, so the next chunk's extraction can resolve pronouns/refs."""
        interesting_types = {"Equipment", "Pump", "Valve", "Motor", "Boiler", "Compressor", "Engineer", "Vendor"}
        values = sorted({e.value for e in entities if e.entity_type in interesting_types})
        return ", ".join(values[:30])
