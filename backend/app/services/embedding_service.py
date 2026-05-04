from app.core.config import settings


class EmbeddingService:
    """Adapter service for embedding model integration."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self.vector_dimension = settings.vector_dimension

    def generate_embedding(self, text: str) -> list[float]:
        # Placeholder deterministic embedding for bootstrapping.
        # Replace with real embedding API integration for production.
        truncated = text[: self.vector_dimension]
        vector = [0.0] * self.vector_dimension
        for i, char in enumerate(truncated):
            vector[i] = (ord(char) % 255) / 255.0
        return vector
