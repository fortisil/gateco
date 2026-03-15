"""Mock S3 client for testing file uploads."""

from typing import Optional
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import secrets


class MockS3PresignedUrl:
    """Mock presigned URL response."""

    def __init__(
        self,
        upload_url: str = None,
        file_url: str = None,
        expires_in: int = 900,
        fields: dict = None,
    ):
        self.upload_id = secrets.token_hex(16)
        self.upload_url = upload_url or f"https://s3.amazonaws.com/gateco-uploads/temp/{self.upload_id}"
        self.file_url = file_url or f"https://gateco-uploads.s3.amazonaws.com/{self.upload_id}"
        self.expires_in = expires_in
        self.fields = fields or {
            "key": f"temp/{self.upload_id}/${filename}",
            "x-amz-algorithm": "AWS4-HMAC-SHA256",
            "x-amz-credential": "mock-credential",
            "x-amz-date": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "x-amz-signature": secrets.token_hex(32),
            "policy": "mock-policy-base64",
        }


class MockS3Object:
    """Mock S3 object."""

    def __init__(
        self,
        key: str,
        content: bytes = b"",
        content_type: str = "application/octet-stream",
        size: int = None,
    ):
        self.key = key
        self.content = content
        self.content_type = content_type
        self.size = size or len(content)
        self.last_modified = datetime.now(timezone.utc)
        self.etag = f'"{secrets.token_hex(16)}"'


class MockS3Client:
    """
    Mock S3 client for testing.

    Simulates S3 operations without actual AWS calls.
    """

    def __init__(
        self,
        bucket_name: str = "gateco-uploads",
        region: str = "us-east-1",
    ):
        self.bucket_name = bucket_name
        self.region = region
        self._objects: dict[str, MockS3Object] = {}
        self._presigned_urls: dict[str, dict] = {}

    def generate_presigned_url(
        self,
        client_method: str,
        params: dict,
        expires_in: int = 900,
    ) -> str:
        """Generate a mock presigned URL."""
        key = params.get("Key", secrets.token_hex(16))
        url_id = secrets.token_hex(8)

        url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}?X-Amz-Signature={url_id}"

        self._presigned_urls[url_id] = {
            "key": key,
            "method": client_method,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        }

        return url

    def generate_presigned_post(
        self,
        bucket: str,
        key: str,
        fields: dict = None,
        conditions: list = None,
        expires_in: int = 900,
    ) -> dict:
        """Generate a mock presigned POST for uploads."""
        url_id = secrets.token_hex(8)

        return {
            "url": f"https://{bucket}.s3.{self.region}.amazonaws.com/",
            "fields": {
                "key": key,
                "x-amz-algorithm": "AWS4-HMAC-SHA256",
                "x-amz-credential": f"mock-access-key/{datetime.now(timezone.utc).strftime('%Y%m%d')}/{self.region}/s3/aws4_request",
                "x-amz-date": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                "x-amz-signature": secrets.token_hex(32),
                "policy": "mock-policy-base64",
                **(fields or {}),
            },
        }

    def put_object(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        **kwargs,
    ) -> dict:
        """Mock putting an object to S3."""
        obj = MockS3Object(
            key=key,
            content=body,
            content_type=content_type,
            size=len(body),
        )
        self._objects[key] = obj

        return {
            "ETag": obj.etag,
            "VersionId": secrets.token_hex(16),
        }

    def get_object(self, bucket: str, key: str) -> dict:
        """Mock getting an object from S3."""
        if key not in self._objects:
            raise Exception("NoSuchKey")

        obj = self._objects[key]
        return {
            "Body": MagicMock(read=MagicMock(return_value=obj.content)),
            "ContentType": obj.content_type,
            "ContentLength": obj.size,
            "ETag": obj.etag,
            "LastModified": obj.last_modified,
        }

    def delete_object(self, bucket: str, key: str) -> dict:
        """Mock deleting an object from S3."""
        if key in self._objects:
            del self._objects[key]

        return {
            "DeleteMarker": True,
            "VersionId": secrets.token_hex(16),
        }

    def head_object(self, bucket: str, key: str) -> dict:
        """Mock getting object metadata."""
        if key not in self._objects:
            raise Exception("NoSuchKey")

        obj = self._objects[key]
        return {
            "ContentType": obj.content_type,
            "ContentLength": obj.size,
            "ETag": obj.etag,
            "LastModified": obj.last_modified,
        }

    def list_objects_v2(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> dict:
        """Mock listing objects in S3."""
        matching = [
            {"Key": key, "Size": obj.size, "LastModified": obj.last_modified}
            for key, obj in self._objects.items()
            if key.startswith(prefix)
        ][:max_keys]

        return {
            "Contents": matching,
            "KeyCount": len(matching),
            "IsTruncated": len(self._objects) > max_keys,
        }

    def copy_object(
        self,
        copy_source: dict,
        bucket: str,
        key: str,
    ) -> dict:
        """Mock copying an object within S3."""
        source_key = copy_source["Key"]
        if source_key not in self._objects:
            raise Exception("NoSuchKey")

        source_obj = self._objects[source_key]
        new_obj = MockS3Object(
            key=key,
            content=source_obj.content,
            content_type=source_obj.content_type,
        )
        self._objects[key] = new_obj

        return {
            "CopyObjectResult": {
                "ETag": new_obj.etag,
                "LastModified": new_obj.last_modified,
            }
        }


def create_s3_mock(bucket_name: str = "gateco-uploads") -> MockS3Client:
    """
    Create a mock S3 client.

    Args:
        bucket_name: Name of the S3 bucket

    Returns:
        MockS3Client: Mock S3 client instance
    """
    return MockS3Client(bucket_name=bucket_name)


def create_presigned_upload_response(
    filename: str = "test-file.pdf",
    content_type: str = "application/pdf",
    organization_id: str = "org_123",
) -> dict:
    """
    Create a mock presigned upload response.

    Args:
        filename: Name of the file to upload
        content_type: MIME type of the file
        organization_id: Organization ID for the upload path

    Returns:
        dict: Mock presigned upload response
    """
    upload_id = secrets.token_hex(16)
    key = f"organizations/{organization_id}/resources/{upload_id}/{filename}"

    return {
        "upload_url": f"https://gateco-uploads.s3.amazonaws.com/{key}",
        "file_url": f"https://cdn.gateco.io/{key}",
        "expires_in": 900,
        "fields": {
            "key": key,
            "Content-Type": content_type,
            "x-amz-algorithm": "AWS4-HMAC-SHA256",
            "x-amz-credential": "mock-credential",
            "x-amz-date": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "x-amz-signature": secrets.token_hex(32),
            "policy": "mock-policy-base64",
        },
    }
