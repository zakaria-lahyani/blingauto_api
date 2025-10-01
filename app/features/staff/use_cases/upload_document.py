"""Upload staff document use case."""

from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO, Optional
import uuid

from app.core.errors import NotFoundError, ValidationError
from app.features.staff.domain import StaffDocument, DocumentType
from app.features.staff.ports import (
    IStaffRepository,
    IStaffDocumentRepository,
    IFileStorageService,
)


@dataclass
class UploadDocumentRequest:
    """Request to upload staff document."""

    staff_id: str
    document_type: DocumentType
    document_name: str
    file_content: BinaryIO
    file_name: str
    content_type: str
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class UploadDocumentUseCase:
    """Upload and store staff document."""

    def __init__(
        self,
        staff_repository: IStaffRepository,
        document_repository: IStaffDocumentRepository,
        file_storage: IFileStorageService,
    ):
        self._staff_repository = staff_repository
        self._document_repository = document_repository
        self._file_storage = file_storage

    async def execute(self, request: UploadDocumentRequest) -> StaffDocument:
        """
        Upload staff document.

        Args:
            request: Upload document request

        Returns:
            StaffDocument: Created document record

        Raises:
            NotFoundError: If staff member not found
            ValidationError: If validation fails
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(request.staff_id)
        if not staff:
            raise NotFoundError(f"Staff member not found: {request.staff_id}")

        # Validate file name
        if not request.file_name or not request.file_name.strip():
            raise ValidationError("File name is required")

        # Upload file to storage
        folder = f"staff_documents/{request.staff_id}"
        file_path = await self._file_storage.upload_file(
            file_content=request.file_content,
            file_name=request.file_name,
            content_type=request.content_type,
            folder=folder,
        )

        # Create document record
        document = StaffDocument(
            id=str(uuid.uuid4()),
            staff_id=request.staff_id,
            document_type=request.document_type,
            document_name=request.document_name,
            file_path=file_path,
            uploaded_at=datetime.now(),
            expires_at=request.expires_at,
            notes=request.notes,
        )

        return await self._document_repository.create(document)
