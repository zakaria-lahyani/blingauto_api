"""File storage service implementation."""

import os
import uuid
from pathlib import Path
from typing import BinaryIO
import aiofiles
import aiofiles.os

from app.features.staff.ports import IFileStorageService


class LocalFileStorageService(IFileStorageService):
    """
    Local filesystem storage implementation.

    For production, this should be replaced with S3/Azure Blob Storage.
    """

    def __init__(self, base_path: str = "uploads"):
        """
        Initialize local file storage.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_content: BinaryIO,
        file_name: str,
        content_type: str,
        folder: str = "staff_documents",
    ) -> str:
        """
        Upload a file to local storage.

        Args:
            file_content: File content as binary stream
            file_name: Original file name
            content_type: MIME type
            folder: Storage folder/prefix

        Returns:
            str: File path in storage
        """
        # Create folder if it doesn't exist
        folder_path = self.base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # Generate unique file name to avoid conflicts
        file_extension = Path(file_name).suffix
        unique_name = f"{uuid.uuid4()}{file_extension}"
        file_path = folder_path / unique_name

        # Write file
        async with aiofiles.open(file_path, "wb") as f:
            content = file_content.read()
            await f.write(content)

        # Return relative path from base_path
        return str(file_path.relative_to(self.base_path))

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            bool: True if deleted successfully
        """
        full_path = self.base_path / file_path

        try:
            if await aiofiles.os.path.exists(full_path):
                await aiofiles.os.remove(full_path)
                return True
            return False
        except Exception:
            return False

    async def get_file_url(self, file_path: str) -> str:
        """
        Get public URL for a file.

        For local storage, returns the file path.
        For cloud storage (S3), this would return a signed URL.

        Args:
            file_path: Path to file in storage

        Returns:
            str: Public URL (or path for local storage)
        """
        # For local storage, return the relative path
        # In production with S3, this would generate a signed URL
        return f"/uploads/{file_path}"

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            file_path: Path to file in storage

        Returns:
            bool: True if file exists
        """
        full_path = self.base_path / file_path
        return await aiofiles.os.path.exists(full_path)


# Future: S3 implementation example
"""
class S3FileStorageService(IFileStorageService):
    def __init__(self, bucket_name: str, aws_access_key: str, aws_secret_key: str):
        import boto3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )
        self.bucket_name = bucket_name

    async def upload_file(self, file_content, file_name, content_type, folder="staff_documents"):
        key = f"{folder}/{uuid.uuid4()}{Path(file_name).suffix}"
        self.s3_client.upload_fileobj(
            file_content,
            self.bucket_name,
            key,
            ExtraArgs={'ContentType': content_type}
        )
        return key

    async def delete_file(self, file_path: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except Exception:
            return False

    async def get_file_url(self, file_path: str) -> str:
        # Generate signed URL valid for 1 hour
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': file_path},
            ExpiresIn=3600
        )

    async def file_exists(self, file_path: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except:
            return False
"""
