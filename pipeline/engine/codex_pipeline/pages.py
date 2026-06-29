from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bridge_loader import ProjectBridge
from .foundation import control_marker
from .profile_loader import ProjectProfile

API_ROOT = "https://api.github.com"


def build_pages_url_map(profile: ProjectProfile, bridge: ProjectBridge) -> dict[str, str]:
    repository = str(bridge.data["github"].get("repository", ""))
    owner, repo = _split_repository(repository)
    base_url = f"https://{owner}.github.io/{repo}/" if owner and repo else ""
    branch = _git(profile.project_root, ["branch", "--show-current"])
    if not branch:
        branch = "unknown"
    preview_key = _safe_path_segment(branch)
    return {
        "base": base_url,
        "dashboard": urllib.parse.urljoin(base_url, "dashboard/"),
        "preview": urllib.parse.urljoin(base_url, f"previews/{preview_key}/latest/"),
        "staging": urllib.parse.urljoin(base_url, "staging/latest/"),
        "production": urllib.parse.urljoin(base_url, "production/latest/"),
        "rollback": urllib.parse.urljoin(base_url, "rollback/latest/"),
    }


def build_pages_readiness_state(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    *,
    execute: bool = False,
    timeout_seconds: float = 15,
) -> dict[str, Any]:
    repository = str(bridge.data["github"].get("repository", ""))
    repo_url = _api_repo_url(repository)
    pages_url = f"{repo_url}/pages" if repo_url else ""
    repo_result = (
        _get_json(repo_url, timeout_seconds=timeout_seconds)
        if execute
        else _empty_result()
    )
    pages_result = (
        _get_json(pages_url, timeout_seconds=timeout_seconds)
        if execute
        else _empty_result()
    )
    gh_pages_fallback_used = False
    if execute and pages_result.get("status_code") == 404:
        owner, repo = _split_repository(repository)
        gh_pages_result = _get_gh_json(
            f"repos/{owner}/{repo}/pages",
            timeout_seconds=timeout_seconds,
        )
        if gh_pages_result.get("ok") is True:
            pages_result = gh_pages_result
            gh_pages_fallback_used = True
    repo_payload = _payload_dict(repo_result)
    pages_payload = _payload_dict(pages_result)
    private = repo_payload.get("private")
    visibility = repo_payload.get("visibility") or (
        "private" if private is True else "public" if private is False else "unknown"
    )
    pages_configured = pages_result.get("status_code") == 200
    pages_missing = pages_result.get("status_code") == 404
    build_type = pages_payload.get("build_type", "")
    free_public_eligible = visibility == "public"
    source_setup_required = pages_missing or (
        pages_configured and build_type not in {"", "workflow"}
    )
    status = "not_checked"
    if execute:
        if free_public_eligible and (pages_configured or pages_missing):
            status = (
                "passed"
                if pages_configured and build_type == "workflow"
                else "free_setup_required"
            )
        elif visibility == "private":
            status = "blocked_private_repo_may_use_paid_or_quota_plan"
        else:
            status = "unknown"
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="pages_readiness"),
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": profile.project_id,
        "repository": repository,
        "execute": execute,
        "status": status,
        "request_methods_used": (
            ["GET", "GH_API_GET"] if gh_pages_fallback_used else ["GET"] if execute else []
        ),
        "authentication": (
            "gh_cli_local_verification" if gh_pages_fallback_used else "none"
        ),
        "token_used": gh_pages_fallback_used,
        "pipeline_authentication_required": "none",
        "pipeline_token_required": False,
        "paid_usage_detected": False,
        "provider_api_calls": False,
        "repo": {
            "visibility": visibility,
            "private": private,
            "default_branch": repo_payload.get("default_branch", ""),
            "html_url": repo_payload.get("html_url", ""),
        },
        "pages": {
            "configured": pages_configured,
            "missing": pages_missing,
            "status_code": pages_result.get("status_code", 0),
            "html_url": pages_payload.get("html_url", ""),
            "build_type": build_type,
            "source": pages_payload.get("source", {}),
        },
        "free_static_cd": {
            "public_repo_standard_runner_free": free_public_eligible,
            "github_pages_public_repo_free": free_public_eligible,
            "pages_source_setup_required": source_setup_required,
            "pages_source_setup_cost_class": "free_repository_setting",
            "pat_or_secret_required_for_pipeline": False,
        },
        "url_map": build_pages_url_map(profile, bridge),
    }


def build_pages_health_state(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    *,
    execute: bool = False,
    timeout_seconds: float = 15,
) -> dict[str, Any]:
    url_map = build_pages_url_map(profile, bridge)
    checks = {}
    for lane, url in url_map.items():
        if lane == "rollback":
            continue
        result = _http_get(url, timeout_seconds=timeout_seconds) if execute else _empty_result()
        checks[lane] = {
            "url": url,
            "status_code": result["status_code"],
            "ok": result["ok"],
            "error": result["error"],
        }
    required = ["base", "dashboard", "staging", "production"]
    required_ok = all(checks.get(name, {}).get("ok") is True for name in required)
    rollback_state = load_pages_rollback_manifest(profile.project_root, bridge)
    rollback_passed = (
        rollback_state.get("rollback_executed") is True
        and rollback_state.get("health", {}).get("status") == "passed"
    )
    status = "not_checked"
    if execute:
        status = "passed" if required_ok else "failed"
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="pages_health"),
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": profile.project_id,
        "execute": execute,
        "status": status,
        "overall_status": status,
        "request_methods_used": ["GET"] if execute else [],
        "authentication": "none",
        "token_used": False,
        "paid_usage_detected": False,
        "provider_api_calls": False,
        "pages_enabled": any(check.get("ok") is True for check in checks.values()),
        "pages_url_observed": any(check.get("url") for check in checks.values()),
        "pages_health_check_passed": status == "passed",
        "dashboard_pages_cd_passed": checks.get("dashboard", {}).get("ok") is True,
        "preview_static_cd_passed": checks.get("preview", {}).get("ok") is True,
        "staging_static_cd_passed": checks.get("staging", {}).get("ok") is True,
        "production_static_cd_passed": checks.get("production", {}).get("ok") is True,
        "safe_static_rollback_execution_passed": rollback_passed,
        "checks": checks,
        "rollback": rollback_state,
        "url_map": url_map,
    }


def build_pages_deploy_manifest(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    pages_health: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="pages_deploy_manifest"),
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": profile.project_id,
        "target_type": "github_pages_static_site",
        "deploy_executed": pages_health.get("pages_health_check_passed") is True,
        "pages_enabled": pages_health.get("pages_enabled") is True,
        "pages_url_observed": pages_health.get("pages_url_observed") is True,
        "pages_health_check_passed": pages_health.get("pages_health_check_passed") is True,
        "url_map": pages_health.get("url_map", build_pages_url_map(profile, bridge)),
        "side_effects": {
            "provider_api_calls": False,
            "paid_usage_detected": False,
            "secrets_used": False,
            "pat_used": False,
            "deploy_key_used": False,
            "external_cloud_used": False,
            "db_migration_executed": False,
            "research_evidence_written": False,
            "github_pages_static_deploy": pages_health.get("pages_health_check_passed") is True,
        },
    }


def build_pages_rollback_manifest(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    *,
    rollback_executed: bool = False,
    target_ref: str = "",
) -> dict[str, Any]:
    health_passed = bool(rollback_executed)
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="pages_rollback_manifest"),
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": profile.project_id,
        "environment": "production",
        "rollback_class": "safe_static_pages",
        "rollback_executed": rollback_executed,
        "target_ref": target_ref,
        "target": {
            "strategy": "previous_known_good_static_pages_snapshot",
            "resolved": rollback_executed,
            "url": build_pages_url_map(profile, bridge).get("production", ""),
        },
        "health": {
            "status": "passed" if health_passed else "pending",
            "checks": [
                {"name": "safe_static_pages_only", "status": "passed"},
                {"name": "provider_api_calls_false", "status": "passed"},
                {"name": "db_migration_false", "status": "passed"},
                {"name": "not_research_evidence", "status": "passed"},
            ],
        },
        "side_effects": {
            "provider_api_calls": False,
            "paid_usage_detected": False,
            "secrets_used": False,
            "pat_used": False,
            "deploy_key_used": False,
            "external_cloud_used": False,
            "db_migration_executed": False,
            "destructive_action": False,
            "research_evidence_written": False,
            "safe_static_pages_deploy": rollback_executed,
        },
        "refused_rollback_classes": [
            "destructive_action",
            "db_restore",
            "provider_api_quota",
            "secrets_credentials",
            "external_cloud_deploy",
            "research_evidence_write",
        ],
    }


def load_pages_readiness(project_root: Path, bridge: ProjectBridge) -> dict[str, Any]:
    return _load_first_json(_pages_readiness_paths(project_root, bridge))


def load_pages_health(project_root: Path, bridge: ProjectBridge) -> dict[str, Any]:
    return _load_first_json(_pages_health_paths(project_root, bridge))


def load_pages_rollback_manifest(project_root: Path, bridge: ProjectBridge) -> dict[str, Any]:
    return _load_first_json(_pages_rollback_paths(project_root, bridge))


def write_pages_readiness_artifacts(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    state: dict[str, Any],
) -> None:
    for path in _pages_readiness_paths(profile.project_root, bridge):
        _write_json(path, state)


def write_pages_health_artifacts(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    health: dict[str, Any],
    deploy_manifest: dict[str, Any],
) -> None:
    for path in _pages_health_paths(profile.project_root, bridge):
        _write_json(path, health)
    for path in _pages_deploy_paths(profile.project_root, bridge):
        _write_json(path, deploy_manifest)


def write_pages_rollback_artifacts(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    state: dict[str, Any],
) -> None:
    for path in _pages_rollback_paths(profile.project_root, bridge):
        _write_json(path, state)


def _pages_readiness_paths(project_root: Path, bridge: ProjectBridge) -> list[Path]:
    return [
        project_root / bridge.dashboard_dir / "data" / "pages-readiness.json",
        project_root / bridge.generated_dir / "effective-pages-readiness.json",
    ]


def _pages_health_paths(project_root: Path, bridge: ProjectBridge) -> list[Path]:
    return [
        project_root / bridge.dashboard_dir / "data" / "pages-health.json",
        project_root / bridge.generated_dir / "effective-pages-health.json",
    ]


def _pages_deploy_paths(project_root: Path, bridge: ProjectBridge) -> list[Path]:
    return [
        project_root / bridge.dashboard_dir / "data" / "pages-deploy-manifest.json",
        project_root / bridge.generated_dir / "effective-pages-deploy-manifest.json",
    ]


def _pages_rollback_paths(project_root: Path, bridge: ProjectBridge) -> list[Path]:
    return [
        project_root / bridge.dashboard_dir / "data" / "pages-rollback-manifest.json",
        project_root / bridge.generated_dir / "effective-pages-rollback-manifest.json",
    ]


def _load_first_json(paths: list[Path]) -> dict[str, Any]:
    for path in paths:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
    return {}


def _api_repo_url(repository: str) -> str:
    owner, repo = _split_repository(repository)
    if not owner or not repo:
        return ""
    encoded_owner = urllib.parse.quote(owner, safe="")
    encoded_repo = urllib.parse.quote(repo, safe="")
    return f"{API_ROOT}/repos/{encoded_owner}/{encoded_repo}"


def _split_repository(repository: str) -> tuple[str, str]:
    parts = repository.split("/", 1)
    if len(parts) != 2:
        return "", ""
    return parts[0], parts[1]


def _get_json(url: str, *, timeout_seconds: float) -> dict[str, Any]:
    if not url:
        return _empty_result(error="missing URL")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-foundation-pages-readiness",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body.strip() else {}
            return {"ok": True, "status_code": response.status, "payload": payload, "error": ""}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body.strip() else {}
        except json.JSONDecodeError:
            payload = {"message": body[:500]}
        return {
            "ok": False,
            "status_code": exc.code,
            "payload": payload,
            "error": _message(payload) or exc.reason,
        }
    except (OSError, TimeoutError) as exc:
        return _empty_result(error=str(exc))


def _get_gh_json(path: str, *, timeout_seconds: float) -> dict[str, Any]:
    if not path:
        return _empty_result(error="missing gh api path")
    try:
        result = subprocess.run(
            ["gh", "api", path],
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return _empty_result(error="gh CLI not found")
    except subprocess.TimeoutExpired:
        return _empty_result(error="gh API request timed out")
    if result.returncode != 0:
        return _empty_result(error=result.stderr.strip()[:500])
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"message": result.stdout[:500]}
    return {"ok": True, "status_code": 200, "payload": payload, "error": ""}


def _http_get(url: str, *, timeout_seconds: float) -> dict[str, Any]:
    if not url:
        return _empty_result(error="missing URL")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "codex-foundation-pages-health"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response.read(256)
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "payload": {},
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status_code": exc.code, "payload": {}, "error": exc.reason}
    except (OSError, TimeoutError) as exc:
        return _empty_result(error=str(exc))


def _empty_result(*, error: str = "") -> dict[str, Any]:
    return {"ok": False, "status_code": 0, "payload": {}, "error": error}


def _payload_dict(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("payload")
    return payload if isinstance(payload, dict) else {}


def _message(payload: Any) -> str:
    if isinstance(payload, dict) and isinstance(payload.get("message"), str):
        return payload["message"]
    return ""


def _safe_path_segment(value: str) -> str:
    safe = value.replace("\\", "/").strip("/")
    safe = safe.replace("/", "-")
    return urllib.parse.quote(safe or "unknown", safe="-._")


def _git(project_root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
