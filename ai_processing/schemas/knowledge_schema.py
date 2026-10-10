from typing import List, Optional

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    """
    Searchable representation of a processed project document.

    This schema combines document identity, document intelligence,
    and organization metadata. OCR content is represented separately
    through KnowledgeChunk objects.
    """

    document_id: int
    project_id: int

    filename: str

    # Document Intelligence metadata
    document_type: Optional[str] = None
    category: Optional[str] = None
    document_name: Optional[str] = None

    # Drawing information
    drawing_number: Optional[str] = None
    drawing_title: Optional[str] = None
    revision: Optional[str] = None
    status: Optional[str] = None

    # Intelligence context
    keywords: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

    # Organization context
    organization_path: Optional[str] = None


class KnowledgeChunk(BaseModel):
    """
    A searchable chunk of OCR/document content.

    Each chunk remains linked to both its source document and project
    so retrieval can remain project-scoped and source references can
    be generated later.
    """

    chunk_id: str

    document_id: int
    project_id: int
    page_number: Optional[int] = None

    text: str = Field(min_length=1)
