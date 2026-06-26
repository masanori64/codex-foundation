# Codex Foundation Vendor Source Lock

Created: 2026-06-25

This lock records Codex foundation source and candidate decisions for Skills, memory,
self-improvement, session operations, and external Skill/Plugin/MCP governance. It is a provenance
artifact, not permission to install, clone, enable, or call any third-party provider, connector,
hook, plugin, MCP server, or tool.

## Policy

- `maasa/.codex` owns Codex-wide Skills, memory, retrospectives, context/session operations,
  self-improvement staging, external Skill/Plugin/MCP governance, and creative output helpers.
- `maasa/research_x` owns the AI-callable X memory-search tool and keeps only thin bridge
  contracts to this foundation.
- External sources remain disabled, staged, provider-gated, or reference-only until source review,
  pinning, script/hook scan, overlap checks, negative-trigger tests, and human promotion pass.
- Provider-backed or cloud memory candidates require explicit provider/privacy approval.
- Install, hook, MCP, plugin, connector, credential, model-download, and dependency changes require
  explicit manual promotion even when they are not provider/API spend.

## Locked Sources

| Candidate | Source | Locked decision |
|---|---|---|
| `headroom` | https://github.com/chopratejas/headroom | Disabled; security/local-dependency gate. |
| `supermemory` | https://github.com/supermemoryai/supermemory | Provider/cloud-memory candidate; not default Codex memory. |
| `superpowers` | https://github.com/obra/superpowers | Disabled; review then optional. MIT license and `v5.1.0` peeled commit `f2cbfbefebbfef77321e4c9abc9e949826bea9d7` checked 2026-06-12; no full source/script/hook audit yet. |
| `superclaude-framework` | https://github.com/SuperClaude-Org/SuperClaude_Framework | Reference only for Codex. |
| `minimax-skills` | https://github.com/MiniMax-AI/skills | Disabled; stack-specific optional. |
| `anthropic-official-skills` | https://github.com/anthropics/skills | Format reference only. |
| `vercel-agent-skills` | https://github.com/vercel-labs/agent-skills | Disabled; frontend optional only. |
| `planning-with-files` | https://github.com/OthmanAdi/planning-with-files | Disabled; adapt only if no duplicate tracker. |
| `context-engineering-skills` | https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering | Disabled; reference/adapt after review. |
| `composio-skills` | https://github.com/ComposioHQ/skills | Disabled; do not global install. |
| `antfu-skills` | https://github.com/antfu/skills | Reference only. |
| `ponytail` | https://github.com/DietrichGebert/ponytail | Catalog/source reference only; no install, clone, hook, or runtime adoption without source review and negative-trigger checks. |
| `awesome-agent-skills` | https://github.com/VoltAgent/awesome-agent-skills | Catalog only; no bulk install. |
| `ai-assistant-workspace` | https://github.com/karaage0703/ai-assistant-workspace | Reference only. |
| `ian-xiaohei-illustrations` | https://github.com/helloianneo/ian-xiaohei-illustrations | Creative optional/reference; MIT license and `v1.0.0` ref `686575741a61e2c0be5e4c6d3615ebf6217dd322` checked 2026-06-12. Use only for explicit visual-planning requests; generated images are not evidence. |
| `goal-setter` | https://github.com/gotalab/goal-setter-skill | Installed personal Codex App plugin; MIT license, plugin `v0.9.3`, and commit `4f37792ca6ee0a3729c861d28485a52e05571b0b` checked 2026-06-26. Codex-wide goal intake only; do not also install the standalone Skill copy. |
| `matt-pocock-skills` | https://github.com/mattpocock/skills | Reference only. |
| `agentmemory` | https://github.com/rohitg00/agentmemory | Disabled; source-review-required. Apache-2.0 license and `v0.9.27` peeled commit `25158519d5d68b9060a97ba5bdcccc3e1aba6d79` checked 2026-06-22. Useful comparison target for hook/MCP/auto-capture/decay/search/inject design; no install now. |
| `skilladaptor` | https://github.com/zjunlp/SkillAdaptor | Staging only; fault-localization and responsible-Skill attribution reference. No automatic Skill rewrite. |
| `muse-autoskill` | https://arxiv.org/abs/2605.27366 | Staging only; Skill lifecycle reference. No automatic Skill growth or provider-backed mining. |
| `evoskill` | https://github.com/sentient-agi/EvoSkill | Staging only; self-evolving Skill discovery reference. No clone/install, no automatic Skill edits, replay/qualifier/human promotion required. |
| `gepa` | https://github.com/gepa-ai/gepa | Staging only; reflective prompt/code optimization reference. Provider/model calls are gated; no default optimizer runtime. |
| `textgrad` | https://github.com/zou-group/textgrad | Staging only; textual-gradient optimizer reference. Provider/model calls are gated; no dependency install. |
| `trace2skill` | https://github.com/Qwen-Applications/Trace2Skill | Staging only; trace-to-skill consolidation reference. No automatic Skill creation or mutation. |
| `skillgrad` | https://github.com/wwwhy725/SkillGrad | Staging only; gradient-style Skill patching reference. Replay, held-out checks, and human promotion required. |
| `skillsmith-paper` | https://arxiv.org/abs/2605.15215 | Reference only; Skill boundary/compiler idea for token-cost reduction. No compiler/runtime adoption without local fixtures and source review. |
| `mem0` | https://github.com/mem0ai/mem0 | Provider/cloud-memory candidate; explicit privacy/provider approval required before use. |
| `core` | https://github.com/RedPlanetHQ/core | Staging/reference only; always-on personal AI OS surface is not enabled and would require connector/auth review. |
| `automem` | https://github.com/verygoodplugins/automem | Staging only; graph-vector memory reference. No MCP/server/provider setup without approval. |
| `memoryoss` | https://memoryoss.com/ | Staging/reference only; local/proxy memory candidate. Binary/proxy/runtime review required before adoption. |
| `memories-sh` | https://memories.sh/docs | Staging/reference only; local-first/cloud memory docs. CLI/MCP/cloud sync remain disabled until reviewed. |
| `pallium` | https://github.com/tszaks/pallium | Staging/reference only; redirected/renamed from `https://github.com/tszaks/codex-memory`. Treat as a read-only repo intelligence canary, not generic Codex memory. Session indexing, embeddings, install, hook, and provider activation remain disabled until reviewed. |
