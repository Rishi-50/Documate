import cv2
import paddleocr

image_path = "data\Drawing Detail Sample Markup_page-0001.jpg"

print("PaddleOCR version:", paddleocr.__version__)

img = cv2.imread(image_path)

if img is None:
    raise ValueError(f"Could not read image: {image_path}")

print("Image shape:", img.shape)

from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="en")

result = ocr.ocr(img, cls=True)

print("OCR result:", repr(result))
print("Result type:", type(result))
