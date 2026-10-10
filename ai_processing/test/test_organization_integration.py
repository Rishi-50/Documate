import tempfile
from pathlib import Path

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from ai_processing.schemas.base import ProcessingStatus
from ai_processing.schemas.organization_schema import OrganizationResult
from ai_processing.services.organization_service import OrganizationService
from documents.models import Document
from projects.models import Project


class FakeOrganizationEngine:
    def __init__(self):
        self.project_name = None

    def organize(self, intelligence, project_name, original_filename):
        self.project_name = project_name
        return OrganizationResult(
            organization_category="Other",
            target_directory="Tower_Project/Unclassified/Other",
            target_filename="scope.pdf",
            target_path="Tower_Project/Unclassified/Other/scope.pdf",
        )


class OrganizationIntegrationTests(TestCase):
    def test_organized_filefield_link_stays_valid_and_reprocessing_is_idempotent(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                project = Project.objects.create(
                    name="Tower Project",
                    client_name="Construction Client",
                )
                document = Document.objects.create(
                    project=project,
                    filename="original-scope.pdf",
                    file=ContentFile(b"project scope", name="original-scope.pdf"),
                )
                intelligence = document.intelligence
                intelligence.extracted_metadata = {}
                intelligence.save(update_fields=["extracted_metadata"])
                original_path = Path(document.file.path)
                engine = FakeOrganizationEngine()
                service = OrganizationService(engine=engine)

                first_result = service.run(document, intelligence)

                document.refresh_from_db()
                organized_path = Path(document.file.path)
                self.assertEqual(first_result.status, ProcessingStatus.SUCCESS)
                self.assertEqual(engine.project_name, "Tower Project")
                self.assertTrue(organized_path.is_file())
                self.assertFalse(original_path.exists())
                self.assertEqual(
                    document.file.name,
                    "projects/Tower_Project/Unclassified/Other/scope.pdf",
                )

                second_result = service.run(document, intelligence)

                document.refresh_from_db()
                self.assertEqual(second_result.status, ProcessingStatus.SUCCESS)
                self.assertEqual(Path(document.file.path), organized_path)
                self.assertEqual(len(list(organized_path.parent.iterdir())), 1)
