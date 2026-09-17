import logging
from time import perf_counter

from ..schemas.base import ProcessingStatus, ProcessingStage
from ..models import ProcessingLog

logger = logging.getLogger(__name__)


class ProcessingManager:
    """
    Orchestrates the complete AI document processing pipeline.
    """

    def __init__(self, pipeline):
        """
        Args:
            pipeline: List of AI service instances.
        """
        self.pipeline = pipeline

    def process_document(self, document, intelligence):
        """
        Execute all AI services sequentially.
        """

        intelligence.processing_status = ProcessingStatus.RUNNING.value
        intelligence.save(update_fields=["processing_status"])

        logger.info(
            "AI processing started | document=%s | file=%s",
            document.id,
            document.filename,
        )

        for service in self.pipeline:

            logger.info(
                "Processing stage started | document=%s | stage=%s",
                document.id,
                service.stage.value,
            )

            start = perf_counter()

            result = service.run(document, intelligence)

            result.execution_time = perf_counter() - start

            logger.info(
                "Processing stage completed | document=%s | stage=%s | status=%s | time=%.2fs",
                document.id,
                service.stage.value,
                result.status.value,
                result.execution_time,
            )

            ProcessingLog.objects.create(
                document=document,
                stage=service.stage.value,
                status=result.status.value,
                message=result.message,
                execution_time=result.execution_time,
            )

            if service.stage is ProcessingStage.OCR:

                ocr = result.payload["ocr_result"]

                intelligence.ocr_text = ocr.full_text
                intelligence.ocr_pages = ocr.model_dump()
                intelligence.confidence_score = ocr.average_confidence

                intelligence.processing_stage = service.stage.value
                intelligence.processing_status = ProcessingStatus.SUCCESS.value

                intelligence.save(
                    update_fields=[
                        "ocr_text",
                        "ocr_pages",
                        "confidence_score",
                        "processing_stage",
                        "processing_status",
                    ]
                )

            if service.stage is ProcessingStage.INTELLIGENCE:
                intelligence_result = result.payload["intelligence_result"]

                intelligence.document_type = (
                    intelligence_result.classification.document_type or ""
                )

                intelligence.confidence_score = intelligence_result.confidence

                intelligence.extracted_metadata = {
                    "classification": (
                        intelligence_result.classification.model_dump()
                    ),
                    "project": (
                        intelligence_result.metadata.project.model_dump()
                    ),
                    "drawing": (
                        intelligence_result.metadata.drawing.model_dump()
                        if intelligence_result.metadata.drawing
                        else None
                    ),
                    "keywords": intelligence_result.keywords,
                    "summary": intelligence_result.summary,
                }

                intelligence.processing_stage = service.stage.value
                intelligence.processing_status = ProcessingStatus.SUCCESS.value
                intelligence.last_error = ""

                intelligence.save(
                    update_fields=[
                        "document_type",
                        "confidence_score",
                        "extracted_metadata",
                        "processing_stage",
                        "processing_status",
                        "last_error",
                    ]
                )

            if result.status == ProcessingStatus.FAILED:

                intelligence.processing_stage = service.stage.value
                intelligence.processing_status = ProcessingStatus.FAILED.value
                intelligence.last_error = result.message

                intelligence.save(
                    update_fields=[
                        "processing_stage",
                        "processing_status",
                        "last_error",
                    ]
                )

                logger.error(
                    "Processing stage failed | document=%s | stage=%s | error=%s",
                    document.id,
                    service.stage.value,
                    result.message,
                )

                return result

        intelligence.processing_status = ProcessingStatus.SUCCESS.value
        intelligence.save(update_fields=["processing_status"])

        logger.info(
            "AI processing completed | document=%s | status=SUCCESS",
            document.id,
        )

        return result   
