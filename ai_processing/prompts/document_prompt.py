"""
Prompt used by the Document Intelligence component.

The prompt is responsible for instructing the LLM to extract
structured information from OCR text.
"""


DOCUMENT_INTELLIGENCE_SYSTEM_PROMPT = """
You are a document intelligence system for construction and engineering
documents.

Your task is to analyze OCR-extracted text from a document and identify
useful structured information.

The document may be a construction drawing, plan, report, specification,
schedule, contract, or another project-related document.

Extract only information that is supported by the provided OCR text.

Do not invent, infer, or hallucinate values that are not reasonably
supported by the document.

If a field cannot be identified, return null for that field.

Your output must follow the provided structured schema exactly.

Focus on:

1. Document classification
   - document type
   - category
   - document name/title

2. Project information
   - project name
   - project number
   - address
   - client
   - consultant

3. Drawing information when applicable
   - drawing title
   - drawing number
   - revision
   - status
   - sheet number
   - discipline

4. Important keywords

5. A concise summary of what the document represents.

Confidence scores must reflect how strongly the OCR text supports
the extracted information.

Do not treat OCR text as perfectly reliable. OCR may contain spelling,
spacing, character, or formatting errors.
"""


DOCUMENT_INTELLIGENCE_USER_PROMPT = """
Analyze the following OCR-extracted document text.

Return structured information according to the DocumentIntelligenceResult
schema.

OCR TEXT
========
{ocr_text}
========

Extraction rules:

- Extract information directly supported by the OCR text.
- Do not invent missing information.
- Use null when a field cannot be identified.
- If the document is not a drawing, drawing-specific fields should remain
  null.
- Preserve identifiers such as drawing numbers, project numbers, and
  revision values as accurately as possible.
- Keep the summary concise.
- Return useful keywords that represent the document's content.
"""


def build_document_intelligence_prompt(ocr_text: str) -> str:
    """
    Build the user prompt containing the OCR text.

    Args:
        ocr_text:
            Full OCR text extracted from the document.

    Returns:
        Formatted prompt for the intelligence engine.
    """

    return DOCUMENT_INTELLIGENCE_USER_PROMPT.format(
        ocr_text=ocr_text
    )