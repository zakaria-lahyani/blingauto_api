"""Delete staff document use case."""

from app.core.errors import NotFoundError
from app.features.staff.ports import IStaffDocumentRepository, IFileStorageService


class DeleteDocumentUseCase:
    """Delete staff document."""

    def __init__(
        self,
        document_repository: IStaffDocumentRepository,
        file_storage: IFileStorageService,
    ):
        self._document_repository = document_repository
        self._file_storage = file_storage

    async def execute(self, document_id: str) -> bool:
        """
        Delete staff document.

        Args:
            document_id: Document ID

        Returns:
            bool: True if deleted successfully

        Raises:
            NotFoundError: If document not found
        """
        # Get document
        document = await self._document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError(f"Document not found: {document_id}")

        # Delete file from storage
        await self._file_storage.delete_file(document.file_path)

        # Delete document record
        return await self._document_repository.delete(document_id)
