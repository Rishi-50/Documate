import logging

from django.db import transaction

from ai_processing.engines.embedding_engine import EmbeddingEngine
from ai_processing.models import DocumentEmbedding
from ai_processing.schemas.base import (
    ProcessingResult,
    ProcessingStage,
    ProcessingStatus,
)
from ai_processing.schemas.embedding_schema import DocumentChunk
from ai_processing.services.base_service import BaseAIService

logger = logging.getLogger(__name__)


class EmbeddingService(BaseAIService):
    MAX_CHUNK_LENGTH = 1200
    CHUNK_OVERLAP = 200

    def __init__(self, engine=None):
        self.engine = engine or EmbeddingEngine()

    @property
    def stage(self):
        return ProcessingStage.EMBEDDING

    def run(self, document, intelligence) -> ProcessingResult:
        logger.info("Generating embeddings for %s", document.id)

        if not intelligence or not intelligence.ocr_text.strip():
            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message="OCR text is empty. Cannot generate document embeddings.",
            )

        chunks = self._create_chunks(intelligence)
        if not chunks:
            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message="No text chunks were available to embed.",
            )

        try:
            vectors = [
                self.engine.embed(
                    chunk.text,
                    task_type="RETRIEVAL_DOCUMENT",
                )
                for chunk in chunks
            ]

            with transaction.atomic():
                DocumentEmbedding.objects.filter(document=document).delete()
                DocumentEmbedding.objects.bulk_create(
                    [
                        DocumentEmbedding(
                            document=document,
                            chunk_index=chunk.chunk_index,
                            page_number=chunk.page_number,
                            text=chunk.text,
                            vector=vector,
                        )
                        for chunk, vector in zip(chunks, vectors)
                    ]
                )

                intelligence.embeddings_created = True
                intelligence.save(update_fields=["embeddings_created", "updated_at"])

            logger.info(
                "Generated %s embeddings for document %s",
                len(chunks),
                document.id,
            )

            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.SUCCESS,
                message="Document embeddings generated successfully.",
                payload={"chunk_count": len(chunks)},
            )

        except Exception as exc:
            logger.exception(
                "Embedding generation failed for document %s",
                document.id,
            )
            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message=f"Embedding generation failed: {exc}",
            )

    def _create_chunks(self, intelligence) -> list[DocumentChunk]:
        stored_ocr = intelligence.ocr_pages or {}
        pages = stored_ocr.get("pages", []) if isinstance(stored_ocr, dict) else []
        page_texts = [
            (page.get("page_number"), page.get("text", ""))
            for page in pages
            if isinstance(page, dict) and page.get("text", "").strip()
        ]

        if not page_texts:
            page_texts = [(None, intelligence.ocr_text)]

        chunks = []
        for page_number, text in page_texts:
            words = text.split()
            start = 0
            while start < len(words):
                end = start
                chunk_length = 0

                while end < len(words):
                    word_length = len(words[end]) + (1 if end > start else 0)
                    if (
                        end > start
                        and chunk_length + word_length > self.MAX_CHUNK_LENGTH
                    ):
                        break

                    chunk_length += word_length
                    end += 1

                chunk_text = " ".join(words[start:end])
                if chunk_text:
                    chunks.append(
                        DocumentChunk(
                            chunk_index=len(chunks),
                            page_number=page_number,
                            text=chunk_text,
                        )
                    )

                if end >= len(words):
                    break

                overlap_start = end
                overlap_length = 0
                while overlap_start > start:
                    word_length = len(words[overlap_start - 1]) + 1
                    if overlap_length + word_length > self.CHUNK_OVERLAP:
                        break
                    overlap_length += word_length
                    overlap_start -= 1

                start = overlap_start if overlap_start > start else end

        return chunks
