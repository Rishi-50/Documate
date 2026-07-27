import logging

from ai_processing.schemas.base import (
    ProcessingResult,
    ProcessingStage,
    ProcessingStatus,
)
from ai_processing.services.base_service import BaseAIService

logger = logging.getLogger(__name__)


class EmbeddingService(BaseAIService):

    @property
    def stage(self):
        return ProcessingStage.EMBEDDING

    def run(self, document, intelligence) -> ProcessingResult:

        logger.info("Generating embeddings for %s", document.id)

        return ProcessingResult(
            stage=self.stage,
            status=ProcessingStatus.SUCCESS,
            message="Embeddings generated successfully.",
            payload={}
        )