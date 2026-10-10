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
        self.root_directory = Path(root_directory).resolve()

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

        relative_directory = Path(organization_result.target_directory)
        if (
            not organization_result.target_directory
            or relative_directory.is_absolute()
            or ".." in relative_directory.parts
        ):
            raise ValueError("Organization directory must stay inside its root.")

        target_directory = self.root_directory / relative_directory
        if not target_directory.resolve().is_relative_to(self.root_directory):
            raise ValueError("Organization directory must stay inside its root.")

        target_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        target_directory = target_directory.resolve()
        if not target_directory.is_relative_to(self.root_directory):
            raise ValueError("Organization directory must stay inside its root.")

        filename = organization_result.target_filename
        if (
            not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
        ):
            raise ValueError("Organization filename must be a single filename.")

        target_path = target_directory / filename
        source_path = source_path.resolve()

        if source_path.parent == target_directory:
            return source_path

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
