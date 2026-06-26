from __future__ import annotations

import importlib.util
import json
from pathlib import Path

FOUNDATION = Path("C:/Users/maasa/.codex/foundation")
SCRIPT = FOUNDATION / "offline_canaries.py"
REGISTRY = FOUNDATION / "offline_canary_registry.json"


def _load_offline_canaries():
    spec = importlib.util.spec_from_file_location("offline_canaries", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_offline_canary_registry_is_provider_free_and_valid() -> None:
    offline_canaries = _load_offline_canaries()

    assert offline_canaries.validate_offline_canary_registry(REGISTRY) == []


def test_offline_canaries_cover_headroom_pallium_and_ocr() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_id = {item["canary_id"]: item for item in data["canaries"]}

    assert set(by_id) == {
        "headroom_library_only_context_compression",
        "pallium_read_only_repo_intelligence",
        "research_x_fake_ocr_fixture",
    }
    assert by_id["headroom_library_only_context_compression"]["status"] == (
        "deferred_needs_source_review"
    )
    assert by_id["pallium_read_only_repo_intelligence"]["status"] == "blocked_reference_only"
    assert by_id["research_x_fake_ocr_fixture"]["status"] == "local_fixture_passed"
    assert by_id["research_x_fake_ocr_fixture"]["fixture_refs"] == [
        {
            "path": "C:/Users/maasa/research_x/examples/ocr_fixture_manifest.json",
            "sha256": "11eb46305e861b4a4af379a393f7ea87df5a7ef70db4403f856bc4c6d38dce52",
        }
    ]

    for canary in by_id.values():
        assert canary["not_evidence"] is True
        assert all(value is False for value in canary["actions"].values())


def test_offline_canary_validation_rejects_install_or_provider_actions(tmp_path: Path) -> None:
    offline_canaries = _load_offline_canaries()
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "policy": {
                    "install": False,
                    "network": False,
                    "provider_call": False,
                    "hook": False,
                    "mcp": False,
                    "plugin_enable": False,
                    "connector_enable": False,
                    "auto_write": False,
                    "not_evidence": True,
                },
                "canaries": [
                    {
                        "canary_id": "bad_provider_canary",
                        "source": "https://example.test/provider",
                        "owner_plane": "codex_foundation",
                        "status": "local_fixture_passed",
                        "decision": "bad",
                        "not_evidence": True,
                        "actions": {
                            "install": False,
                            "network": False,
                            "provider_call": True,
                            "hook": False,
                            "mcp": False,
                            "plugin_enable": False,
                            "connector_enable": False,
                            "auto_write": False,
                        },
                        "fixture_refs": [],
                        "blockers": [],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    errors = offline_canaries.validate_offline_canary_registry(bad)

    assert "bad_provider_canary: actions.provider_call must be false" in errors
    assert "bad_provider_canary: local_fixture_passed requires fixture_refs" in errors


def test_offline_canary_validation_rejects_direct_research_x_ocr_hashes(
    tmp_path: Path,
) -> None:
    offline_canaries = _load_offline_canaries()
    bad = tmp_path / "bad-ocr.json"
    bad.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "policy": {
                    "install": False,
                    "network": False,
                    "provider_call": False,
                    "hook": False,
                    "mcp": False,
                    "plugin_enable": False,
                    "connector_enable": False,
                    "auto_write": False,
                    "not_evidence": True,
                },
                "canaries": [
                    {
                        "canary_id": "research_x_fake_ocr_fixture",
                        "source": "C:/Users/maasa/research_x/src/research_x/memory/ocr.py",
                        "owner_plane": "research_x",
                        "status": "local_fixture_passed",
                        "decision": "bad direct hash",
                        "not_evidence": True,
                        "actions": {
                            "install": False,
                            "network": False,
                            "provider_call": False,
                            "hook": False,
                            "mcp": False,
                            "plugin_enable": False,
                            "connector_enable": False,
                            "auto_write": False,
                        },
                        "fixture_refs": [
                            {
                                "path": "C:/Users/maasa/research_x/src/research_x/memory/ocr.py"
                            }
                        ],
                        "blockers": [],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    errors = offline_canaries.validate_offline_canary_registry(bad)

    assert any("must reference the research_x OCR manifest" in error for error in errors)
