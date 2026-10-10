from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_index: int = Field(ge=0)
    page_number: Optional[int] = Field(default=None, ge=1)
    text: str = Field(min_length=1)


class EmbeddedChunk(DocumentChunk):
    vector: List[float] = Field(min_length=1)
