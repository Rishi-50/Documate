from pathlib import Path

import pytest

from ai_processing.engines.organization_engine import OrganizationEngine
from ai_processing.services.file_organizer import FileOrganizer
from ai_processing.schemas.intelligence_schema import (
    DocumentClassification,
    DocumentIntelligenceResult,
    DocumentMetadata,
    DrawingInformation,
)
from ai_processing.schemas.organization_schema import (
    OrganizationResult,
)
from ai_processing.services.organization_service import (
    OrganizationService,
)

# ============================================================
# Helpers
# ============================================================


def create_drawing_intelligence(
    document_type="Architectural Drawing",
    category="Architectural",
    name="Ground Floor Plan",
    drawing_title="Ground Floor Plan",
    drawing_number="A-101",
    revision="R02",
    discipline="Architectural",
):
    return DocumentIntelligenceResult(
        classification=DocumentClassification(
            document_type=document_type,
            category=category,
            name=name,
        ),
        metadata=DocumentMetadata(
            drawing=DrawingInformation(
                drawing_title=drawing_title,
                drawing_number=drawing_number,
                revision=revision,
                discipline=discipline,
            )
        ),
    )


def create_document_intelligence(
    document_type=None,
    category=None,
    name=None,
):
    return DocumentIntelligenceResult(
        classification=DocumentClassification(
            document_type=document_type,
            category=category,
            name=name,
        ),
        metadata=DocumentMetadata(),
    )


# ============================================================
# 1. Schema
# ============================================================


def test_organization_schema():

    result = OrganizationResult(
        organization_category="Architectural Drawing",
        target_directory="ABC_Tower/Architectural/Drawings",
        target_filename="A-101_Ground_Floor_Plan_R02.pdf",
        target_path=(
            "ABC_Tower/Architectural/Drawings/" "A-101_Ground_Floor_Plan_R02.pdf"
        ),
        status="success",
        reason="Test organization result.",
    )

    assert result.organization_category == "Architectural Drawing"
    assert result.target_directory == ("ABC_Tower/Architectural/Drawings")
    assert result.target_filename == ("A-101_Ground_Floor_Plan_R02.pdf")
    assert result.status == "success"


# ============================================================
# 2. Organization Engine
# ============================================================


def test_complete_architectural_drawing():

    intelligence = create_drawing_intelligence()

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="drawing.pdf",
    )

    assert result.organization_category == ("Architectural Drawing")

    assert result.target_directory == ("ABC_Tower/Architectural/Drawings")

    assert result.target_filename == ("A-101_Ground_Floor_Plan_R02.pdf")

    assert result.target_path == (
        "ABC_Tower/Architectural/Drawings/" "A-101_Ground_Floor_Plan_R02.pdf"
    )


def test_structural_drawing():

    intelligence = create_drawing_intelligence(
        document_type="Structural Drawing",
        category="Structural",
        name="Foundation Plan",
        drawing_title="Foundation Plan",
        drawing_number="S-101",
        revision="R01",
        discipline="Structural",
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="drawing.pdf",
    )

    assert result.target_directory == ("ABC_Tower/Structural/Drawings")

    assert result.target_filename == ("S-101_Foundation_Plan_R01.pdf")


def test_electrical_drawing():

    intelligence = create_drawing_intelligence(
        document_type="Electrical Drawing",
        category="Electrical",
        name="Lighting Plan",
        drawing_title="Lighting Plan",
        drawing_number="E-201",
        revision="R03",
        discipline="Electrical",
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="lighting.pdf",
    )

    assert result.target_directory == ("ABC_Tower/Electrical/Drawings")

    assert result.target_filename == ("E-201_Lighting_Plan_R03.pdf")


def test_mechanical_drawing():

    intelligence = create_drawing_intelligence(
        document_type="Mechanical Drawing",
        category="Mechanical",
        name="HVAC Plan",
        drawing_title="HVAC Plan",
        drawing_number="M-301",
        revision="R01",
        discipline="Mechanical",
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="hvac.pdf",
    )

    assert result.target_directory == ("ABC_Tower/Mechanical/Drawings")

    assert result.target_filename == ("M-301_HVAC_Plan_R01.pdf")


# ============================================================
# 3. Missing Drawing Metadata
# ============================================================


def test_drawing_without_revision():

    intelligence = create_drawing_intelligence(
        revision=None,
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="drawing.pdf",
    )

    assert result.target_filename == ("A-101_Ground_Floor_Plan.pdf")


def test_drawing_without_number():

    intelligence = create_drawing_intelligence(
        drawing_number=None,
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="drawing.pdf",
    )

    assert result.target_filename == ("Ground_Floor_Plan_R02.pdf")


def test_drawing_without_number_and_revision():

    intelligence = create_drawing_intelligence(
        drawing_number=None,
        revision=None,
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="drawing.pdf",
    )

    assert result.target_filename == ("Ground_Floor_Plan.pdf")


# ============================================================
# 4. Non-Drawing Documents
# ============================================================


def test_report():

    intelligence = create_document_intelligence(
        document_type="Report",
        name="Structural Inspection Report",
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="report.pdf",
    )

    assert result.target_directory == ("ABC_Tower/Unclassified/Reports")

    assert result.target_filename == ("Structural_Inspection_Report.pdf")


def test_specification():

    intelligence = create_document_intelligence(
        document_type="Specification",
        name="Fire Safety Specification",
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="specification.pdf",
    )

    assert result.target_directory == ("ABC_Tower/Unclassified/Specifications")

    assert result.target_filename == ("Fire_Safety_Specification.pdf")


def test_unknown_document_type():

    intelligence = create_document_intelligence(
        document_type="Contract",
        name="Construction Contract",
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="contract.pdf",
    )

    assert result.target_directory == ("ABC_Tower/Unclassified/Other")

    assert result.target_filename == ("Construction_Contract.pdf")


# ============================================================
# 5. Completely Missing Intelligence
# ============================================================


def test_empty_intelligence():

    intelligence = DocumentIntelligenceResult()

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower",
        original_filename="unknown_document.pdf",
    )

    assert result.target_directory == ("ABC_Tower/Unclassified/Other")

    assert result.target_filename == ("unknown_document.pdf")

    assert result.status == "success"


# ============================================================
# 6. Filename Normalization
# ============================================================


def test_filename_normalization():

    intelligence = create_drawing_intelligence(
        drawing_number="A:101",
        drawing_title="Ground Floor / Main Plan",
        revision="R02",
    )

    engine = OrganizationEngine()

    result = engine.organize(
        intelligence=intelligence,
        project_name="ABC Tower Phase 1",
        original_filename="drawing.pdf",
    )

    assert result.target_filename == ("A101_Ground_Floor_Main_Plan_R02.pdf")

    assert result.target_directory == ("ABC_Tower_Phase_1/" "Architectural/Drawings")


# ============================================================
# 7. File Organizer
# ============================================================


def create_organization_result(
    filename="A-101_Ground_Floor_Plan_R02.pdf",
):
    return OrganizationResult(
        organization_category="Architectural Drawing",
        target_directory="ABC_Tower/Architectural/Drawings",
        target_filename=filename,
        target_path=("ABC_Tower/Architectural/Drawings/" f"{filename}"),
        status="success",
    )


def test_file_is_moved(tmp_path):

    source_file = tmp_path / "drawing.pdf"
    source_file.write_text("test document")

    organizer = FileOrganizer(root_directory=tmp_path / "organized")

    result = organizer.organize(
        source_path=source_file,
        organization_result=create_organization_result(),
    )

    expected = (
        tmp_path
        / "organized"
        / "ABC_Tower"
        / "Architectural"
        / "Drawings"
        / "A-101_Ground_Floor_Plan_R02.pdf"
    )

    assert result == expected
    assert result.exists()

    assert result.read_text() == "test document"

    assert not source_file.exists()


def test_directory_is_created(tmp_path):

    source_file = tmp_path / "drawing.pdf"
    source_file.write_text("test")

    organizer = FileOrganizer(root_directory=tmp_path / "organized")

    result = organizer.organize(
        source_path=source_file,
        organization_result=create_organization_result(),
    )

    assert result.parent.exists()
    assert result.exists()


def test_duplicate_file_gets_suffix(tmp_path):

    organizer = FileOrganizer(root_directory=tmp_path / "organized")

    first_source = tmp_path / "drawing1.pdf"
    first_source.write_text("first")

    first_result = organizer.organize(
        source_path=first_source,
        organization_result=create_organization_result(),
    )

    second_source = tmp_path / "drawing2.pdf"
    second_source.write_text("second")

    second_result = organizer.organize(
        source_path=second_source,
        organization_result=create_organization_result(),
    )

    assert first_result.name == ("A-101_Ground_Floor_Plan_R02.pdf")

    assert second_result.name == ("A-101_Ground_Floor_Plan_R02_1.pdf")

    assert first_result.read_text() == "first"
    assert second_result.read_text() == "second"


def test_multiple_duplicates(tmp_path):

    organizer = FileOrganizer(root_directory=tmp_path / "organized")

    for index in range(3):

        source_file = tmp_path / f"drawing_{index}.pdf"
        source_file.write_text(f"document {index}")

        organizer.organize(
            source_path=source_file,
            organization_result=create_organization_result(),
        )

    target_directory = (
        tmp_path / "organized" / "ABC_Tower" / "Architectural" / "Drawings"
    )

    filenames = {file.name for file in target_directory.iterdir()}

    assert filenames == {
        "A-101_Ground_Floor_Plan_R02.pdf",
        "A-101_Ground_Floor_Plan_R02_1.pdf",
        "A-101_Ground_Floor_Plan_R02_2.pdf",
    }


def test_missing_source_file(tmp_path):

    organizer = FileOrganizer(root_directory=tmp_path / "organized")

    missing_file = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        organizer.organize(
            source_path=missing_file,
            organization_result=create_organization_result(),
        )


# ============================================================
# 8. Organization Service
# ============================================================


class FakeDocumentFile:

    def __init__(self, path):
        self.path = str(path)


class FakeDocument:

    id = 1
    filename = "drawing.pdf"

    def __init__(self, path):
        self.file = FakeDocumentFile(path)


class FakeEngine:

    def __init__(self):
        self.called = False

    def organize(
        self,
        intelligence,
        project_name,
        original_filename,
    ):
        self.called = True

        return create_organization_result(filename="A-101.pdf")


class FakeOrganizer:

    def __init__(self):
        self.called = False

    def organize(
        self,
        source_path,
        organization_result,
    ):
        self.called = True

        return Path("/organized/ABC_Tower/" "Architectural/Drawings/A-101.pdf")


def test_service_connects_engine_and_organizer(tmp_path):

    source_file = tmp_path / "drawing.pdf"
    source_file.write_text("test")

    engine = FakeEngine()
    organizer = FakeOrganizer()

    service = OrganizationService(
        engine=engine,
        organizer=organizer,
    )

    document = FakeDocument(source_file)

    intelligence = create_drawing_intelligence()

    result = service.run(
        document=document,
        intelligence=intelligence,
        project_name="ABC Tower",
    )

    assert engine.called is True
    assert organizer.called is True

    assert result.payload["final_path"] == (
        "/organized/ABC_Tower/" "Architectural/Drawings/A-101.pdf"
    )
