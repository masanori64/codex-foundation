from __future__ import annotations

from pathlib import Path
from typing import Any

from .foundation import FOUNDATION_ID, control_marker, foundation_manifest_summary

PIPELINE_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = PIPELINE_ROOT / "templates" / "github-workflows"
WORKFLOW_DIR = Path(".github") / "workflows"
WRAPPERS = {
    "codex-ci.yml": "codex-ci.template.yml",
    "codex-dashboard.yml": "codex-dashboard.template.yml",
    "codex-preview.yml": "codex-preview.template.yml",
    "codex-artifact-smoke.yml": "codex-artifact-smoke.template.yml",
}
PAGES_WRAPPERS = {
    "codex-pages-dashboard.yml": "codex-pages-dashboard.template.yml",
    "codex-pages-preview.yml": "codex-pages-preview.template.yml",
    "codex-pages-staging.yml": "codex-pages-staging.template.yml",
    "codex-pages-production.yml": "codex-pages-production.template.yml",
    "codex-pages-rollback.yml": "codex-pages-rollback.template.yml",
}
FORBIDDEN_SNIPPETS = (
    "pull_request_target",
    "pages: write",
    "id-token: write",
    "deployments: write",
    "secrets.",
    "gh api",
    "curl https://api.github.com",
    "C:/Users/maasa/.codex",
    "C:\\Users\\maasa\\.codex",
    "pages: write",
    "environment:",
)
PAGES_FORBIDDEN_SNIPPETS = (
    "pull_request_target",
    "secrets.",
    "gh api",
    "curl https://api.github.com",
    "C:/Users/maasa/.codex",
    "C:\\Users\\maasa\\.codex",
)
REQUIRED_MARKERS = (
    "control_artifact=true",
    "not_project_evidence=true",
    "not_research_evidence=true",
    "not_citation=true",
    "not_answer_support=true",
    f"generated_by={FOUNDATION_ID}",
    "foundation_manifest_sha256=",
)


def generate_workflow_wrappers(project_root: Path) -> dict[str, Any]:
    workflow_root = project_root / WORKFLOW_DIR
    workflow_root.mkdir(parents=True, exist_ok=True)
    written = []
    for output_name, template_name in WRAPPERS.items():
        output_path = workflow_root / output_name
        output_path.write_text(
            render_workflow_template(template_name=template_name),
            encoding="utf-8",
            newline="\n",
        )
        written.append(str(output_path))
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="github_workflow_wrappers"),
        "project_root": str(project_root),
        "workflow_files": written,
        "github_api_calls_executed": False,
        "deploy_executed": False,
        "pages_enabled": False,
        "repository_settings_changed": False,
        "secrets_used": False,
    }


def generate_pages_workflows(project_root: Path) -> dict[str, Any]:
    workflow_root = project_root / WORKFLOW_DIR
    workflow_root.mkdir(parents=True, exist_ok=True)
    written = []
    for output_name, template_name in PAGES_WRAPPERS.items():
        output_path = workflow_root / output_name
        output_path.write_text(
            render_workflow_template(template_name=template_name),
            encoding="utf-8",
            newline="\n",
        )
        written.append(str(output_path))
    return {
        "schema_version": 1,
        **control_marker(artifact_kind="github_pages_workflows"),
        "project_root": str(project_root),
        "workflow_files": written,
        "github_pages_static_cd": True,
        "standard_runner_only": True,
        "provider_api_calls": False,
        "secrets_used": False,
        "paid_usage_detected": False,
    }


def render_workflow_template(*, template_name: str) -> str:
    template_path = TEMPLATE_ROOT / template_name
    text = template_path.read_text(encoding="utf-8")
    manifest = foundation_manifest_summary()
    return (
        text.replace("{{FOUNDATION_ID}}", FOUNDATION_ID)
        .replace("{{FOUNDATION_MANIFEST_SHA256}}", str(manifest["sha256"]))
        .replace("{{SOURCE_TEMPLATE}}", f"templates/github-workflows/{template_name}")
    )


def validate_workflow_wrappers(
    project_root: Path,
    *,
    capability_status: str | None = None,
    dashboard_artifact_status: str | None = None,
) -> list[str]:
    workflow_root = project_root / WORKFLOW_DIR
    expected_paths = {name: workflow_root / name for name in WRAPPERS}
    existing = [path for path in expected_paths.values() if path.exists()]
    if not existing:
        if _enabled_status(capability_status):
            return [
                "github_actions_wrappers capability is enabled but wrapper files are missing"
            ]
        return []
    errors: list[str] = []
    if capability_status == "disabled":
        errors.append(
            "github_actions_wrappers capability is disabled but wrapper files exist"
        )
    if dashboard_artifact_status == "disabled":
        errors.append(
            "dashboard_artifact_cd capability is disabled but dashboard wrapper exists"
        )
    for output_name, path in expected_paths.items():
        if not path.exists():
            errors.append(f"missing GitHub Actions wrapper: {path}")
            continue
        errors.extend(_validate_workflow_text(output_name, path))
    return errors


def validate_pages_workflows(project_root: Path) -> list[str]:
    workflow_root = project_root / WORKFLOW_DIR
    expected_paths = {name: workflow_root / name for name in PAGES_WRAPPERS}
    errors: list[str] = []
    for output_name, path in expected_paths.items():
        if not path.exists():
            errors.append(f"missing GitHub Pages workflow: {path}")
            continue
        errors.extend(_validate_pages_workflow_text(output_name, path))
    return errors


def _validate_workflow_text(output_name: str, path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append(f"{path}: missing marker {marker!r}")
    for snippet in FORBIDDEN_SNIPPETS:
        if snippet.casefold() in text.casefold():
            errors.append(f"{path}: forbidden GitHub workflow snippet {snippet!r}")
    if "permissions:\n  contents: read" not in text:
        errors.append(f"{path}: top-level permissions must be contents: read")
    if text.count("permissions:\n      contents: read") < 1:
        errors.append(f"{path}: job-level permissions must be contents: read")
    if "\n  pull_request:" not in text:
        errors.append(f"{path}: wrapper must run on pull_request")
    if output_name == "codex-artifact-smoke.yml":
        if "\n  push:" not in text:
            errors.append(f"{path}: artifact smoke wrapper must run on push")
        if "\n  workflow_dispatch:" in text:
            errors.append(f"{path}: artifact smoke wrapper must not use workflow_dispatch")
    elif "\n  workflow_dispatch:" not in text:
        errors.append(f"{path}: wrapper must support workflow_dispatch")
    if output_name != "codex-artifact-smoke.yml" and "\n  push:" in text:
        errors.append(f"{path}: wrapper must not run on push")
    if "actions/checkout@v4" not in text:
        errors.append(f"{path}: wrapper must use checkout with read-only permissions")
    if (
        output_name in {"codex-dashboard.yml", "codex-artifact-smoke.yml"}
        and "actions/upload-artifact@v4" not in text
    ):
        errors.append(f"{path}: wrapper must upload an artifact")
    if output_name == "codex-preview.yml":
        for snippet in (
            "actions/upload-artifact@v4",
            "preview-manifest.json",
            "GITHUB_STEP_SUMMARY",
            "live_url",
        ):
            if snippet not in text:
                errors.append(f"{path}: preview wrapper missing {snippet!r}")
    return errors


def _validate_pages_workflow_text(output_name: str, path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append(f"{path}: missing marker {marker!r}")
    for snippet in PAGES_FORBIDDEN_SNIPPETS:
        if snippet.casefold() in text.casefold():
            errors.append(f"{path}: forbidden GitHub Pages workflow snippet {snippet!r}")
    for snippet in (
        "permissions:\n  contents: read\n  pages: write\n  id-token: write",
        "actions/configure-pages@v5",
        "actions/upload-pages-artifact@v3",
        "actions/deploy-pages@v4",
        "runs-on: ubuntu-latest",
        "control_artifact=true",
        "not_research_evidence=true",
    ):
        if snippet not in text:
            errors.append(f"{path}: pages workflow missing {snippet!r}")
    if output_name == "codex-pages-rollback.yml":
        if "\n  workflow_dispatch:" not in text:
            errors.append(f"{path}: rollback must be workflow_dispatch")
        if "target_ref" not in text:
            errors.append(f"{path}: rollback must expose target_ref input")
    else:
        if "\n  push:" not in text:
            errors.append(f"{path}: pages workflow must run on push")
    if output_name != "codex-pages-rollback.yml":
        for snippet in ("previews/", "PREVIEW_PATH"):
            if snippet not in text:
                errors.append(
                    f"{path}: pages workflow must preserve preview path {snippet!r}"
                )
    if output_name.startswith("codex-pages-") and "rollback/latest" not in text:
        errors.append(f"{path}: pages workflow must preserve rollback/latest")
    if output_name == "codex-pages-rollback.yml" and "PREVIEW_PATH" not in text:
        errors.append(f"{path}: rollback workflow must preserve preview/latest")
    if output_name == "codex-pages-staging.yml" and "staging/latest" not in text:
        errors.append(f"{path}: staging workflow must publish staging/latest")
    if output_name == "codex-pages-production.yml" and "production/latest" not in text:
        errors.append(f"{path}: production workflow must publish production/latest")
    if "provider_api_calls=false" not in text:
        errors.append(f"{path}: pages workflow must state provider_api_calls=false")
    if "paid_usage_detected=false" not in text:
        errors.append(f"{path}: pages workflow must state paid_usage_detected=false")
    return errors


def _enabled_status(status: str | None) -> bool:
    return status not in (None, "", "disabled")
