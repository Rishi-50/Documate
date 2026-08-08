from abc import ABC, abstractmethod

from ..schemas.base import ProcessingResult


class BaseAIService(ABC):
    """
    Base class for all AI processing services.
    Every AI service in the pipeline must inherit from this class.
    """

    @property
    @abstractmethod
    def stage(self):
        """
        Returns the processing stage handled by this service.
        Example:
            ProcessingStage.OCR
            ProcessingStage.INTELLIGENCE
        """
        pass

    @abstractmethod
    def run(self, document, intelligence) -> ProcessingResult:
        """
        Execute the service.

        Args:
            document:
                The Document model instance.

            intelligence:
                The DocumentIntelligence model instance.

        Returns:
            ProcessingResult
        """
        pass