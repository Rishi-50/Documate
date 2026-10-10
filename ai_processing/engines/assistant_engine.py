import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ai_processing.prompts.assistant_prompt import (
    ASSISTANT_SYSTEM_PROMPT,
    build_assistant_prompt,
)
from ai_processing.schemas.retrieval_schema import RetrievedChunk

load_dotenv()

logger = logging.getLogger(__name__)


class AssistantEngine:
    """
    Generates answers grounded in retrieved project document excerpts.
    """

    def __init__(
        self,
        client=None,
        model: str = "gemini-3.6-flash",
    ):
        if client is None:
            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set.")

            client = genai.Client(api_key=api_key)

        self.client = client
        self.model = model

    def answer(
        self,
        project_name: str,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> str:
        if not question.strip():
            raise ValueError("Question cannot be empty.")
        if not chunks:
            raise ValueError("At least one document excerpt is required.")

        response = self.client.models.generate_content(
            model=self.model,
            contents=build_assistant_prompt(
                project_name=project_name,
                question=question,
                chunks=chunks,
            ),
            config=types.GenerateContentConfig(
                system_instruction=ASSISTANT_SYSTEM_PROMPT,
                temperature=0,
            ),
        )

        if not response.text or not response.text.strip():
            logger.error("Assistant model returned an empty answer.")
            raise ValueError("Assistant model returned an empty answer.")

        return response.text.strip()
