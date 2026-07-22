"""Wraps OpenAI's embeddings API with batching and retry logic."""
from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import logger


class EmbeddingService:
    def __init__(self):
        from openai import OpenAI

        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model
        self._dimensions = settings.openai_embedding_dimensions

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns one vector per input text, same order."""
        if not texts:
            return []
        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions,
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.error(f"Embedding request failed: {exc}")
            raise

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
