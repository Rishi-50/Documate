import logging

from ai_processing.schemas.base import (
    ProcessingResult,
    ProcessingStage,
    ProcessingStatus,
)
from ai_processing.services.base_service import BaseAIService

logger = logging.getLogger(__name__)


class IntelligenceService(BaseAIService):

    @property
    def stage(self):
        return ProcessingStage.INTELLIGENCE

    def run(self, document, intelligence) -> ProcessingResult:

        logger.info("Running document intelligence for %s", document.id)

        return ProcessingResult(
            stage=self.stage,
            status=ProcessingStatus.SUCCESS,
            message="Document intelligence completed successfully.",
            payload={}
        )