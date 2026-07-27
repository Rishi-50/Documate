from typing import List, Tuple

from pydantic import BaseModel, Field


class OCRWord(BaseModel):
    """
    Represents a single OCR-detected text element.
    """

    text: str = Field(
        ...,
        description="Detected text."
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1."
    )

    bounding_box: List[List[int]] = Field(
        default_factory=list,
        description="Bounding box coordinates [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]."
    )


class OCRPage(BaseModel):
    """
    OCR result for a single page.
    """

    page_number: int = Field(
        ...,
        ge=1,
        description="1-based page number."
    )

    text: str = Field(
        default="",
        description="Complete OCR text for this page."
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average confidence of this page."
    )

    words: List[OCRWord] = Field(
        default_factory=list,
        description="List of OCR detected words."
    )


class OCRResult(BaseModel):
    """
    Complete OCR output for an entire document.
    """

    page_count: int = Field(
        default=0,
        ge=0,
        description="Total number of processed pages."
    )

    processing_time: float = Field(
        default=0.0,
        ge=0.0,
        description="Total OCR processing time in seconds."
    )

    average_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average confidence across all pages."
    )

    full_text: str = Field(
        default="",
        description="Combined OCR text from all pages."
    )

    pages: List[OCRPage] = Field(
        default_factory=list,
        description="OCR output for each page."
    )