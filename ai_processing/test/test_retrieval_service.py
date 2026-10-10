from django.test import TestCase

from ai_processing.models import DocumentEmbedding
from ai_processing.schemas.base import ProcessingStatus
from ai_processing.services.retrieval_service import RetrievalService
from documents.models import Document
from projects.models import Project


class FakeEmbeddingEngine:
    def embed(self, text, task_type):
        self.task_type = task_type
        return [1.0, 0.0]


class RetrievalServiceTests(TestCase):
    def create_document(self, project, filename, status, indexed=True):
        document = Document.objects.create(
            project=project,
            filename=filename,
            file=f"uploads/{filename}",
        )
        intelligence = document.intelligence
        intelligence.processing_status = status
        intelligence.embeddings_created = indexed
        intelligence.save(update_fields=["processing_status", "embeddings_created"])
        return document

    def test_retrieval_is_project_scoped_and_only_uses_processed_documents(self):
        project = Project.objects.create(name="Project A", client_name="Client")
        other_project = Project.objects.create(
            name="Project B",
            client_name="Client",
        )
        included = self.create_document(
            project,
            "included.pdf",
            ProcessingStatus.SUCCESS.value,
        )
        self.create_document(
            other_project,
            "other-project.pdf",
            ProcessingStatus.SUCCESS.value,
        )
        not_processed = self.create_document(
            project,
            "not-processed.pdf",
            ProcessingStatus.FAILED.value,
        )

        DocumentEmbedding.objects.create(
            document=included,
            chunk_index=0,
            page_number=3,
            text="Concrete strength is 40 MPa.",
            vector=[1.0, 0.0],
        )
        DocumentEmbedding.objects.create(
            document=Document.objects.get(filename="other-project.pdf"),
            chunk_index=0,
            text="This belongs to another project.",
            vector=[1.0, 0.0],
        )
        DocumentEmbedding.objects.create(
            document=not_processed,
            chunk_index=0,
            text="This document did not finish processing.",
            vector=[1.0, 0.0],
        )

        engine = FakeEmbeddingEngine()
        result = RetrievalService(embedding_engine=engine).retrieve(
            project_id=project.id,
            question="What is the concrete strength?",
        )

        self.assertEqual(engine.task_type, "RETRIEVAL_QUERY")
        self.assertEqual(len(result.chunks), 1)
        self.assertEqual(result.chunks[0].filename, "included.pdf")
        self.assertEqual(result.chunks[0].page_number, 3)
        self.assertAlmostEqual(result.chunks[0].similarity, 1.0)

    def test_returns_no_results_without_calling_embedding_engine(self):
        project = Project.objects.create(name="Empty", client_name="Client")

        class UnusedEmbeddingEngine:
            def embed(self, text, task_type):
                raise AssertionError("No query embedding should be generated.")

        result = RetrievalService(embedding_engine=UnusedEmbeddingEngine()).retrieve(
            project.id, "Any processed documents?"
        )

        self.assertEqual(result.chunks, [])
