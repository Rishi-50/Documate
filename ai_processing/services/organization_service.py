"""Application service for safe, auditable document organization."""

import logging
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation

from ai_processing.engines.organization_engine import OrganizationEngine
from ai_processing.services.file_organizer import FileOrganizer
from ai_processing.schemas.base import (
    ProcessingResult,
    ProcessingStage,
    ProcessingStatus,
)
from ai_processing.schemas.intelligence_schema import DocumentIntelligenceResult

logger = logging.getLogger(__name__)


class OrganizationService:
    """Coordinate classification decisions and filesystem organization."""

    def __init__(self, engine=None, organizer=None, root_directory=None):
        self.engine = engine if engine is not None else OrganizationEngine()
        if organizer is not None:
            self.organizer = organizer
        else:
            if root_directory is None:
                root_directory = Path(settings.MEDIA_ROOT) / "projects"
            self.organizer = FileOrganizer(root_directory=root_directory)

    @property
    def stage(self):
        return ProcessingStage.ORGANIZATION

    def run(self, document, intelligence) -> ProcessingResult:
        document_id = getattr(document, "id", "unknown")
        filename = getattr(document, "filename", "unknown")
        logger.info(
            "Starting organization | document=%s | file=%s",
            document_id,
            filename,
        )

        try:
            extracted_metadata = getattr(intelligence, "extracted_metadata", None) or {}
            if not isinstance(extracted_metadata, dict):
                raise TypeError("intelligence.extracted_metadata must be a dictionary")

            # Missing optional values are deliberately represented as empty values;
            # the engine will route insufficient evidence to Needs_Review.
            intelligence_result = DocumentIntelligenceResult(
                classification=extracted_metadata.get("classification") or {},
                metadata={
                    "project": extracted_metadata.get("project") or {},
                    "drawing": extracted_metadata.get("drawing") or {},
                },
                keywords=extracted_metadata.get("keywords") or [],
                summary=extracted_metadata.get("summary") or "",
                confidence=(getattr(intelligence, "confidence_score", None) or 0.0),
            )

            project = getattr(document, "project", None)
            project_name = getattr(project, "name", None) or "Project"
            source_path = Path(document.file.path).resolve()
            if not source_path.is_file():
                raise FileNotFoundError(f"Source document does not exist: {source_path}")

            organization_result = self.engine.organize(
                intelligence=intelligence_result,
                project_name=project_name,
                original_filename=filename or source_path.name,
            )

            storage = document.file.storage
            storage_root = Path(storage.path("")).resolve()

            if isinstance(self.organizer, FileOrganizer):
                organization_root = Path(self.organizer.root_directory).resolve()
                if not self._is_within(organization_root, storage_root):
                    raise SuspiciousFileOperation(
                        "Organization root must be inside the document storage."
                    )

            final_path = Path(
                self.organizer.organize(
                    source_path=source_path,
                    organization_result=organization_result,
                )
            ).resolve()

            # Do not persist a path that escapes the storage backend's local root.
            try:
                relative_path = final_path.relative_to(storage_root)
            except ValueError as exc:
                raise SuspiciousFileOperation(
                    "Organized file path is outside the document storage root."
                ) from exc

            document.file.name = relative_path.as_posix()
            document.save(update_fields=["file"])

            review_required = getattr(organization_result, "status", "") == "review_required"
            message = (
                "Document organized and flagged for review."
                if review_required
                else "Document organized successfully."
            )

            logger.info(
                "Organization completed | document=%s | category=%s | review_required=%s | path=%s",
                document_id,
                getattr(organization_result, "organization_category", "unknown"),
                review_required,
                final_path,
            )

            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.SUCCESS,
                message=message,
                payload={
                    "organization_result": organization_result,
                    "final_path": str(final_path),
                    "review_required": review_required,
                },
            )

        except Exception as exc:
            logger.exception(
                "Organization failed | document=%s | file=%s",
                document_id,
                filename,
            )
            return ProcessingResult(
                stage=self.stage,
                status=ProcessingStatus.FAILED,
                message=f"Organization failed: {type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False
