"""Staff service interfaces."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class IFileStorageService(ABC):
    """Interface for file storage service (documents, photos, etc.)."""

    @abstractmethod
    async def upload_file(
        self,
        file_content: BinaryIO,
        file_name: str,
        content_type: str,
        folder: str = "staff_documents",
    ) -> str:
        """
        Upload a file to storage.

        Args:
            file_content: File content as binary stream
            file_name: Original file name
            content_type: MIME type
            folder: Storage folder/prefix

        Returns:
            str: File path/URL in storage
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            bool: True if deleted successfully
        """
        pass

    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """
        Get public URL for a file.

        Args:
            file_path: Path to file in storage

        Returns:
            str: Public URL
        """
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            file_path: Path to file in storage

        Returns:
            bool: True if file exists
        """
        pass
