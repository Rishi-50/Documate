"""Rule-based, explainable document organization decisions."""

import re
from pathlib import Path
from typing import Any, Optional

from ai_processing.schemas.intelligence_schema import DocumentIntelligenceResult
from ai_processing.schemas.organization_schema import OrganizationResult


class OrganizationEngine:
    """Build a safe destination using structured intelligence and text hints.

    The engine does not move files. It prefers explicit extracted metadata,
    then falls back to classification fields, keywords, summary, and filename.
    Uncertain documents are routed to a review folder rather than silently
    assigned to an arbitrary business category.
    """

    # Each phrase maps to a stable folder name. Longer phrases are checked first.
    DISCIPLINE_RULES = (
        ("fire protection", "Fire_Protection"),
        ("mechanical", "Mechanical"),
        ("architectural", "Architectural"),
        ("architecture", "Architectural"),
        ("structural", "Structural"),
        ("structure", "Structural"),
        ("electrical", "Electrical"),
        ("electric", "Electrical"),
        ("plumbing", "Plumbing"),
        ("hydraulic", "Plumbing"),
        ("civil", "Civil"),
        ("landscape", "Landscape"),
        ("interior design", "Interiors"),
        ("interior", "Interiors"),
        ("geotechnical", "Geotechnical"),
    )

    DOCUMENT_TYPE_RULES = (
        (("change order", "variation order"), "Change_Orders"),
        (("purchase order", " po "), "Purchase_Orders"),
        (("invoice", "tax invoice", "bill"), "Invoices"),
        (("receipt", "payment receipt"), "Receipts"),
        (("contract", "agreement", "subcontract"), "Contracts"),
        (("specification", "specifications", "spec"), "Specifications"),
        (("submittal", "material submission", "product data"), "Submittals"),
        (("transmittal", "document register"), "Transmittals"),
        (("meeting minutes", "minutes of meeting", "mom"), "Meeting_Minutes"),
        (("inspection report", "site inspection", "inspection checklist"), "Inspection_Reports"),
        (("safety report", "incident report", "risk assessment", "method statement"), "Safety_and_Risk"),
        (("progress report", "weekly report", "monthly report"), "Progress_Reports"),
        (("non-conformance", "non conformance", "ncr"), "Quality_Reports"),
        (("request for information", "rfi"), "RFIs"),
        (("calculation", "design calculation", "engineering calc"), "Calculations"),
        (("correspondence", "letter", "email"), "Correspondence"),
        (("permit", "approval", "consent"), "Permits_and_Approvals"),
        (("schedule", "programme", "program"), "Schedules"),
        (("drawing", "floor plan", "site plan", "elevation", "section", "plan"), "Drawings"),
        (("report", "assessment", "survey"), "Reports"),
    )

    def organize(
        self,
        intelligence: DocumentIntelligenceResult,
        project_name: str,
        original_filename: str,
    ) -> OrganizationResult:
        safe_project_name = self._normalize_name(project_name)
        evidence_text = self._build_evidence_text(intelligence, original_filename)

        discipline, discipline_source = self._get_discipline(intelligence, evidence_text)
        document_type, type_source = self._get_document_type(intelligence, evidence_text)

        # Do not misrepresent missing evidence as a confident classification.
        needs_review = discipline == "General" or document_type == "Needs_Review"
        if document_type == "Needs_Review":
            document_type = "Needs_Review"

        target_directory = self._build_directory(
            safe_project_name,
            discipline,
            document_type,
        )
        target_filename = self._build_filename(
            intelligence,
            original_filename,
            document_type,
        )
        target_path = f"{target_directory}/{target_filename}"

        if needs_review:
            organization_category = "Needs Review"
        elif discipline == "General":
            organization_category = document_type.replace("_", " ")
        else:
            organization_category = (
                f"{discipline.replace('_', ' ')} / "
                f"{document_type.replace('_', ' ')}"
            )

        reason_parts = []
        if type_source:
            reason_parts.append(f"document type inferred from {type_source}")
        else:
            reason_parts.append("document type could not be reliably inferred")
        if discipline_source:
            reason_parts.append(f"discipline inferred from {discipline_source}")
        else:
            reason_parts.append("discipline was unavailable; General folder used")
        if needs_review:
            reason_parts.append("manual review recommended")

        return OrganizationResult(
            organization_category=organization_category,
            target_directory=target_directory,
            target_filename=target_filename,
            target_path=target_path,
            status="review_required" if needs_review else "success",
            reason="; ".join(reason_parts) + ".",
        )

    @staticmethod
    def _get(value: Any, key: str, default=None):
        if value is None:
            return default
        if isinstance(value, dict):
            return value.get(key, default)
        return getattr(value, key, default)

    @classmethod
    def _nested(cls, value: Any, *keys: str, default=None):
        current = value
        for key in keys:
            current = cls._get(current, key, None)
            if current is None:
                return default
        return current

    @classmethod
    def _build_evidence_text(cls, intelligence: Any, filename: str) -> str:
        values = [filename]
        classification = cls._get(intelligence, "classification")
        metadata = cls._get(intelligence, "metadata")
        drawing = cls._get(metadata, "drawing")

        for value in (
            cls._get(classification, "document_type"),
            cls._get(classification, "category"),
            cls._get(classification, "name"),
            cls._get(drawing, "discipline"),
            cls._get(drawing, "drawing_title"),
            cls._get(drawing, "drawing_number"),
            cls._get(intelligence, "summary"),
        ):
            if value:
                values.append(str(value))

        keywords = cls._get(intelligence, "keywords", []) or []
        if isinstance(keywords, str):
            values.append(keywords)
        else:
            values.extend(str(item) for item in keywords if item)

        return " | ".join(values).lower()

    @classmethod
    def _get_discipline(cls, intelligence: Any, evidence_text: str):
        drawing = cls._nested(intelligence, "metadata", "drawing")
        explicit = cls._get(drawing, "discipline")
        if explicit:
            match = cls._match_phrase(str(explicit), cls.DISCIPLINE_RULES)
            if match:
                return match, "drawing metadata"

        # Only infer from textual evidence when a known discipline phrase occurs.
        match = cls._match_phrase(evidence_text, cls.DISCIPLINE_RULES)
        if match:
            return match, "document text or filename"
        return "General", None

    @classmethod
    def _get_document_type(cls, intelligence: Any, evidence_text: str):
        classification = cls._get(intelligence, "classification")
        explicit_values = [
            cls._get(classification, "document_type"),
            cls._get(classification, "category"),
            cls._get(classification, "name"),
        ]
        explicit_text = " | ".join(str(v) for v in explicit_values if v).lower()

        # Prefer structured classification before broad filename/summary clues.
        match = cls._match_type(explicit_text)
        if match:
            return match, "document classification"

        match = cls._match_type(evidence_text)
        if match:
            return match, "document text or filename"
        return "Needs_Review", None

    @classmethod
    def _match_type(cls, text: str) -> Optional[str]:
        if not text:
            return None
        normalized = f" {cls._normalize_text(text)} "
        for phrases, folder in cls.DOCUMENT_TYPE_RULES:
            for phrase in sorted(phrases, key=len, reverse=True):
                candidate = f" {cls._normalize_text(phrase)} "
                if candidate in normalized:
                    return folder
        return None

    @classmethod
    def _match_phrase(cls, text: str, rules) -> Optional[str]:
        normalized = f" {cls._normalize_text(text)} "
        for phrase, folder in sorted(rules, key=lambda item: len(item[0]), reverse=True):
            if f" {cls._normalize_text(phrase)} " in normalized:
                return folder
        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        value = str(value or "").lower().replace("_", " ").replace("-", " ")
        return re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).strip()

    @staticmethod
    def _build_directory(project_name: str, discipline: str, document_type: str) -> str:
        return "/".join((project_name, discipline, document_type))

    def _build_filename(
        self,
        intelligence: DocumentIntelligenceResult,
        original_filename: str,
        document_type: str,
    ) -> str:
        source = Path(original_filename or "document")
        extension = source.suffix.lower()
        drawing = self._nested(intelligence, "metadata", "drawing")

        if document_type == "Drawings":
            parts = []
            for key in ("drawing_number", "drawing_title", "revision"):
                value = self._get(drawing, key)
                if value:
                    normalized = self._normalize_name(str(value))
                    if normalized != "Unknown":
                        parts.append(normalized)
            if parts:
                return self._limit_filename("_".join(parts) + extension)

        classification = self._get(intelligence, "classification")
        document_name = self._get(classification, "name")
        stem = self._normalize_name(str(document_name)) if document_name else self._normalize_name(source.stem)
        if stem == "Unknown":
            stem = "document"
        return self._limit_filename(stem + extension)

    @staticmethod
    def _limit_filename(value: str, max_length: int = 180) -> str:
        path = Path(value)
        suffix = path.suffix
        stem = path.stem[: max(1, max_length - len(suffix))]
        return f"{stem}{suffix}"

    @staticmethod
    def _normalize_name(value: Optional[str]) -> str:
        if not value:
            return "Unknown"
        value = str(value).strip()
        # Keep letters/numbers/underscores/hyphens/dots; remove path separators.
        value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE)
        value = re.sub(r"_+", "_", value).strip("._ ")
        if not value or value in {".", ".."}:
            return "Unknown"
        # Avoid Windows device names when files may be moved cross-platform.
        if value.split(".")[0].upper() in {
            "CON", "PRN", "AUX", "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }:
            value = f"_{value}"
        return value[:120]
