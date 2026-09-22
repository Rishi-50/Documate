from ai_processing.engines.intelligence_engine import (
    IntelligenceEngine,
)


def main():

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

    engine = IntelligenceEngine()

    result = engine.process(
        ocr_text=ocr_text
    )

    print("=" * 80)
    print("DOCUMENT INTELLIGENCE TEST")
    print("=" * 80)

    print("\nClassification")
    print("-" * 80)

    print(
        "Type:",
        result.classification.document_type
    )

    print(
        "Category:",
        result.classification.category
    )

    print(
        "Name:",
        result.classification.name
    )

    print(
        "Confidence:",
        result.classification.confidence
    )

    print("\nProject Information")
    print("-" * 80)

    print(
        "Project:",
        result.metadata.project.project_name
    )

    print(
        "Project Number:",
        result.metadata.project.project_number
    )

    print(
        "Client:",
        result.metadata.project.client
    )

    print(
        "Consultant:",
        result.metadata.project.consultant
    )

    print("\nDrawing Information")
    print("-" * 80)

    if result.metadata.drawing:

        print(
            "Title:",
            result.metadata.drawing.drawing_title
        )

        print(
            "Number:",
            result.metadata.drawing.drawing_number
        )

        print(
            "Revision:",
            result.metadata.drawing.revision
        )

        print(
            "Status:",
            result.metadata.drawing.status
        )

        print(
            "Sheet:",
            result.metadata.drawing.sheet_number
        )

        print(
            "Discipline:",
            result.metadata.drawing.discipline
        )

    print("\nKeywords")
    print("-" * 80)

    print(
        ", ".join(result.keywords)
    )

    print("\nSummary")
    print("-" * 80)

    print(result.summary)

    print("\nOverall Confidence")
    print("-" * 80)

    print(result.confidence)

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()