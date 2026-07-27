from pathlib import Path
from typing import List

import fitz
from PIL import Image


class PDFParser:
    """
    Converts a PDF document into a list of PIL Images.
    """

    DEFAULT_DPI = 300

    @classmethod
    def parse(
        cls,
        pdf_path: str | Path,
        dpi: int = DEFAULT_DPI,
    ) -> List[Image.Image]:
        """
        Convert every page of a PDF into a PIL Image.

        Args:
            pdf_path:
                Path to the PDF.

            dpi:
                Rendering DPI.

        Returns:
            List of PIL Images.
        """

        pdf_path = Path(pdf_path)

        document = fitz.open(pdf_path)

        images = []

        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        for page in document:

            pix = page.get_pixmap(matrix=matrix)

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )

            images.append(image)

        document.close()

        return images