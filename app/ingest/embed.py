"""Lazy local sentence-transformers wrapper; no embedding API is used."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings


class EmbeddingModel:
    """Load a local multilingual encoder once and normalize its vectors."""

    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name or get_settings().embedding_model
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        if self.dimension is None:
            raise RuntimeError(f"Could not determine embedding dimension for {self.model_name}")

    def _prepare(self, texts: list[str], *, kind: str) -> list[str]:
        if "multilingual-e5" in self.model_name.lower():
            prefix = "query: " if kind == "query" else "passage: "
            return [prefix + text for text in texts]
        # BGE-M3 does not use the E5 query/passage prefix convention.
        return texts

    def encode(self, texts: list[str], *, kind: str = "passage", batch_size: int = 32) -> list[list[float]]:
        if kind not in {"query", "passage"}:
            raise ValueError("kind must be 'query' or 'passage'")
        if not texts:
            return []
        vectors = self.model.encode(
            self._prepare(texts, kind=kind),
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


@lru_cache(maxsize=2)
def get_embedder(model_name: str | None = None) -> EmbeddingModel:
    """Reuse a model object across an ingestion run and subsequent calls."""
    return EmbeddingModel(model_name)


def get_embedding_dimension(model_name: str | None = None) -> int:
    return int(get_embedder(model_name).dimension)
