from __future__ import annotations

import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))

from codex_pipeline.foundation import (  # noqa: E402
    validate_foundation_manifest,
    write_foundation_manifest,
)

if validate_foundation_manifest():
    write_foundation_manifest(known_projects=["C:/Users/maasa/research_x"], audit=False)
