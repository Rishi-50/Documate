import logging
from statistics import mean
from time import perf_counter
from typing import Any, List

import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

from ai_processing.schemas.ocr_schema import (
    OCRPage,
    OCRResult,
    OCRWord,
)

logger = logging.getLogger(__name__)
logging.getLogger("ppocr").setLevel(logging.WARNING)


class PaddleOCREngine:
    """PaddleOCR engine with defensive result parsing."""

    def __init__(self):
        # Keep initialization compatible with the legacy API.
        # PaddleOCR 3.x may require different constructor arguments.
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
        )

        # PaddleOCR 3.x exposes predict(); legacy 2.x uses ocr().
        self._use_predict = callable(getattr(self.ocr, "predict", None))

    @staticmethod
    def _to_numpy(image: Any) -> np.ndarray:
        """Convert a supported image into a valid RGB NumPy array."""

        if isinstance(image, Image.Image):
            image = image.convert("RGB")
            array = np.asarray(image)

        elif isinstance(image, np.ndarray):
            array = image

            if array.size == 0:
                raise ValueError("Input image array is empty.")

            if array.ndim == 2:
                pass  # Grayscale image.
            elif array.ndim == 3:
                if array.shape[2] == 4:
                    # Remove alpha channel.
                    array = array[:, :, :3]
                elif array.shape[2] != 3:
                    raise ValueError(f"Unsupported channel count: {array.shape[2]}")
            else:
                raise ValueError(f"Unsupported image dimensions: {array.shape}")
        else:
            raise TypeError(f"Unsupported image type: {type(image).__name__}")

        if array.size == 0:
            raise ValueError("Input image is empty.")

        if array.dtype != np.uint8:
            array = np.clip(array, 0, 255).astype(np.uint8)

        return np.ascontiguousarray(array)

    @staticmethod
    def _get_field(data: Any, key: str, default=None):
        """Read a field from a dictionary or result object."""

        if isinstance(data, dict):
            return data.get(key, default)

        try:
            return data[key]
        except (KeyError, IndexError, TypeError, AttributeError):
            return getattr(data, key, default)

    @classmethod
    def _unwrap_result(cls, result: Any) -> Any:
        """Unwrap PaddleOCR 3.x result objects when necessary."""

        if result is None:
            return None

        json_data = getattr(result, "json", None)

        if callable(json_data):
            try:
                json_data = json_data()
            except Exception:
                json_data = None

        if isinstance(json_data, dict):
            result = json_data

        nested = cls._get_field(result, "res")

        if nested is not None:
            return nested

        return result

    @staticmethod
    def _parse_box(box: Any):
        """Convert a detected polygon to integer [x, y] points."""

        if box is None:
            return None

        try:
            points = np.asarray(box, dtype=float)

            if points.size < 4 or points.size % 2 != 0:
                return None

            points = points.reshape(-1, 2)

            if not np.isfinite(points).all():
                return None

            return [[int(round(x)), int(round(y))] for x, y in points]
        except (TypeError, ValueError, OverflowError):
            return None

    @classmethod
    def _parse_legacy(cls, result: Any) -> List[dict]:
        """Parse the PaddleOCR 2.x line format."""

        if result is None:
            return []

        # Legacy output usually has one outer list per image.
        if isinstance(result, (list, tuple)):
            if not result:
                return []

            first = result[0]

            if first is None:
                return []

            if not isinstance(first, (list, tuple)):
                return []

            # Empty first page means no detections.
            lines = first
        else:
            return []

        words = []

        for line in lines:
            if line is None or not isinstance(line, (list, tuple)):
                continue

            if len(line) < 2:
                continue

            box = cls._parse_box(line[0])
            recognition = line[1]

            if box is None:
                continue

            if not isinstance(recognition, (list, tuple)):
                continue

            if len(recognition) < 2:
                continue

            text = recognition[0]

            if text is None:
                continue

            try:
                confidence = float(recognition[1])
            except (TypeError, ValueError, OverflowError):
                continue

            if not np.isfinite(confidence):
                continue

            words.append(
                {
                    "text": str(text),
                    "confidence": max(0.0, min(1.0, confidence)),
                    "bounding_box": box,
                }
            )

        return words

    @classmethod
    def _parse_modern(cls, result: Any) -> List[dict]:
        """Parse PaddleOCR 3.x prediction results."""

        data = cls._unwrap_result(result)

        if data is None:
            return []

        texts = cls._get_field(data, "rec_texts")
        scores = cls._get_field(data, "rec_scores")
        boxes = cls._get_field(data, "rec_polys")

        if boxes is None:
            boxes = cls._get_field(data, "dt_polys")

        if boxes is None:
            boxes = cls._get_field(data, "rec_boxes")

        if texts is None:
            return []

        texts = list(texts)
        scores = list(scores) if scores is not None else []
        boxes = list(boxes) if boxes is not None else []

        words = []

        for index, text in enumerate(texts):
            if text is None:
                continue

            if index >= len(boxes):
                continue

            box = cls._parse_box(boxes[index])

            if box is None:
                continue

            try:
                confidence = float(scores[index]) if index < len(scores) else 0.0
            except (TypeError, ValueError, OverflowError):
                confidence = 0.0

            if not np.isfinite(confidence):
                confidence = 0.0

            words.append(
                {
                    "text": str(text),
                    "confidence": max(0.0, min(1.0, confidence)),
                    "bounding_box": box,
                }
            )

        return words

    def _recognize(self, image: np.ndarray) -> List[dict]:
        """Run inference and normalize its output."""

        if self._use_predict:
            result = self.ocr.predict(image)

            if result is None:
                return []

            # predict() generally returns one result object per image.
            if isinstance(result, (list, tuple)):
                if not result:
                    return []
                result = result[0]

            return self._parse_modern(result)

        result = self.ocr.ocr(image, cls=True)
        return self._parse_legacy(result)

    def process(self, images: List[Image.Image]) -> OCRResult:
        """Run OCR on images and return structured page results."""

        start_time = perf_counter()

        if images is None:
            raise ValueError("OCR received images=None.")

        pages = []
        full_text = []
        page_confidences = []

        for page_number, image in enumerate(images, start=1):
            try:
                array = self._to_numpy(image)
                words_data = self._recognize(array)

            except Exception:
                logger.exception(
                    "OCR inference failed | page=%d | image_type=%s",
                    page_number,
                    type(image).__name__,
                )
                raise

            words = [
                OCRWord(
                    text=item["text"],
                    confidence=item["confidence"],
                    bounding_box=item["bounding_box"],
                )
                for item in words_data
            ]

            page_text = "\n".join(word.text for word in words)

            confidences = [word.confidence for word in words]

            page_confidence = mean(confidences) if confidences else 0.0

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

            logger.info(
                "OCR page completed | page=%d | words=%d",
                page_number,
                len(words),
            )

        processing_time = perf_counter() - start_time

        average_confidence = mean(page_confidences) if page_confidences else 0.0

        return OCRResult(
            page_count=len(pages),
            processing_time=processing_time,
            average_confidence=average_confidence,
            full_text="\n\n".join(full_text),
            pages=pages,
        )
