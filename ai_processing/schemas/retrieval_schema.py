from typing import List, Optional

from pydantic import BaseModel, Field


class RetrievalCandidate(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    page_number: Optional[int] = None
    text: str
    vector: List[float] = Field(min_length=1)


class RetrievedChunk(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    page_number: Optional[int] = None
    text: str
    similarity: float


class RetrievalResult(BaseModel):
    chunks: List[RetrievedChunk] = Field(default_factory=list)
