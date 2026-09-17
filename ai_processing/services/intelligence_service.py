import logging

from ai_processing.engines.intelligence_engine import IntelligenceEngine
from ai_processing.schemas.base import (
    ProcessingResult,
    ProcessingStage,
    ProcessingStatus,
)
from ai_processing.schemas.intelligence_schema import (
    DocumentIntelligenceResult,
)
from ai_processing.services.base_service import BaseAIService

logger = logging.getLogger(__name__)


class IntelligenceService(BaseAIService):
    """
    Document Intelligence service.

    Takes OCR output and converts it into structured
    document intelligence using the configured LLM engine.
    """

    def __init__(self, engine=None):
        self.engine = engine or IntelligenceEngine()

    @property
    def stage(self):
        return ProcessingStage.INTELLIGENCE

    def run(self, document, intelligence) -> ProcessingResult:
        """
        Execute document intelligence processing.

        Args:
            document:
                Django Document instance.

            intelligence:
                Current DocumentIntelligence instance.

        Returns:
            ProcessingResult containing DocumentIntelligenceResult.
        """

        logger.info(
            "Starting document intelligence for document %s",
            document.id,
        )

        if not intelligence:
            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message="Document intelligence record is required.",
            )

        ocr_text = intelligence.ocr_text

        if not ocr_text or not ocr_text.strip():
            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message="OCR text is empty. Cannot perform document intelligence.",
            )

        try:
            result: DocumentIntelligenceResult = self.engine.process(ocr_text=ocr_text)

            self.save_result(
                intelligence=intelligence,
                result=result,
            )

            logger.info(
                "Document intelligence completed for document %s",
                document.id,
            )

            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.SUCCESS,
                message="Document intelligence completed successfully.",
                payload={
                    "intelligence_result": result,
                },
            )

        except Exception as exc:
            logger.exception(
                "Document intelligence failed for document %s",
                document.id,
            )

            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message=f"Document intelligence failed: {str(exc)}",
            )

    def save_result(self, intelligence, result):
        """
        Persist the DocumentIntelligenceResult into
        the existing DocumentIntelligence model.
        """

        intelligence.document_type = result.classification.document_type or ""

        intelligence.confidence_score = result.confidence

        intelligence.extracted_metadata = {
            "classification": (result.classification.model_dump()),
            "project": (result.metadata.project.model_dump()),
            "drawing": (
                result.metadata.drawing.model_dump()
                if result.metadata.drawing
                else None
            ),
            "keywords": result.keywords,
            "summary": result.summary,
        }

        intelligence.last_error = ""

        intelligence.save(
            update_fields=[
                "document_type",
                "confidence_score",
                "extracted_metadata",
                "last_error",
                "updated_at",
            ]
        )
