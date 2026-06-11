import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture(autouse=True)
def stub_embedding_service(monkeypatch: pytest.MonkeyPatch):
    """Prevent tests from making real OpenAI embedding API calls."""
    monkeypatch.setattr("app.services.law_embedding_service.settings.openai_api_key", None)
    monkeypatch.setattr("app.services.document_generation_service.settings.openai_api_key", None)

    def _fake_generate_embedding(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Embedding text is empty")
        # Keep vector size stable with app defaults.
        return [0.0] * int(getattr(self, "vector_dimension", 3072))

    monkeypatch.setattr(
        "app.services.embedding_service.EmbeddingService.generate_embedding",
        _fake_generate_embedding,
    )
