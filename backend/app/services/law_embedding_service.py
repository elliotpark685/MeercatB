import hashlib

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.law_chunk import LawChunk
from app.repositories.law_repository import LawRepository


class LawEmbeddingService:
    def __init__(
        self,
        db: Session,
        model_name: str = "text-embedding-3-small",
        mock_dimension: int = 1536,
    ) -> None:
        self.db = db
        self.repo = LawRepository(db)
        self.model_name = model_name
        self.mock_dimension = mock_dimension
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def embed_pending_chunks(self, limit: int | None = None) -> dict:
        chunks = self.repo.list_chunks_without_embedding(embedding_model=self.model_name, limit=limit)
        created_count = 0
        skipped_count = 0
        for chunk in chunks:
            result = self.embed_chunk(chunk)
            if result["status"] == "embedded":
                created_count += 1
            else:
                skipped_count += 1
        if self.db is not None:
            self.db.commit()
        return {"created_count": created_count, "skipped_count": skipped_count}

    def embed_chunk(self, chunk: LawChunk) -> dict:
        existing = self.repo.get_embedding_by_chunk_and_model(chunk_id=chunk.id, embedding_model=self.model_name)
        if existing is not None:
            return {"chunk_id": chunk.id, "embedding_id": existing.id, "status": "skipped_duplicate"}

        vector = self.generate_embedding(chunk.chunk_text)
        embedding = self.repo.create_law_embedding(
            article_id=None,
            chunk_id=chunk.id,
            embedding_model=self.model_name,
            embedding=vector,
            embedding_vector=vector,
        )
        return {"chunk_id": chunk.id, "embedding_id": embedding.id, "status": "embedded"}

    def generate_embedding(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Embedding text is empty")
        if self._client is None:
            return self._mock_embedding(text)
        try:
            response = self._client.embeddings.create(model=self.model_name, input=text)
            return response.data[0].embedding
        except Exception:
            return self._mock_embedding(text)

    def _mock_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        for index in range(self.mock_dimension):
            byte = digest[index % len(digest)]
            values.append(round((byte / 255.0) * 2 - 1, 6))
        return values
