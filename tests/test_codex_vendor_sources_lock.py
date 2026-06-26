from __future__ import annotations

import json
import tomllib
from pathlib import Path

CODEX_VENDOR_LOCK = Path("C:/Users/maasa/.codex/foundation/vendor_sources.lock.md")
CODEX_FOUNDATION_REGISTRY = Path(
    "C:/Users/maasa/.codex/foundation/codex-foundation-registry.toml"
)
CODEX_CONFIG = Path("C:/Users/maasa/.codex/config.toml")
GOAL_SETTER_MANIFEST = Path(
    "C:/Users/maasa/.codex/plugins/cache/personal/goal-setter/0.9.3/.codex-plugin/plugin.json"
)


def _codex_vendor_lock_text() -> str:
    return CODEX_VENDOR_LOCK.read_text(encoding="utf-8")


def test_ian_xiaohei_is_creative_optional_not_evidence_or_enabled() -> None:
    vendor_lock = _codex_vendor_lock_text()

    assert "ian-xiaohei-illustrations" in vendor_lock
    assert "686575741a61e2c0be5e4c6d3615ebf6217dd322" in vendor_lock
    assert "Use only for explicit visual-planning requests" in vendor_lock
    assert "generated images are not evidence" in vendor_lock
    assert "v1.0.0" in vendor_lock


def test_superpowers_is_pinned_but_disabled_until_full_review() -> None:
    vendor_lock = _codex_vendor_lock_text()

    assert "superpowers" in vendor_lock
    assert "f2cbfbefebbfef77321e4c9abc9e949826bea9d7" in vendor_lock
    assert "Disabled; review then optional" in vendor_lock
    assert "no full source/script/hook audit yet" in vendor_lock


def test_agentmemory_is_pinned_but_disabled_until_hook_and_retention_review() -> None:
    vendor_lock = _codex_vendor_lock_text()

    assert "agentmemory" in vendor_lock
    assert "25158519d5d68b9060a97ba5bdcccc3e1aba6d79" in vendor_lock
    assert "source-review-required" in vendor_lock
    assert "hook/MCP/auto-capture" in vendor_lock
    assert "no install now" in vendor_lock


def test_codex_skill_catalogs_stay_disabled_or_reference_only() -> None:
    vendor_lock = _codex_vendor_lock_text()

    assert "superclaude-framework" in vendor_lock
    assert "minimax-skills" in vendor_lock
    assert "ponytail" in vendor_lock
    assert "Catalog/source reference only" in vendor_lock
    assert "Reference only" in vendor_lock or "Disabled" in vendor_lock


def test_headroom_has_registry_and_source_lock_boundary() -> None:
    vendor_lock = _codex_vendor_lock_text()
    registry = CODEX_FOUNDATION_REGISTRY.read_text(encoding="utf-8")

    assert "headroom" in vendor_lock
    assert "https://github.com/chopratejas/headroom" in vendor_lock
    assert 'name = "headroom"' in registry
    assert "Optional context-compression adapter candidate" in registry


def test_goal_setter_is_installed_plugin_with_source_lock_boundary() -> None:
    vendor_lock = _codex_vendor_lock_text()
    registry = CODEX_FOUNDATION_REGISTRY.read_text(encoding="utf-8")
    config = CODEX_CONFIG.read_text(encoding="utf-8")
    manifest = json.loads(GOAL_SETTER_MANIFEST.read_text(encoding="utf-8"))

    assert "goal-setter" in vendor_lock
    assert "4f37792ca6ee0a3729c861d28485a52e05571b0b" in vendor_lock
    assert "plugin `v0.9.3`" in vendor_lock
    assert "do not also install the standalone Skill copy" in vendor_lock
    assert 'name = "goal-setter"' in registry
    assert "source_locked_installed_personal_plugin" in registry
    assert '[plugins."goal-setter@personal"]' in config
    assert "enabled = true" in config
    assert manifest["name"] == "goal-setter"
    assert manifest["version"] == "0.9.3"
    assert manifest["skills"] == "./skills/"


def test_codex_foundation_registry_has_no_source_lock_placeholders() -> None:
    registry = CODEX_FOUNDATION_REGISTRY.read_text(encoding="utf-8")

    assert "source-lock-needed:" not in registry
    assert "source_lock_required" not in registry
    assert "manual_gate_for_install_hook_mcp_plugin_connector = true" in registry


def test_self_improvement_and_memory_candidates_are_source_locked_not_enabled() -> None:
    vendor_lock = _codex_vendor_lock_text()

    for candidate in (
        "evoskill",
        "gepa",
        "textgrad",
        "trace2skill",
        "skillgrad",
        "skillsmith-paper",
        "mem0",
        "automem",
        "memoryoss",
        "memories-sh",
        "codex-memory",
    ):
        assert candidate in vendor_lock
    assert "No clone/install" in vendor_lock
    assert "Provider/cloud-memory candidate" in vendor_lock
    assert "No MCP/server/provider setup" in vendor_lock


def test_pallium_registry_metadata_is_machine_readable() -> None:
    registry = tomllib.loads(CODEX_FOUNDATION_REGISTRY.read_text(encoding="utf-8"))
    candidates = {item["name"]: item for item in registry["candidates"]}
    pallium = candidates["pallium"]

    assert pallium["canonical_url"] == "https://github.com/tszaks/pallium"
    assert pallium["legacy_url"] == "https://github.com/tszaks/codex-memory"
    assert pallium["redirect_chain"] == [
        "https://github.com/tszaks/codex-memory",
        "https://github.com/tszaks/pallium",
    ]
    assert pallium["source_kind"] == "repo_intelligence"
    assert pallium["review_status"] == "blocked_reference_only"
    assert pallium["license"] == "unverified"
    assert pallium["retrieved_at"] == "2026-06-26"
    assert pallium["surface_alias"] == "codex-memory"
    assert pallium["enabled"] is False
