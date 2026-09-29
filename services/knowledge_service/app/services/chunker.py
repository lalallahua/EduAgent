import hashlib
import re
from dataclasses import dataclass

from services.knowledge_service.app.services.parsers import (
    ParsedUnit,
)


@dataclass
class ChunkData:
    chunk_index: int
    page_no: int | None
    section: str | None
    text: str
    token_count: int
    checksum_sha256: str


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")

    return re.sub(
        r"[ \t]+",
        " ",
        text,
    ).strip()


def approximate_token_count(
    text: str,
) -> int:
    return len(
        re.findall(
            r"\S+",
            text,
        )
    )


def chunk_units(
    units: list[ParsedUnit],
    *,
    max_chars: int,
    overlap_chars: int,
) -> list[ChunkData]:
    chunks: list[ChunkData] = []

    index = 0

    for unit in units:
        text = normalize_text(
            unit.text
        )

        if not text:
            continue

        start = 0

        while start < len(text):
            end = min(
                len(text),
                start + max_chars,
            )

            piece = text[start:end].strip()

            if piece:
                checksum = hashlib.sha256(
                    piece.encode("utf-8")
                ).hexdigest()

                chunks.append(
                    ChunkData(
                        chunk_index=index,
                        page_no=unit.page_no,
                        section=unit.section,
                        text=piece,
                        token_count=(
                            approximate_token_count(
                                piece
                            )
                        ),
                        checksum_sha256=checksum,
                    )
                )

                index += 1

            if end >= len(text):
                break

            start = max(
                start + 1,
                end - overlap_chars,
            )

    return chunks
