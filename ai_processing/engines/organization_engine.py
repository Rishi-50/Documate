from pathlib import Path
from typing import Optional

from ai_processing.schemas.intelligence_schema import (
    DocumentIntelligenceResult,
)
from ai_processing.schemas.organization_schema import (
    OrganizationResult,
)


class OrganizationEngine:
    """
    Determines the standardized location and filename for a document
    based on the output of Document Intelligence.

    This engine does not perform any filesystem operations.
    """

    DISCIPLINES = {
        "architectural": "Architectural",
        "architecture": "Architectural",
        "structural": "Structural",
        "structure": "Structural",
        "electrical": "Electrical",
        "electric": "Electrical",
        "mechanical": "Mechanical",
        "mechanic": "Mechanical",
    }

    DOCUMENT_TYPES = {
        "drawing": "Drawings",
        "plan": "Drawings",
        "specification": "Specifications",
        "spec": "Specifications",
        "report": "Reports",
    }

    def organize(
        self,
        intelligence: DocumentIntelligenceResult,
        project_name: str,
        original_filename: str,
    ) -> OrganizationResult:
        """
        Generate an organization decision from document intelligence.

        Args:
            intelligence: Output from Document Intelligence.
            project_name: Name of the Django project.
            original_filename: Original uploaded filename.

        Returns:
            OrganizationResult containing the target directory,
            filename and path.
        """

        safe_project_name = self._normalize_name(project_name)

        discipline = self._get_discipline(intelligence)
        document_type = self._get_document_type(intelligence)

        target_directory = self._build_directory(
            safe_project_name,
            discipline,
            document_type,
        )

        target_filename = self._build_filename(
            intelligence,
            original_filename,
        )

        target_path = f"{target_directory}/{target_filename}"

        organization_category = self._build_category(
            discipline,
            document_type,
        )

        reason = self._build_reason(
            intelligence,
            discipline,
            document_type,
        )

        return OrganizationResult(
            organization_category=organization_category,
            target_directory=target_directory,
            target_filename=target_filename,
            target_path=target_path,
            status="success",
            reason=reason,
        )

    # ---------------------------------------------------------
    # Discipline
    # ---------------------------------------------------------

    def _get_discipline(
        self,
        intelligence: DocumentIntelligenceResult,
    ) -> str:
        """
        Determine the discipline from drawing metadata.

        Falls back to Unclassified when discipline is unavailable.
        """

        drawing = intelligence.metadata.drawing

        if drawing and drawing.discipline:
            discipline = drawing.discipline.strip().lower()

            for key, value in self.DISCIPLINES.items():
                if key in discipline:
                    return value

        return "Unclassified"

    # ---------------------------------------------------------
    # Document Type
    # ---------------------------------------------------------

    def _get_document_type(
        self,
        intelligence: DocumentIntelligenceResult,
    ) -> str:
        """
        Determine the target document folder from classification.
        """

        document_type = intelligence.classification.document_type

        if not document_type:
            return "Other"

        normalized_type = document_type.strip().lower()

        for key, value in self.DOCUMENT_TYPES.items():
            if key in normalized_type:
                return value

        return "Other"

    # ---------------------------------------------------------
    # Directory
    # ---------------------------------------------------------

    def _build_directory(
        self,
        project_name: str,
        discipline: str,
        document_type: str,
    ) -> str:
        """
        Build the relative target directory.
        """

        return "/".join(
            [
                project_name,
                discipline,
                document_type,
            ]
        )

    # ---------------------------------------------------------
    # Filename
    # ---------------------------------------------------------

    def _build_filename(
        self,
        intelligence: DocumentIntelligenceResult,
        original_filename: str,
    ) -> str:
        """
        Build a standardized filename.

        Drawings:
            drawing_number_drawing_title_revision.ext

        Other documents:
            document_name.ext

        Missing metadata falls back safely to available information.
        """

        extension = Path(original_filename).suffix.lower()

        drawing = intelligence.metadata.drawing

        # Drawing document
        if self._is_drawing(intelligence):

            parts = []

            if drawing:
                if drawing.drawing_number:
                    parts.append(self._normalize_name(drawing.drawing_number))

                if drawing.drawing_title:
                    parts.append(self._normalize_name(drawing.drawing_title))

                if drawing.revision:
                    parts.append(self._normalize_name(drawing.revision))

            if parts:
                return "_".join(parts) + extension

        # Non-drawing document
        document_name = intelligence.classification.name

        if document_name:
            return self._normalize_name(document_name) + extension

        # Final fallback: original filename
        original_stem = Path(original_filename).stem

        return self._normalize_name(original_stem) + extension

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _is_drawing(
        self,
        intelligence: DocumentIntelligenceResult,
    ) -> bool:
        """
        Determine whether the document is a drawing.
        """

        document_type = (intelligence.classification.document_type or "").lower()

        category = (intelligence.classification.category or "").lower()

        return (
            "drawing" in document_type
            or "drawing" in category
            or "plan" in document_type
            or "plan" in category
        )

    def _build_category(
        self,
        discipline: str,
        document_type: str,
    ) -> str:
        """
        Build a human-readable organization category.
        """

        if discipline == "Unclassified":
            return "Unclassified"

        return f"{discipline} {document_type[:-1]}"

    def _build_reason(
        self,
        intelligence: DocumentIntelligenceResult,
        discipline: str,
        document_type: str,
    ) -> str:
        """
        Build a simple explanation of the organization decision.
        """

        original_type = intelligence.classification.document_type

        if original_type:
            return (
                f"Document classified as '{original_type}' "
                f"and organized under "
                f"{discipline}/{document_type}."
            )

        return (
            "Document classification was unavailable; "
            "safe fallback organization was used."
        )

    @staticmethod
    def _normalize_name(value: Optional[str]) -> str:
        """
        Convert a value into a filesystem-safe filename/folder component.
        """

        if not value:
            return "Unknown"

        value = value.strip()

        unsafe_characters = '<>:"/\\|?*'

        for character in unsafe_characters:
            value = value.replace(character, "")

        value = value.replace(" ", "_")

        while "__" in value:
            value = value.replace("__", "_")

        return value.strip("._ ")
