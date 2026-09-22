from types import SimpleNamespace

from ai_processing.engines.intelligence_engine import (
    IntelligenceEngine,
)
from ai_processing.services.intelligence_service import (
    IntelligenceService,
)


def main():

    # Simulated OCR output.
    # This represents the text that would have been produced
    # by the already-tested OCR component.
    ocr_text = """
    PROJECT: RIVERSIDE RESIDENTIAL DEVELOPMENT

    PROJECT NO: RD-2026-014

    CLIENT: ABC DEVELOPMENTS LTD.

    CONSULTANT: XYZ ARCHITECTS

    DRAWING TITLE: GROUND FLOOR PLAN

    DRAWING NO: A-101

    REVISION: REV 03

    STATUS: FOR CONSTRUCTION

    SHEET: 1 OF 12

    DISCIPLINE: ARCHITECTURAL

    SCALE: 1:100

    GENERAL NOTES:
    All dimensions are in millimetres unless otherwise noted.
    Refer to structural drawings for structural information.
    """

    # Mock objects so that Django/database are not required.
    document = SimpleNamespace(
        id=1
    )

    intelligence = SimpleNamespace(
        ocr_text=ocr_text
    )

    # Use the real IntelligenceEngine.
    engine = IntelligenceEngine()

    service = IntelligenceService(
        engine=engine
    )

    result = service.run(
        document=document,
        intelligence=intelligence,
    )

    print("=" * 80)
    print("INTELLIGENCE SERVICE TEST")
    print("=" * 80)

    print("\nStatus")
    print("-" * 80)

    print(result.status)

    print("\nMessage")
    print("-" * 80)

    print(result.message)

    if result.status.value == "SUCCESS":

        intelligence_result = result.payload[
            "intelligence_result"
        ]

        print("\nClassification")
        print("-" * 80)

        print(
            "Type:",
            intelligence_result.classification.document_type
        )

        print(
            "Category:",
            intelligence_result.classification.category
        )

        print(
            "Name:",
            intelligence_result.classification.name
        )

        print("\nProject")
        print("-" * 80)

        print(
            "Project:",
            intelligence_result.metadata.project.project_name
        )

        print(
            "Project Number:",
            intelligence_result.metadata.project.project_number
        )

        print(
            "Client:",
            intelligence_result.metadata.project.client
        )

        print(
            "Consultant:",
            intelligence_result.metadata.project.consultant
        )

        print("\nDrawing")
        print("-" * 80)

        drawing = intelligence_result.metadata.drawing

        if drawing:

            print(
                "Title:",
                drawing.drawing_title
            )

            print(
                "Number:",
                drawing.drawing_number
            )

            print(
                "Revision:",
                drawing.revision
            )

            print(
                "Status:",
                drawing.status
            )

            print(
                "Sheet:",
                drawing.sheet_number
            )

            print(
                "Discipline:",
                drawing.discipline
            )

        print("\nKeywords")
        print("-" * 80)

        print(
            ", ".join(
                intelligence_result.keywords
            )
        )

        print("\nSummary")
        print("-" * 80)

        print(
            intelligence_result.summary
        )

        print("\nOverall Confidence")
        print("-" * 80)

        print(
            intelligence_result.confidence
        )

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()