from openai import OpenAI

from app.core.config import settings


class EmbeddingService:
    """OpenAI embedding service."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self.vector_dimension = settings.vector_dimension
        self._client = OpenAI(api_key=settings.openai_api_key)

    def generate_embedding(self, text: str) -> list[float]:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        if not text or not text.strip():
            raise ValueError("Embedding text is empty")

        response = self._client.embeddings.create(
            model=self.model_name,
            input=text,
        )
        return response.data[0].embedding
