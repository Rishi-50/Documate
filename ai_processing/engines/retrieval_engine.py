import math
from typing import Sequence

from ai_processing.schemas.retrieval_schema import (
    RetrievalCandidate,
    RetrievalResult,
    RetrievedChunk,
)


class RetrievalEngine:
    """
    Ranks project document chunks by cosine similarity.
    """

    def retrieve(
        self,
        query_vector: Sequence[float],
        candidates: Sequence[RetrievalCandidate],
        limit: int = 5,
    ) -> RetrievalResult:
        if not query_vector:
            raise ValueError("Query embedding cannot be empty.")
        if limit < 1:
            raise ValueError("Retrieval limit must be greater than zero.")

        ranked = []

        for candidate in candidates:
            if len(candidate.vector) != len(query_vector):
                raise ValueError(
                    "Query and document embeddings have different dimensions."
                )

            score = self._cosine_similarity(query_vector, candidate.vector)
            ranked.append(
                RetrievedChunk(
                    chunk_id=candidate.chunk_id,
                    document_id=candidate.document_id,
                    filename=candidate.filename,
                    page_number=candidate.page_number,
                    text=candidate.text,
                    similarity=score,
                )
            )

        ranked.sort(key=lambda chunk: chunk.similarity, reverse=True)
        return RetrievalResult(chunks=ranked[:limit])

    @staticmethod
    def _cosine_similarity(
        left: Sequence[float],
        right: Sequence[float],
    ) -> float:
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(left, right))
        return dot_product / (left_norm * right_norm)
