from __future__ import annotations

import json

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

    manifest = json.loads(FOUNDATION_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["root"] == "."
    assert manifest["registered_in"] == "../codex-foundation-registry.toml"
