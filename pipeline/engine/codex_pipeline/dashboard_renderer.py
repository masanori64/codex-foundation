from __future__ import annotations

import html
import json
from typing import Any


def render_dashboard_html(state: dict[str, Any]) -> str:
    notice = "control artifact / not evidence / not citation"
    gate_rows = "\n".join(
        "<tr>"
        f"<td>{_esc(gate['gate_id'])}</td>"
        f"<td>{_esc(gate['status'])}</td>"
        f"<td>{_esc(gate['reason'])}</td>"
        "</tr>"
        for gate in state["gates"]
    )
    lane_rows = "\n".join(
        "<tr>"
        f"<td>{_esc(lane['id'])}</td>"
        f"<td>{_esc(lane['name'])}</td>"
        f"<td>{_esc(str(lane['automatic']).lower())}</td>"
        "</tr>"
        for lane in state["pipeline"]["lanes"]
    )
    capability_rows = "\n".join(
        "<tr>"
        f"<td>{_esc(capability['capability_id'])}</td>"
        f"<td>{_esc(capability['status'])}</td>"
        f"<td>{_esc(capability['reason'])}</td>"
        "</tr>"
        for capability in state["capabilities"]
    )
    mermaid_blocks = "\n".join(
        f"<section><h3>{_esc(name)}</h3><pre>{_esc(source)}</pre></section>"
        for name, source in state["dashboard"]["mermaid"].items()
    )
    state_json = html.escape(json.dumps(state, ensure_ascii=False, sort_keys=True), quote=False)
    github_api_enabled = _esc(str(state["collection"]["github_api_enabled"]).lower())
    rollback_executed = _esc(str(state["rollback_manifest"]["rollback_executed"]).lower())
    audit_status = _esc(state["control_artifact_audit"]["status"])
    github_read = state["github_read_state"]
    cost_guard = state["cost_guard"]
    workflow_artifact_audit = state["workflow_artifact_audit"]
    workflow_smoke = state["workflow_smoke"]
    subagent_dry_run = state["subagent_runtime_dry_run"]
    e2e_completion = state["e2e_completion_manifest"]
    pages_readiness = state["pages_readiness"]
    pages_health = state["pages_health"]
    paid_execution = _esc(
        str(cost_guard["answer"]["has_paid_execution_in_current_pipeline"]).lower()
    )
    artifact_status = _esc(workflow_artifact_audit["status"])
    workflow_smoke_status = _esc(workflow_smoke["status"])
    subagent_dry_run_status = _esc(subagent_dry_run["status"])
    e2e_status = _esc(e2e_completion["final_automatic_pipeline_status"])
    free_static_complete = _esc(
        str(e2e_completion.get("completion", {}).get("free_static_pages_cd_complete", False))
        .lower()
    )
    active_blockers = e2e_completion.get("active_completion_blockers", [])
    active_blockers_text = "none" if not active_blockers else ", ".join(map(str, active_blockers))
    intermediate_smoke = _esc(e2e_completion.get("intermediate_smoke_status", "unknown"))
    hard_blocked_paid_count = len(cost_guard.get("hard_blocked_paid", []))
    outside_scope_count = len(cost_guard.get("not_used_outside_free_static_pages_cd", []))
    pages_readiness_status = _esc(pages_readiness.get("status", "not_checked"))
    pages_health_status = _esc(pages_health.get("overall_status", "not_checked"))
    pages_url = _esc(pages_health.get("url_map", {}).get("base", ""))
    foundation = state["foundation"]
    foundation_panel = (
        f'{_esc(foundation["id"])}<br>'
        f'{_esc(foundation["version"])}'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(state["dashboard"]["title"])}</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #1f2937; background: #f8fafc; }}
    header {{ padding: 24px; background: #111827; color: #fff; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
    section {{ margin: 0 0 24px; }}
    .notice {{
      border: 2px solid #b91c1c;
      background: #fff1f2;
      color: #7f1d1d;
      padding: 12px;
      font-weight: 700;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }}
    .panel {{ background: #fff; border: 1px solid #d1d5db; border-radius: 6px; padding: 16px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #e5e7eb; }}
    pre {{
      white-space: pre-wrap;
      overflow: auto;
      background: #111827;
      color: #f9fafb;
      padding: 12px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{_esc(state["dashboard"]["title"])}</h1>
    <p>{notice}</p>
  </header>
  <main>
    <section class="notice">
      {notice}. This page is never research evidence, never citation support,
      and never answer support.
    </section>
    <section class="grid">
      <div class="panel"><strong>Project</strong><br>{_esc(state["project"]["id"])}</div>
      <div class="panel"><strong>Collection</strong><br>{_esc(state["collection"]["mode"])}</div>
      <div class="panel"><strong>GitHub API</strong><br>{github_api_enabled}</div>
      <div class="panel"><strong>GitHub Read Smoke</strong><br>{_esc(github_read["status"])}</div>
      <div class="panel"><strong>Paid Execution</strong><br>{paid_execution}</div>
      <div class="panel"><strong>Artifact Smoke</strong><br>{artifact_status}</div>
      <div class="panel"><strong>Workflow E2E</strong><br>{workflow_smoke_status}</div>
      <div class="panel"><strong>E2E Completion</strong><br>{e2e_status}</div>
      <div class="panel"><strong>Free Static Pages CD</strong><br>{free_static_complete}</div>
      <div class="panel"><strong>Active Completion Blockers</strong><br>
        {_esc(active_blockers_text)}
      </div>
      <div class="panel"><strong>Intermediate Smoke</strong><br>{intermediate_smoke}</div>
      <div class="panel"><strong>Pages Readiness</strong><br>{pages_readiness_status}</div>
      <div class="panel"><strong>Pages Health</strong><br>{pages_health_status}</div>
      <div class="panel"><strong>Pages URL</strong><br>{pages_url}</div>
      <div class="panel"><strong>Subagent Dry Run</strong><br>{subagent_dry_run_status}</div>
      <div class="panel"><strong>Safe Static Pages Rollback</strong><br>{rollback_executed}</div>
      <div class="panel"><strong>Hard Blocked Paid</strong><br>{hard_blocked_paid_count}</div>
      <div class="panel"><strong>Outside Free Static CD</strong><br>{outside_scope_count}</div>
      <div class="panel"><strong>Evidence Boundary Audit</strong><br>{audit_status}</div>
      <div class="panel"><strong>Foundation</strong><br>{foundation_panel}</div>
      <div class="panel"><strong>Manifest SHA256</strong><br>{_esc(foundation["sha256"])}</div>
    </section>
    <section>
      <h2>HOTL Gates</h2>
      <table><thead><tr><th>Gate</th><th>Status</th><th>Reason</th></tr></thead><tbody>{gate_rows}</tbody></table>
    </section>
    <section>
      <h2>CI/CD Lanes</h2>
      <table><thead><tr><th>Lane</th><th>Name</th><th>Automatic</th></tr></thead><tbody>{lane_rows}</tbody></table>
    </section>
    <section>
      <h2>Capability Kill Switches</h2>
      <table><thead><tr><th>Capability</th><th>Status</th><th>Reason</th></tr></thead><tbody>{capability_rows}</tbody></table>
    </section>
    <section>
      <h2>{_esc(state["project"]["id"])} Evidence Boundary</h2>
      <p>{_esc(state["evidence_boundary"]["invariant"])}</p>
      <p>Control artifacts are evidence: false. Control artifacts are citations: false.</p>
    </section>
    <section>
      <h2>Mermaid Sources</h2>
      {mermaid_blocks}
    </section>
  </main>
  <script type="application/json" id="dashboard-state">{state_json}</script>
</body>
</html>
"""


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
