from pathlib import Path

from ai_processing.engines.ocr_engine import PaddleOCREngine
from ai_processing.services.ocr_service import OCRService
from ai_processing.services.intelligence_service import IntelligenceService
from ai_processing.services.processing_manager import ProcessingManager


class MockFile:
    def __init__(self, path):
        self.path = str(path)


class MockDocument:
    def __init__(self, path):
        self.id = 1
        self.filename = Path(path).name
        self.file = MockFile(path)


class MockIntelligence:
    def __init__(self):
        self.processing_status = "PENDING"
        self.processing_stage = "PENDING"

        self.ocr_text = ""
        self.ocr_pages = []
        self.confidence_score = 0.0

        self.document_type = ""
        self.extracted_metadata = {}
        self.last_error = ""

    def save(self, update_fields=None):
        pass


def main():
    sample_file = Path(__file__).parent / "sample.pdf"

    document = MockDocument(sample_file)
    intelligence = MockIntelligence()

    ocr_service = OCRService(engine=PaddleOCREngine())

    intelligence_service = IntelligenceService()

    manager = ProcessingManager(
        pipeline=[
            ocr_service,
            intelligence_service,
        ]
    )

    print("=" * 80)
    print("OCR → DOCUMENT INTELLIGENCE PIPELINE")
    print("=" * 80)

    result = manager.process_document(
        document=document,
        intelligence=intelligence,
    )

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)

    print("Status :", result.status)
    print("Stage  :", result.stage)
    print("Message:", result.message)

    print("\n" + "=" * 80)
    print("INTELLIGENCE RESULT")
    print("=" * 80)

    print("Document Type :", intelligence.document_type)
    print("Confidence    :", intelligence.confidence_score)

    print("\nExtracted Metadata:")
    print(intelligence.extracted_metadata)

    print("\n" + "=" * 80)
    print("PIPELINE TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
