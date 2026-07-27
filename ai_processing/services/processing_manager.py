import logging
from time import perf_counter

from ..schemas.base import ProcessingStatus

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

        logger.info("Starting processing for document %s", document.id)

        for service in self.pipeline:

            logger.info("Running %s...", service.stage.value)

            start = perf_counter()

            result = service.run(document, intelligence)

            result.execution_time = perf_counter() - start

            if result.status == ProcessingStatus.FAILED:

                logger.error(
                    "%s failed: %s",
                    service.stage.value,
                    result.message,
                )

                return result

        logger.info("Processing completed.")

        return result