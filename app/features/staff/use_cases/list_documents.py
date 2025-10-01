"""List staff documents use case."""

from typing import List

from app.core.errors import NotFoundError
from app.features.staff.domain import StaffDocument
from app.features.staff.ports import IStaffRepository, IStaffDocumentRepository


class ListDocumentsUseCase:
    """List documents for a staff member."""

    def __init__(
        self,
        staff_repository: IStaffRepository,
        document_repository: IStaffDocumentRepository,
    ):
        self._staff_repository = staff_repository
        self._document_repository = document_repository

    async def execute(
        self,
        staff_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StaffDocument]:
        """
        List staff documents.

        Args:
            staff_id: Staff member ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[StaffDocument]: List of documents

        Raises:
            NotFoundError: If staff member not found
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise NotFoundError(f"Staff member not found: {staff_id}")

        # Get documents
        documents = await self._document_repository.list_by_staff(
            staff_id=staff_id,
            skip=skip,
            limit=limit,
        )

        return documents
