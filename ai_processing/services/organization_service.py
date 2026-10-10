import logging
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation

from ai_processing.engines.organization_engine import (
    OrganizationEngine,
)
from ai_processing.services.file_organizer import (
    FileOrganizer,
)
from ai_processing.schemas.base import (
    ProcessingResult,
    ProcessingStage,
    ProcessingStatus,
)
from ai_processing.schemas.intelligence_schema import (
    DocumentIntelligenceResult,
)

logger = logging.getLogger(__name__)


class OrganizationService:
    """
    Coordinates document organization.

    Organization consumes the structured intelligence that was
    already persisted by the Document Intelligence stage.
    """

    def __init__(
        self,
        engine=None,
        organizer=None,
        root_directory=None,
    ):
        self.engine = engine or OrganizationEngine()

        if organizer is not None:
            self.organizer = organizer
        else:
            if root_directory is None:
                root_directory = Path(settings.MEDIA_ROOT) / "projects"

            self.organizer = FileOrganizer(root_directory=root_directory)

    @property
    def stage(self):
        return ProcessingStage.ORGANIZATION

    def run(
        self,
        document,
        intelligence,
    ) -> ProcessingResult:
        """
        Organize a document using the intelligence already
        persisted by the Document Intelligence stage.
        """

        logger.info(
            "Starting organization for document %s",
            document.id,
        )

        try:
            extracted_metadata = intelligence.extracted_metadata or {}

            intelligence_result = DocumentIntelligenceResult(
                classification=extracted_metadata.get(
                    "classification",
                    {},
                ),
                metadata={
                    "project": extracted_metadata.get(
                        "project",
                        {},
                    ),
                    "drawing": extracted_metadata.get(
                        "drawing",
                    ),
                },
                keywords=extracted_metadata.get(
                    "keywords",
                    [],
                ),
                summary=extracted_metadata.get(
                    "summary",
                ),
                confidence=(intelligence.confidence_score or 0.0),
            )

            project_name = document.project.name

            organization_result = self.engine.organize(
                intelligence=intelligence_result,
                project_name=project_name,
                original_filename=document.filename,
            )

            source_path = Path(document.file.path)
            storage_root = Path(document.file.storage.path("")).resolve()

            if isinstance(self.organizer, FileOrganizer):
                if not self.organizer.root_directory.is_relative_to(storage_root):
                    raise SuspiciousFileOperation(
                        "Organization root must be inside the document storage."
                    )

            final_path = self.organizer.organize(
                source_path=source_path,
                organization_result=organization_result,
            )
            relative_path = final_path.resolve().relative_to(storage_root)
            document.file.name = relative_path.as_posix()
            document.save(update_fields=["file"])

            logger.info(
                "Document %s organized successfully: %s",
                document.id,
                final_path,
            )

            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.SUCCESS,
                message="Document organized successfully.",
                payload={
                    "organization_result": organization_result,
                    "final_path": str(final_path),
                },
            )

        except Exception as exc:
            logger.exception(
                "Organization failed for document %s",
                document.id,
            )

            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message=f"Organization failed: {exc}",
            )
