from typing import List, Optional

from pydantic import BaseModel, Field


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AssistantSource(BaseModel):
    source_id: str
    document_id: int
    filename: str
    page_number: Optional[int] = None
    url: str
    similarity: float


class AssistantResponse(BaseModel):
    answer: str
    sources: List[AssistantSource] = Field(default_factory=list)
