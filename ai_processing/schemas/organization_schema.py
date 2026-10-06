from typing import Optional

from pydantic import BaseModel, Field


class OrganizationResult(BaseModel):
    """
    Represents the organization decision for a document.

    This schema does not perform any filesystem operation.
    It only describes where the document should go and
    what it should be called.
    """

    organization_category: str = Field(
        ...,
        description="High-level organization category for the document.",
    )

    target_directory: str = Field(
        ...,
        description="Relative directory where the document should be organized.",
    )

    target_filename: str = Field(
        ...,
        description="Standardized filename for the document.",
    )

    target_path: str = Field(
        ...,
        description="Complete relative target path for the document.",
    )

    status: str = Field(
        default="success",
        description="Organization decision status.",
    )

    reason: Optional[str] = Field(
        default=None,
        description="Explanation for why the document was organized this way.",
    )
