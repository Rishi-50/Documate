import logging
from pathlib import Path

from ai_processing.engines.ocr_engine import PaddleOCREngine
from ai_processing.parsers.image_parser import ImageParser
from ai_processing.parsers.pdf_parser import PDFParser
from ai_processing.schemas.base import (
    ProcessingResult,
    ProcessingStage,
    ProcessingStatus,
)
from ai_processing.services.base_service import BaseAIService

logger = logging.getLogger(__name__)


class OCRService(BaseAIService):
    """
    Executes the OCR workflow.

    Responsibilities:
    - Determine the document type
    - Parse the document into images
    - Execute OCR
    - Return the OCR result
    """

    def __init__(self, engine=None):
        self.engine = engine or PaddleOCREngine()

    @property
    def stage(self):
        return ProcessingStage.OCR

    def run(self, document, intelligence) -> ProcessingResult:
        """
        Execute OCR for a document.
        """

        logger.info(
            "Starting OCR for document %s",
            document.id,
        )

        file_path = Path(document.file.path)

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            images = PDFParser.parse(file_path)

        elif suffix in [
            ".png",
            ".jpg",
            ".jpeg",
            ".tif",
            ".tiff",
            ".bmp",
        ]:
            images = [
                ImageParser.parse(file_path)
            ]

        else:
            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message=f"Unsupported file type: {suffix}",
            )

        ocr_result = self.engine.process(images)

        return ProcessingResult(
            stage=self.stage,
            status=ProcessingStatus.SUCCESS,
            message="OCR completed successfully.",
            payload={
                "ocr_result": ocr_result,
            },
        )