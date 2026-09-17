from ai_processing.services.intelligence_service import IntelligenceService

TEST_DOCUMENTS = [
    {
        "name": "Architectural Drawing",
        "ocr_text": """
        PROJECT: RIVERFRONT RESIDENCE
        PROJECT NO: RF-2026-001
        CLIENT: ABC DEVELOPERS
        CONSULTANT: XYZ ARCHITECTS
        ADDRESS: 24 PARK ROAD, PUNE

        A-101
        GROUND FLOOR PLAN
        ARCHITECTURAL
        REVISION: B
        STATUS: ISSUED FOR CONSTRUCTION
        SHEET 01 OF 12
        """,
    },
    {
        "name": "Specification",
        "ocr_text": """
        RIVERFRONT RESIDENCE
        INTERNAL FINISHES SPECIFICATION

        Project Number: RF-2026-001
        Client: ABC DEVELOPERS

        SECTION 09
        INTERNAL FINISHES

        This specification describes the materials,
        finishes, installation requirements and quality
        standards for internal building finishes.
        """,
    },
    {
        "name": "Report",
        "ocr_text": """
        RIVERFRONT RESIDENCE
        ACOUSTIC REPORT

        Project Number: RF-2026-001
        Prepared for: ABC DEVELOPERS
        Consultant: SOUND CONSULTANTS

        This report provides acoustic assessment results
        and recommendations for the proposed development.
        """,
    },
    {
        "name": "Schedule",
        "ocr_text": """
        RIVERFRONT RESIDENCE

        HARDWARE SCHEDULE

        Door No.    Hardware Set    Description
        D-001       HW-01            Entrance Door
        D-002       HW-02            Internal Door
        D-003       HW-03            Fire Door

        Project Number: RF-2026-001
        """,
    },
    {
        "name": "Scope of Works",
        "ocr_text": """
        RIVERFRONT RESIDENCE

        SCOPE OF WORKS

        Project Number: RF-2026-001

        The contractor shall provide all labour,
        materials, equipment and supervision required
        to complete the works described in this document.

        The scope includes site preparation,
        construction, finishes and handover.
        """,
    },
    {
        "name": "Incomplete OCR",
        "ocr_text": """
        RIVERFRONT RESIDENCE
        RF-2026-001

        FLOOR PLAN
        A-203

        REV B
        """,
    },
]


def run_tests():
    service = IntelligenceService()

    print("\n" + "=" * 70)
    print("DOCUMENT INTELLIGENCE MULTI-DOCUMENT TEST")
    print("=" * 70)

    passed = 0

    for index, test_document in enumerate(TEST_DOCUMENTS, start=1):
        print("\n" + "-" * 70)
        print(f"TEST {index}: {test_document['name']}")
        print("-" * 70)

        try:
            result = service.engine.process(ocr_text=test_document["ocr_text"])

            print("\nClassification:")
            print(f"  Document Type : {result.classification.document_type}")
            print(f"  Category      : {result.classification.category}")
            print(f"  Name          : {result.classification.name}")
            print(f"  Confidence    : {result.classification.confidence}")

            print("\nProject:")
            print(f"  Name          : {result.metadata.project.project_name}")
            print(f"  Number        : {result.metadata.project.project_number}")
            print(f"  Client        : {result.metadata.project.client}")
            print(f"  Consultant    : {result.metadata.project.consultant}")

            if result.metadata.drawing:
                print("\nDrawing:")
                print(f"  Title         : {result.metadata.drawing.drawing_title}")
                print(f"  Number        : {result.metadata.drawing.drawing_number}")
                print(f"  Revision      : {result.metadata.drawing.revision}")
                print(f"  Status        : {result.metadata.drawing.status}")
                print(f"  Sheet         : {result.metadata.drawing.sheet_number}")
                print(f"  Discipline    : {result.metadata.drawing.discipline}")

            print("\nKeywords:")
            print(f"  {result.keywords}")

            print("\nSummary:")
            print(f"  {result.summary}")

            print("\nOverall Confidence:")
            print(f"  {result.confidence}")

            # Basic structural validation
            assert result.classification is not None
            assert result.metadata is not None
            assert 0.0 <= result.confidence <= 1.0
            assert isinstance(result.keywords, list)

            print("\n✅ TEST PASSED")
            passed += 1

        except Exception as exc:
            print(f"\n❌ TEST FAILED")
            print(f"Error: {exc}")

    print("\n" + "=" * 70)
    print(f"RESULT: {passed}/{len(TEST_DOCUMENTS)} tests passed")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
