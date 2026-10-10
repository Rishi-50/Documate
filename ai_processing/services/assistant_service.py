from django.urls import reverse

from ai_processing.engines.assistant_engine import AssistantEngine
from ai_processing.schemas.assistant_schema import (
    AssistantResponse,
    AssistantSource,
)
from ai_processing.services.retrieval_service import RetrievalService


class AssistantService:
    """
    Answers questions using only retrieved documents from one project.
    """

    NO_DOCUMENTS_ANSWER = (
        "I couldn't find any processed documents for this project yet. "
        "Upload and process documents, then try again."
    )

    def __init__(self, retrieval_service=None, engine=None):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.engine = engine or AssistantEngine()

    def answer_question(self, project, question: str) -> AssistantResponse:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        retrieval = self.retrieval_service.retrieve(
            project_id=project.id,
            question=question,
        )

        if not retrieval.chunks:
            return AssistantResponse(answer=self.NO_DOCUMENTS_ANSWER)

        answer = self.engine.answer(
            project_name=project.name,
            question=question,
            chunks=retrieval.chunks,
        )
        sources = [
            AssistantSource(
                source_id=f"S{index}",
                document_id=chunk.document_id,
                filename=chunk.filename,
                page_number=chunk.page_number,
                url=reverse(
                    "document_detail",
                    kwargs={"document_id": chunk.document_id},
                ),
                similarity=chunk.similarity,
            )
            for index, chunk in enumerate(retrieval.chunks, start=1)
        ]

        return AssistantResponse(answer=answer, sources=sources)
