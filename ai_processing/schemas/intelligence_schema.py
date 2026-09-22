from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentClassification(BaseModel):
    """
    Classification of the construction document.
    """

    document_type: Optional[str] = Field(
        default=None,
        description="High-level document type, e.g. drawing, report, specification, schedule, contract."
    )

    category: Optional[str] = Field(
        default=None,
        description="Document category."
    )

    name: Optional[str] = Field(
        default=None,
        description="Specific document name or title."
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the classification."
    )


class ProjectInformation(BaseModel):
    """
    Static project information that may appear across construction documents.
    """

    project_name: Optional[str] = None

    project_number: Optional[str] = None

    address: Optional[str] = None

    client: Optional[str] = None

    consultant: Optional[str] = None


class DrawingInformation(BaseModel):
    """
    Information specific to construction drawings/plans.
    """

    drawing_title: Optional[str] = None

    drawing_number: Optional[str] = None

    revision: Optional[str] = None

    status: Optional[str] = None

    sheet_number: Optional[str] = None

    discipline: Optional[str] = None


class DocumentMetadata(BaseModel):
    """
    Structured metadata extracted from the document.
    """

    project: ProjectInformation = Field(
        default_factory=ProjectInformation
    )

    drawing: Optional[DrawingInformation] = None


class DocumentIntelligenceResult(BaseModel):
    """
    Complete structured understanding of a construction document.

    This is the output contract of the Document Intelligence component.
    """

    classification: DocumentClassification = Field(
        default_factory=DocumentClassification
    )

    metadata: DocumentMetadata = Field(
        default_factory=DocumentMetadata
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the extracted intelligence."
    )

    keywords: List[str] = Field(
        default_factory=list,
        description="Important keywords identified in the document."
    )

    summary: Optional[str] = Field(
        default=None,
        description="Short summary of the document."
    )