from pathlib import Path

from ai_processing.engines.ocr_engine import PaddleOCREngine
from ai_processing.services.ocr_service import OCRService

class MockFile:
    def __init__(self, path):
        self.path = str(path)


class MockDocument:
    def __init__(self, path):
        self.id = 1
        self.file = MockFile(path)


def main():

    sample_file = Path(__file__).parent / "sample.pdf"

    document = MockDocument(sample_file)

    service = OCRService(
        engine=PaddleOCREngine()
    )

    result = service.run(
        document=document,
        intelligence=None,
    )

    print("=" * 80)
    print("STATUS :", result.status)
    print("MESSAGE:", result.message)
    print("=" * 80)

    ocr = result.payload["ocr_result"]

    print("Pages:", ocr.page_count)
    print("Confidence:", round(ocr.average_confidence, 3))
    print()

    print("Extracted Text")
    print("-" * 80)
    print(ocr.full_text)

    print("-" * 80)

    for page in ocr.pages:

        print(
            f"Page {page.page_number}: "
            f"{len(page.words)} words"
        )


if __name__ == "__main__":
    main()