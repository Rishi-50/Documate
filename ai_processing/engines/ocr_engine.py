from statistics import mean
from time import perf_counter
from typing import List

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image

from ai_processing.schemas.ocr_schema import (
    OCRPage,
    OCRResult,
    OCRWord,
)

import logging

logging.getLogger("ppocr").setLevel(logging.WARNING)


class PaddleOCREngine:
    """
    OCR engine implementation using PaddleOCR.
    """

    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
        )

    def process(
        self,
        images: List[Image.Image],
    ) -> OCRResult:
        """
        Perform OCR on a list of images.

        Args:
            images:
                List of PIL images.

        Returns:
            OCRResult
        """

        start_time = perf_counter()

        pages = []

        page_confidences = []

        full_text = []

        for page_number, image in enumerate(images, start=1):

            result = self.ocr.ocr(
                np.array(image)
            )

            words = []

            page_lines = []

            confidences = []

            if result and result[0]:

                for line in result[0]:

                    bounding_box = [
                        [int(x), int(y)]
                        for x, y in line[0]
                    ]

                    text = line[1][0]

                    confidence = float(line[1][1])

                    words.append(
                        OCRWord(
                            text=text,
                            confidence=confidence,
                            bounding_box=bounding_box,
                        )
                    )

                    page_lines.append(text)

                    confidences.append(confidence)

            page_text = "\n".join(page_lines)

            page_confidence = (
                mean(confidences)
                if confidences
                else 0.0
            )

            pages.append(
                OCRPage(
                    page_number=page_number,
                    text=page_text,
                    confidence=page_confidence,
                    words=words,
                )
            )

            full_text.append(page_text)

            page_confidences.append(page_confidence)

        processing_time = perf_counter() - start_time

        average_confidence = (
            mean(page_confidences)
            if page_confidences
            else 0.0
        )

        return OCRResult(
            page_count=len(pages),
            processing_time=processing_time,
            average_confidence=average_confidence,
            full_text="\n\n".join(full_text),
            pages=pages,
        )