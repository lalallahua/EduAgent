import asyncio
from io import BytesIO

from minio import Minio

from services.knowledge_service.app.core.config import (
    settings,
)


class ObjectStorage:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=settings.minio_secure,
        )

        self.bucket = settings.minio_bucket

    async def ensure_bucket(self) -> None:
        def _ensure():
            if not self.client.bucket_exists(
                self.bucket
            ):
                self.client.make_bucket(
                    self.bucket
                )

        await asyncio.to_thread(_ensure)

    async def put_bytes(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        await self.ensure_bucket()

        def _put():
            self.client.put_object(
                self.bucket,
                key,
                BytesIO(data),
                length=len(data),
                content_type=content_type,
            )

        await asyncio.to_thread(_put)

    async def get_bytes(
        self,
        *,
        key: str,
    ) -> bytes:
        def _get():
            response = self.client.get_object(
                self.bucket,
                key,
            )

            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        return await asyncio.to_thread(_get)

    async def delete(
        self,
        *,
        key: str,
    ) -> None:
        await asyncio.to_thread(
            self.client.remove_object,
            self.bucket,
            key,
        )


object_storage = ObjectStorage()
