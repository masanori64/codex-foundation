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


def build_github_read_state(
    project_root: Path,
    bridge: ProjectBridge,
    *,
    execute: bool = False,
    timeout_seconds: float = 15,
) -> dict[str, Any]:
    repository = _select_repository(project_root, bridge)
    state: dict[str, Any] = {
        "schema_version": 1,
        **control_marker(artifact_kind="github_read_state"),
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": repository,
        "collection_mode": "unauthenticated_read_only" if execute else "not_collected",
        "status": "not_collected",
        "authentication": "none",
        "token_used": False,
        "secrets_used": False,
        "write_operations_available": False,
        "mutation_methods_available": [],
        "request_methods_used": [],
        "api_calls_executed": False,
        "paid_usage_detected": False,
        "provider_api_calls": False,
        "deploy_executed": False,
        "rollback_executed": False,
        "endpoints": [],
        "repo": {},
        "pull_requests": {"sample_count": 0, "items": []},
        "workflow_runs": {"sample_count": 0, "items": []},
        "artifacts": {"sample_count": 0, "items": []},
        "rate_limit": {},
    }
    if not execute:
        state["reason"] = "GitHub read-only collection has not been executed."
        return state
    state["api_calls_executed"] = True
    state["request_methods_used"] = ["GET"]
    endpoints = _endpoint_plan(repository["selected"])
    for endpoint in endpoints:
        result = _get_json(endpoint["url"], timeout_seconds=timeout_seconds)
        endpoint_record = {
            "name": endpoint["name"],
            "method": "GET",
            "url": _redact_url(endpoint["url"]),
            "status_code": result["status_code"],
            "ok": result["ok"],
            "error": result["error"],
            "rate_limit": result["rate_limit"],
        }
        state["endpoints"].append(endpoint_record)
        _merge_endpoint_payload(state, endpoint["name"], result["payload"])
    ok_count = sum(1 for endpoint in state["endpoints"] if endpoint["ok"])
    if ok_count == len(state["endpoints"]):
        state["status"] = "passed"
        state["reason"] = "All unauthenticated GitHub REST read endpoints returned successfully."
    elif ok_count:
        state["status"] = "partial"
        state["reason"] = "Some GitHub REST read endpoints were readable without credentials."
    else:
        state["status"] = "read_blocked"
        state["reason"] = (
            "No GitHub REST read endpoints were readable without credentials; "
            "the no-secret/no-PAT gate remains closed."
        )
    return state


def load_github_read_state(project_root: Path, bridge: ProjectBridge) -> dict[str, Any]:
    for path in _github_read_paths(project_root, bridge):
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
    return build_github_read_state(project_root, bridge, execute=False)


def write_github_read_artifacts(
    profile: ProjectProfile,
    bridge: ProjectBridge,
    state: dict[str, Any],
) -> None:
    for path in _github_read_paths(profile.project_root, bridge):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, state)


def _github_read_paths(project_root: Path, bridge: ProjectBridge) -> list[Path]:
    return [
        project_root / bridge.dashboard_dir / "data" / "github-read-state.json",
        project_root / bridge.generated_dir / "effective-github-read-state.json",
    ]


def _select_repository(project_root: Path, bridge: ProjectBridge) -> dict[str, Any]:
    bridge_repo = str(bridge.data["github"].get("repository", ""))
    remote_repo = _repository_from_remote(project_root)
    selected = remote_repo or bridge_repo
    return {
        "bridge": bridge_repo,
        "git_remote": remote_repo,
        "selected": selected,
        "source": "git_remote" if remote_repo else "bridge",
        "mismatch": bool(remote_repo and bridge_repo and remote_repo != bridge_repo),
    }


def _repository_from_remote(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return _parse_github_repo(result.stdout.strip())


def _parse_github_repo(remote: str) -> str:
    if remote.startswith("git@github.com:"):
        value = remote.removeprefix("git@github.com:")
    elif "github.com/" in remote:
        value = remote.split("github.com/", 1)[1]
    else:
        return ""
    value = value.removesuffix(".git").strip("/")
    parts = value.split("/")
    if len(parts) < 2:
        return ""
    return f"{parts[0]}/{parts[1]}"


def _endpoint_plan(repository: str) -> list[dict[str, str]]:
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in repository.split("/", 1))
    return [
        {"name": "repo", "url": f"{API_ROOT}/repos/{encoded}"},
        {
            "name": "pull_requests",
            "url": f"{API_ROOT}/repos/{encoded}/pulls?state=open&per_page=10",
        },
        {"name": "workflow_runs", "url": f"{API_ROOT}/repos/{encoded}/actions/runs?per_page=10"},
        {"name": "artifacts", "url": f"{API_ROOT}/repos/{encoded}/actions/artifacts?per_page=10"},
        {"name": "rate_limit", "url": f"{API_ROOT}/rate_limit"},
    ]


def _get_json(url: str, *, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-foundation-no-cost-read-smoke",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body.strip() else {}
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "payload": payload,
                "error": "",
                "rate_limit": _rate_headers(response.headers),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        payload: Any
        try:
            payload = json.loads(body) if body.strip() else {}
        except json.JSONDecodeError:
            payload = {"message": body[:500]}
        return {
            "ok": False,
            "status_code": exc.code,
            "payload": payload,
            "error": _payload_message(payload) or exc.reason,
            "rate_limit": _rate_headers(exc.headers),
        }
    except (OSError, TimeoutError) as exc:
        return {
            "ok": False,
            "status_code": 0,
            "payload": {},
            "error": str(exc),
            "rate_limit": {},
        }


def _merge_endpoint_payload(state: dict[str, Any], name: str, payload: Any) -> None:
    if name == "pull_requests":
        items = payload if isinstance(payload, list) else []
        state["pull_requests"] = {
            "sample_count": len(items),
            "items": [
                {
                    "number": item.get("number"),
                    "title": item.get("title", ""),
                    "state": item.get("state", ""),
                    "html_url": item.get("html_url", ""),
                }
                for item in items[:10]
                if isinstance(item, dict)
            ],
        }
        return
    if not isinstance(payload, dict):
        return
    if name == "repo":
        state["repo"] = {
            "full_name": payload.get("full_name", ""),
            "private": payload.get("private"),
            "visibility": payload.get("visibility", ""),
            "default_branch": payload.get("default_branch", ""),
            "html_url": payload.get("html_url", ""),
        }
        return
    if name == "workflow_runs":
        runs = payload.get("workflow_runs", [])
        if not isinstance(runs, list):
            runs = []
        state["workflow_runs"] = {
            "total_count": payload.get("total_count", 0),
            "sample_count": len(runs),
            "items": [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                    "path": item.get("path", ""),
                    "head_branch": item.get("head_branch", ""),
                    "run_number": item.get("run_number"),
                    "run_attempt": item.get("run_attempt"),
                    "status": item.get("status", ""),
                    "conclusion": item.get("conclusion"),
                    "event": item.get("event", ""),
                    "created_at": item.get("created_at", ""),
                    "updated_at": item.get("updated_at", ""),
                    "html_url": item.get("html_url", ""),
                }
                for item in runs[:10]
                if isinstance(item, dict)
            ],
        }
        return
    if name == "artifacts":
        artifacts = payload.get("artifacts", [])
        if not isinstance(artifacts, list):
            artifacts = []
        state["artifacts"] = {
            "total_count": payload.get("total_count", 0),
            "sample_count": len(artifacts),
            "items": [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                    "expired": item.get("expired"),
                    "size_in_bytes": item.get("size_in_bytes"),
                    "created_at": item.get("created_at", ""),
                    "expires_at": item.get("expires_at", ""),
                    "workflow_run": _artifact_workflow_run(item.get("workflow_run")),
                }
                for item in artifacts[:10]
                if isinstance(item, dict)
            ],
        }
        return
    if name == "rate_limit":
        resources = payload.get("resources", {})
        core = resources.get("core", {}) if isinstance(resources, dict) else {}
        state["rate_limit"] = {
            "core": core,
            "rate": payload.get("rate", {}),
        }


def _payload_message(payload: Any) -> str:
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str):
            return message
    return ""


def _artifact_workflow_run(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "id": value.get("id"),
        "repository_id": value.get("repository_id"),
        "head_branch": value.get("head_branch", ""),
        "head_sha": value.get("head_sha", ""),
    }


def _rate_headers(headers: Any) -> dict[str, str]:
    keys = (
        "x-ratelimit-limit",
        "x-ratelimit-remaining",
        "x-ratelimit-used",
        "x-ratelimit-reset",
        "x-ratelimit-resource",
    )
    return {key: headers.get(key, "") for key in keys if headers.get(key) is not None}


def _redact_url(url: str) -> str:
    return url.split("?", 1)[0]


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
