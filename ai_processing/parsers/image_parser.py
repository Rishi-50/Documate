from pathlib import Path

from PIL import Image


class ImageParser:
    """
    Loads an image file into a PIL Image.
    """

    @classmethod
    def parse(cls, image_path: str | Path) -> Image.Image:
        """
        Load an image file.

        Args:
            image_path:
                Path to the image.

        Returns:
            PIL Image.
        """

        image_path = Path(image_path)

        return Image.open(image_path).convert("RGB")