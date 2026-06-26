from __future__ import annotations

from codex_pipeline.foundation import (
    FOUNDATION_ID,
    FOUNDATION_MANIFEST,
    foundation_manifest_summary,
    validate_foundation_manifest,
)


def test_foundation_manifest_exists_and_validates() -> None:
    assert FOUNDATION_MANIFEST.exists()
    assert validate_foundation_manifest() == []

    summary = foundation_manifest_summary()

    assert summary["id"] == FOUNDATION_ID
    assert summary["sha256"]
