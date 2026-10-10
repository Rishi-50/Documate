from ai_processing.engines.embedding_engine import EmbeddingEngine
from ai_processing.engines.retrieval_engine import RetrievalEngine
from ai_processing.models import DocumentEmbedding
from ai_processing.schemas.base import ProcessingStatus
from ai_processing.schemas.retrieval_schema import (
    RetrievalCandidate,
    RetrievalResult,
)


class RetrievalService:
    """
    Retrieves the most relevant project chunks from successfully processed files.
    """

    def __init__(self, embedding_engine=None, engine=None):
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.engine = engine or RetrievalEngine()

    def retrieve(
        self,
        project_id: int,
        question: str,
        limit: int = 5,
    ) -> RetrievalResult:
        embeddings = list(
            DocumentEmbedding.objects.filter(
                document__project_id=project_id,
                document__intelligence__processing_status=(
                    ProcessingStatus.SUCCESS.value
                ),
                document__intelligence__embeddings_created=True,
            ).select_related("document")
        )

        if not embeddings:
            return RetrievalResult()

        query_vector = self.embedding_engine.embed(
            question,
            task_type="RETRIEVAL_QUERY",
        )
        candidates = [
            RetrievalCandidate(
                chunk_id=embedding.id,
                document_id=embedding.document_id,
                filename=embedding.document.filename,
                page_number=embedding.page_number,
                text=embedding.text,
                vector=embedding.vector,
            )
            for embedding in embeddings
        ]

        return self.engine.retrieve(
            query_vector=query_vector,
            candidates=candidates,
            limit=limit,
        )
