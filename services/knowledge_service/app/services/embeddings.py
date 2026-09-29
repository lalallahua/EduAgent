import hashlib
import math
import re
from abc import ABC, abstractmethod

import httpx

from services.knowledge_service.app.core.config import (
    settings,
)


class EmbeddingProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        raise NotImplementedError


class DevHashEmbeddingProvider(
    EmbeddingProvider
):
    name = "dev_hash"
    model = "hash-bow-v1"

    def __init__(
        self,
        dimension: int,
    ) -> None:
        self.dimension = dimension

    async def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [
            self._embed_one(text)
            for text in texts
        ]

    def _embed_one(
        self,
        text: str,
    ) -> list[float]:
        vector = [
            0.0
            for _ in range(
                self.dimension
            )
        ]

        tokens = re.findall(
            r"[\w]+",
            text.lower(),
            flags=re.UNICODE,
        )

        for token in tokens:
            digest = hashlib.sha256(
                token.encode("utf-8")
            ).digest()

            bucket = (
                int.from_bytes(
                    digest[:8],
                    "big",
                )
                % self.dimension
            )

            sign = (
                1.0
                if digest[8] % 2 == 0
                else -1.0
            )

            vector[bucket] += sign

        norm = math.sqrt(
            sum(
                value * value
                for value in vector
            )
        )

        if norm > 0:
            vector = [
                value / norm
                for value in vector
            ]

        return vector


class OpenAICompatibleEmbeddingProvider(
    EmbeddingProvider
):
    name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
    ) -> None:
        if not base_url:
            raise ValueError(
                "EMBEDDING_BASE_URL "
                "is required"
            )

        if not api_key:
            raise ValueError(
                "EMBEDDING_API_KEY "
                "is required"
            )

        if not model:
            raise ValueError(
                "EMBEDDING_MODEL "
                "is required"
            )

        self.base_url = (
            base_url.rstrip("/")
        )

        self.api_key = api_key
        self.model = model

    async def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        batch_size = (
            settings.embedding_batch_size
        )

        all_vectors: list[
            list[float]
        ] = []

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:

            for start in range(
                0,
                len(texts),
                batch_size,
            ):
                batch = texts[
                    start:
                    start + batch_size
                ]

                response = (
                    await client.post(
                        (
                            f"{self.base_url}"
                            "/embeddings"
                        ),
                        headers={
                            "Authorization":
                                (
                                    "Bearer "
                                    f"{self.api_key}"
                                ),
                            "Content-Type":
                                "application/json",
                        },
                        json={
                            "model":
                                self.model,
                            "input":
                                batch,
                        },
                    )
                )

                if response.is_error:
                    raise RuntimeError(
                        "Embedding API failed: "
                        f"status="
                        f"{response.status_code}, "
                        f"batch_start="
                        f"{start}, "
                        f"batch_size="
                        f"{len(batch)}, "
                        f"body="
                        f"{response.text[:2000]}"
                    )

                body = response.json()

                ordered = sorted(
                    body["data"],
                    key=lambda item:
                        item["index"],
                )

                vectors = [
                    item["embedding"]
                    for item in ordered
                ]

                if (
                    len(vectors)
                    != len(batch)
                ):
                    raise RuntimeError(
                        "Embedding response "
                        "count mismatch: "
                        f"expected="
                        f"{len(batch)}, "
                        f"actual="
                        f"{len(vectors)}"
                    )

                all_vectors.extend(
                    vectors
                )

        return all_vectors

def get_embedding_provider(
) -> EmbeddingProvider:
    if (
        settings.embedding_provider
        == "dev_hash"
    ):
        return DevHashEmbeddingProvider(
            settings.embedding_dimension
        )

    if (
        settings.embedding_provider
        == "openai_compatible"
    ):
        return (
            OpenAICompatibleEmbeddingProvider(
                base_url=(
                    settings.embedding_base_url
                ),
                api_key=(
                    settings.embedding_api_key
                ),
                model=(
                    settings.embedding_model
                ),
            )
        )

    raise ValueError(
        "Unknown EMBEDDING_PROVIDER: "
        f"{settings.embedding_provider}"
    )
