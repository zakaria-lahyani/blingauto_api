"""Verify staff document use case."""

from app.core.errors import NotFoundError
from app.features.staff.domain import StaffDocument
from app.features.staff.ports import IStaffDocumentRepository


class VerifyDocumentUseCase:
    """Verify staff document (manager/admin function)."""

    def __init__(self, document_repository: IStaffDocumentRepository):
        self._document_repository = document_repository

    async def execute(self, document_id: str, verified_by_user_id: str) -> StaffDocument:
        """
        Verify staff document.

        Args:
            document_id: Document ID
            verified_by_user_id: ID of user verifying the document

        Returns:
            StaffDocument: Updated document

        Raises:
            NotFoundError: If document not found
        """
        # Get document
        document = await self._document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError(f"Document not found: {document_id}")

        # Mark as verified
        document.verify(verified_by_user_id)

        return await self._document_repository.update(document)
