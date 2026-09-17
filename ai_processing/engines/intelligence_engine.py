import json
import logging
import os

from google import genai
from google.genai import types

from ai_processing.prompts.document_prompt import (
    DOCUMENT_INTELLIGENCE_SYSTEM_PROMPT,
    build_document_intelligence_prompt,
)
from ai_processing.schemas.intelligence_schema import (
    DocumentIntelligenceResult,
)


from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class IntelligenceEngine:
    """
    LLM-based document intelligence engine.

    Responsible only for:
    - Sending OCR text to the LLM.
    - Requesting structured output.
    - Validating the returned structure.
    """

    def __init__(self, model: str = "gemini-3.6-flash"):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = model

    def process(
        self,
        ocr_text: str,
    ) -> DocumentIntelligenceResult:
        """
        Analyze OCR text and return structured document intelligence.

        Args:
            ocr_text:
                Full OCR text extracted from a document.

        Returns:
            DocumentIntelligenceResult
        """

        if not ocr_text or not ocr_text.strip():
            raise ValueError(
                "OCR text cannot be empty."
            )

        prompt = build_document_intelligence_prompt(
            ocr_text
        )

        logger.info(
            "Running document intelligence using %s",
            self.model,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=DOCUMENT_INTELLIGENCE_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=DocumentIntelligenceResult,
                temperature=0,
            ),
        )

        if not response.text:
            raise ValueError(
                "Intelligence engine returned an empty response."
            )

        try:
            data = json.loads(response.text)

        except json.JSONDecodeError as exc:
            logger.exception(
                "Failed to parse intelligence engine response."
            )

            raise ValueError(
                "Intelligence engine returned invalid JSON."
            ) from exc

        try:
            result = DocumentIntelligenceResult.model_validate(
                data
            )

        except Exception as exc:
            logger.exception(
                "Failed to validate intelligence result."
            )

            raise ValueError(
                "Intelligence engine returned invalid structured data."
            ) from exc

        logger.info(
            "Document intelligence completed successfully."
        )

        return result