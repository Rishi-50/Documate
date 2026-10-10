from django.test import TestCase

from ai_processing.models import DocumentEmbedding
from ai_processing.schemas.base import ProcessingStatus
from ai_processing.services.embedding_service import EmbeddingService
from documents.models import Document
from projects.models import Project


class FakeEmbeddingEngine:
    def embed(self, text, task_type):
        return [float(len(text)), 1.0]


class EmbeddingServiceTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="North Tower",
            client_name="Example Client",
        )
        self.document = Document.objects.create(
            project=self.project,
            filename="plan.pdf",
            file="uploads/plan.pdf",
        )
        self.intelligence = self.document.intelligence
        self.intelligence.ocr_text = "Ground floor plan and structural notes."
        self.intelligence.ocr_pages = {
            "pages": [
                {"page_number": 1, "text": "Ground floor plan."},
                {"page_number": 2, "text": "Structural notes."},
            ]
        }
        self.intelligence.save(update_fields=["ocr_text", "ocr_pages"])
        self.service = EmbeddingService(engine=FakeEmbeddingEngine())

    def test_run_persists_page_chunks_and_vectors(self):
        result = self.service.run(self.document, self.intelligence)

        self.assertEqual(result.status, ProcessingStatus.SUCCESS)
        self.assertEqual(result.payload["chunk_count"], 2)
        self.assertEqual(
            list(
                DocumentEmbedding.objects.filter(document=self.document).values_list(
                    "page_number", "text", "vector"
                )
            ),
            [
                (1, "Ground floor plan.", [18.0, 1.0]),
                (2, "Structural notes.", [17.0, 1.0]),
            ],
        )
        self.intelligence.refresh_from_db()
        self.assertTrue(self.intelligence.embeddings_created)

    def test_failed_reindex_keeps_existing_embeddings(self):
        self.service.run(self.document, self.intelligence)
        original_ids = list(
            DocumentEmbedding.objects.filter(document=self.document).values_list(
                "id", flat=True
            )
        )

        class FailingEngine:
            def embed(self, text, task_type):
                raise RuntimeError("embedding service unavailable")

        result = EmbeddingService(engine=FailingEngine()).run(
            self.document,
            self.intelligence,
        )

        self.assertEqual(result.status, ProcessingStatus.FAILED)
        self.assertEqual(
            list(
                DocumentEmbedding.objects.filter(document=self.document).values_list(
                    "id", flat=True
                )
            ),
            original_ids,
        )

    def test_run_fails_when_ocr_text_is_empty(self):
        self.intelligence.ocr_text = ""

        result = self.service.run(self.document, self.intelligence)

        self.assertEqual(result.status, ProcessingStatus.FAILED)
        self.assertFalse(
            DocumentEmbedding.objects.filter(document=self.document).exists()
        )

    def test_long_pages_are_split_on_word_boundaries_with_overlap(self):
        words = [f"token{index}" for index in range(250)]
        self.intelligence.ocr_pages = {
            "pages": [{"page_number": 1, "text": " ".join(words)}]
        }

        chunks = self.service._create_chunks(self.intelligence)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(
            all(len(chunk.text) <= self.service.MAX_CHUNK_LENGTH for chunk in chunks)
        )
        self.assertTrue(
            all(word in words for chunk in chunks for word in chunk.text.split())
        )
        self.assertTrue(set(chunks[0].text.split()) & set(chunks[1].text.split()))
