from pathlib import Path
import shutil

from ai_processing.schemas.organization_schema import OrganizationResult


class FileOrganizer:
    """
    Handles the physical organization of a document on the filesystem.

    This class does not decide where a document belongs.
    It executes an OrganizationResult produced by OrganizationEngine.
    """

    def __init__(self, root_directory: str | Path):
        self.root_directory = Path(root_directory)

    def organize(
        self,
        source_path: str | Path,
        organization_result: OrganizationResult,
    ) -> Path:
        """
        Move a document to its target location.

        Args:
            source_path: Current location of the document.
            organization_result: Organization decision generated
                by OrganizationEngine.

        Returns:
            Final path of the organized document.
        """

        source_path = Path(source_path)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {source_path}")

        target_directory = self.root_directory / organization_result.target_directory
  
        target_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        target_path = target_directory / organization_result.target_filename
   
        target_path = self._get_available_path(target_path)

        shutil.move(
            str(source_path),
            str(target_path),
        )

        return target_path

    @staticmethod
    def _get_available_path(
        target_path: Path,
    ) -> Path:
        """
        Generate a non-conflicting path if the target filename
        already exists.

        Example:

            drawing.pdf
            drawing_1.pdf
            drawing_2.pdf
        """

        if not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix

        counter = 1

        while True:
            candidate = target_path.parent / f"{stem}_{counter}{suffix}"

            if not candidate.exists():
                return candidate

            counter += 1
