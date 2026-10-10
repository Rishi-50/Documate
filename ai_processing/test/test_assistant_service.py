from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ai_processing.schemas.retrieval_schema import (
    RetrievalResult,
    RetrievedChunk,
)
from ai_processing.services.assistant_service import AssistantService
from documents.models import Document
from projects.models import Project


class FakeRetrievalService:
    def __init__(self, result):
        self.result = result
        self.project_id = None
        self.question = None

    def retrieve(self, project_id, question):
        self.project_id = project_id
        self.question = question
        return self.result


class FakeAssistantEngine:
    def __init__(self):
        self.received_chunks = None

    def answer(self, project_name, question, chunks):
        self.received_chunks = chunks
        return "The drawing lists a 40 MPa concrete strength. [S1]"


class AssistantServiceTests(TestCase):
    def test_answer_uses_project_retrieval_and_returns_citable_sources(self):
        project = Project.objects.create(name="North Tower", client_name="Client")
        retrieved = RetrievedChunk(
            chunk_id=7,
            document_id=12,
            filename="structural.pdf",
            page_number=4,
            text="Concrete strength: 40 MPa.",
            similarity=0.91,
        )
        retrieval = FakeRetrievalService(RetrievalResult(chunks=[retrieved]))
        engine = FakeAssistantEngine()

        response = AssistantService(
            retrieval_service=retrieval,
            engine=engine,
        ).answer_question(project, "What is the concrete strength?")

        self.assertEqual(retrieval.project_id, project.id)
        self.assertEqual(retrieval.question, "What is the concrete strength?")
        self.assertEqual(engine.received_chunks, [retrieved])
        self.assertEqual(
            response.sources[0].model_dump(),
            {
                "source_id": "S1",
                "document_id": 12,
                "filename": "structural.pdf",
                "page_number": 4,
                "url": reverse("document_detail", kwargs={"document_id": 12}),
                "similarity": 0.91,
            },
        )

    def test_does_not_call_model_when_no_processed_document_matches(self):
        project = Project.objects.create(name="Empty Project", client_name="Client")

        class UnusedAssistantEngine:
            def answer(self, **kwargs):
                raise AssertionError("No excerpts should be sent to the model.")

        response = AssistantService(
            retrieval_service=FakeRetrievalService(RetrievalResult()),
            engine=UnusedAssistantEngine(),
        ).answer_question(project, "What is in the documents?")

        self.assertIn("couldn't find any processed documents", response.answer)
        self.assertEqual(response.sources, [])

    def test_project_question_endpoint_returns_grounded_response(self):
        project = Project.objects.create(name="North Tower", client_name="Client")
        response = SimpleNamespace(
            model_dump=lambda mode: {
                "answer": "The drawing lists 40 MPa. [S1]",
                "sources": [],
            }
        )

        with patch("projects.views.AssistantService") as assistant_class:
            assistant_class.return_value.answer_question.return_value = response
            result = self.client.post(
                reverse("project_assistant", kwargs={"project_id": project.id}),
                {"question": "What is the concrete strength?"},
            )

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["answer"], "The drawing lists 40 MPa. [S1]")
        assistant_class.return_value.answer_question.assert_called_once()

    def test_project_question_endpoint_rejects_empty_question(self):
        project = Project.objects.create(name="North Tower", client_name="Client")
        result = self.client.post(
            reverse("project_assistant", kwargs={"project_id": project.id}),
            {"question": "   "},
        )

        self.assertEqual(result.status_code, 400)
        self.assertEqual(
            result.json()["error"],
            "Please enter a question before sending.",
        )

    def test_project_question_endpoint_rejects_questions_over_limit(self):
        project = Project.objects.create(name="North Tower", client_name="Client")
        result = self.client.post(
            reverse("project_assistant", kwargs={"project_id": project.id}),
            {"question": "a" * 2001},
        )

        self.assertEqual(result.status_code, 400)
        self.assertEqual(
            result.json()["error"],
            "Keep your question to 2000 characters or fewer.",
        )

    def test_project_page_renders_assistant_form_for_selected_project(self):
        project = Project.objects.create(name="North Tower", client_name="Client")

        result = self.client.get(
            reverse("project_detail", kwargs={"project_id": project.id})
        )

        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Ask your project documents")
        self.assertContains(
            result,
            reverse("project_assistant", kwargs={"project_id": project.id}),
        )

    def test_dashboard_and_document_detail_render(self):
        project = Project.objects.create(name="North Tower", client_name="Client")
        document = Document.objects.create(
            project=project,
            filename="structural-plan.pdf",
            file="uploads/structural-plan.pdf",
        )
        document.intelligence.processing_status = "SUCCESS"
        document.intelligence.document_type = "Structural drawing"
        document.intelligence.ocr_text = "Concrete strength: 40 MPa."
        document.intelligence.extracted_metadata = {
            "summary": "Structural plan for the north tower.",
            "keywords": ["concrete", "structure"],
            "classification": {"category": "Drawing"},
        }
        document.intelligence.save(
            update_fields=[
                "processing_status",
                "document_type",
                "ocr_text",
                "extracted_metadata",
            ]
        )

        dashboard = self.client.get(reverse("home"))
        detail = self.client.get(
            reverse("document_detail", kwargs={"document_id": document.id})
        )

        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Your projects")
        self.assertContains(dashboard, "North Tower")
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Structural plan for the north tower.")
        self.assertContains(detail, "Concrete strength: 40 MPa.")
