import logging
from pathlib import Path
from time import perf_counter

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

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
}


class OCRService(BaseAIService):
    """Parse a document, run OCR, and return a structured result."""

    def __init__(self, engine=None):
        self.engine = engine if engine is not None else PaddleOCREngine()

    @property
    def stage(self):
        return ProcessingStage.OCR

    def run(self, document, intelligence) -> ProcessingResult:
        started_at = perf_counter()
        document_id = getattr(document, "id", "unknown")
        filename = getattr(document, "filename", "unknown")

        logger.info(
            "OCR started | document=%s | file=%s",
            document_id,
            filename,
        )

        try:
            file_path = Path(document.file.path)

            if not file_path.is_file():
                return self._failure(f"Document file does not exist: {file_path}")

            suffix = file_path.suffix.lower()

            # Parse the document.
            if suffix == ".pdf":
                images = PDFParser.parse(file_path)

            elif suffix in SUPPORTED_IMAGE_EXTENSIONS:
                image = ImageParser.parse(file_path)
                images = [image]

            else:
                return self._failure(f"Unsupported file type: {suffix}")

            # Validate parser output before calling PaddleOCR.
            if images is None:
                return self._failure("Document parser returned None.")

            if not isinstance(images, (list, tuple)):
                return self._failure("Document parser must return a list of images.")

            if not images:
                return self._failure("Document parser returned no pages.")

            for index, image in enumerate(images):
                if image is None:
                    return self._failure(f"Parser returned None for page {index + 1}.")

                # Supports NumPy arrays without importing NumPy here.
                if getattr(image, "size", 1) == 0:
                    return self._failure(
                        f"Parser returned an empty image on page " f"{index + 1}."
                    )

            logger.info(
                "Document parsed | document=%s | pages=%d",
                document_id,
                len(images),
            )

            # Execute OCR.
            ocr_result = self.engine.process(images)

            if ocr_result is None:
                return self._failure("OCR engine returned None.")

            page_count = getattr(ocr_result, "page_count", len(images))
            average_confidence = getattr(ocr_result, "average_confidence", None)
            processing_time = getattr(
                ocr_result,
                "processing_time",
                perf_counter() - started_at,
            )

            logger.info(
                "OCR completed | document=%s | pages=%s | "
                "confidence=%s | time=%.2fs",
                document_id,
                page_count,
                (
                    f"{average_confidence:.2f}"
                    if isinstance(average_confidence, (int, float))
                    else "N/A"
                ),
                (processing_time if isinstance(processing_time, (int, float)) else 0.0),
            )

            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.SUCCESS,
                message="OCR completed successfully.",
                payload={"ocr_result": ocr_result},
            )

        except Exception as exc:
            logger.exception(
                "OCR failed | document=%s | file=%s",
                document_id,
                filename,
            )

            return self._failure(f"OCR processing failed: {type(exc).__name__}: {exc}")

    def _failure(self, message: str) -> ProcessingResult:
        logger.error("OCR failure | %s", message)

        return ProcessingResult(
            stage=self.stage,
            status=ProcessingStatus.FAILED,
            message=message,
        )
