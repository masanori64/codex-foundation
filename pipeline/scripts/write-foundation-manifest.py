from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = PIPELINE_ROOT / "engine"
sys.path.insert(0, str(ENGINE_ROOT))

from codex_pipeline.foundation import write_foundation_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--known-project", action="append", default=[])
    args = parser.parse_args()
    manifest = write_foundation_manifest(known_projects=args.known_project)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
