import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Creates text embeddings using the configured Gemini embedding model.
    """

    def __init__(
        self,
        client=None,
        model: str = "gemini-embedding-001",
    ):
        if client is None:
            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set.")

            client = genai.Client(api_key=api_key)

        self.client = client
        self.model = model

    def embed(
        self,
        text: str,
        task_type: str,
    ) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Text to embed cannot be empty.")

        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type),
        )

        if not response.embeddings or not response.embeddings[0].values:
            logger.error("Embedding model returned an empty vector.")
            raise ValueError("Embedding model returned an empty vector.")

        return [float(value) for value in response.embeddings[0].values]
