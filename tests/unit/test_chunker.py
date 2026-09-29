from services.knowledge_service.app.services.chunker import (
    chunk_units,
)
from services.knowledge_service.app.services.parsers import (
    ParsedUnit,
)


def test_chunker_creates_overlap():
    text = "a" * 2500

    chunks = chunk_units(
        [
            ParsedUnit(
                text=text,
                page_no=1,
            )
        ],
        max_chars=1200,
        overlap_chars=200,
    )

    assert len(chunks) == 3

    assert (
        chunks[0].page_no
        == 1
    )

    assert (
        chunks[0].chunk_index
        == 0
    )


def test_chunk_checksum_is_stable():
    units = [
        ParsedUnit(
            text="computer vision"
        )
    ]

    a = chunk_units(
        units,
        max_chars=1200,
        overlap_chars=200,
    )

    b = chunk_units(
        units,
        max_chars=1200,
        overlap_chars=200,
    )

    assert (
        a[0].checksum_sha256
        == b[0].checksum_sha256
    )
