# Source Origin Inventory

Created: 2026-06-26

This is the consolidated source-origin inventory for the materials supplied around
`research_x` and the Codex foundation. It classifies sources by origin type, not by
whether they became Skills.

This file is a control/provenance index. It is not evidence, not permission to
install, not permission to call providers, and not an instruction to convert
sources into natural-language Skills. Source restoration, provider gates,
license/security review, and human promotion still apply.

## Active Owners

- Original 31-source intake:
  `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/01_foundation_policy_sources/source_inventory.json`
- Human-readable original matrix:
  `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/01_foundation_policy_sources/11_source_review_matrix.md`
- research_x project source lock:
  `C:/Users/maasa/research_x/control/vendor_sources.lock.md`
- research_x machine-readable adoption boundary:
  `C:/Users/maasa/research_x/control/adoption_registry.toml`
- X/GPT 35-item historical candidate flow:
  `C:/Users/maasa/.codex/foundation/project_reviews/research_x_chatgpt_control/x-url-analysis-20260622/wbs-35-item-flow.json`
- Codex foundation registry:
  `C:/Users/maasa/.codex/foundation/codex-foundation-registry.toml`
- Codex foundation source lock:
  `C:/Users/maasa/.codex/foundation/vendor_sources.lock.md`

## Classification Rules

- `paper`: research paper, arXiv paper, benchmark paper, or paper-like research source.
- `article`: blog, Zenn, note, Hugging Face post, vendor engineering article, or community commentary.
- `repo_code`: GitHub or OSS repository containing code, scripts, models, framework code, or tool runtime.
- `skill_or_catalog`: repository or package mainly about agent Skills, prompts, command packs, or Skill catalogs.
- `provider_api`: hosted API, managed cloud service, search API, Reader, OCR provider, embedding provider, or quota-bearing lane.
- `local_code`: code already present in `research_x` or the Codex foundation.
- `design_archive`: imported design package, source matrix, execution prompt, provenance context, ZIP, or disabled script.
- `x_candidate`: X/GPT-derived candidate locator. These are entry points, not restored primary sources.
- `actual_skill`: installed/active Skill surface. Only this class is a real Skill.

## Research Papers

| Source | Locator | Handling |
|---|---|---|
| SkillOpt | https://arxiv.org/html/2605.23904v2 | Codex self-improvement reference; not an active Skill. |
| MUSE-Autoskill | https://arxiv.org/abs/2605.27366 | Skill lifecycle reference; no automatic Skill growth. |
| Reflective Prompt Tuning | https://arxiv.org/abs/2605.21781 | Prompt improvement reference; offline/fake-provider gates only. |
| Agent Skills ecosystem/security papers | https://arxiv.org/abs/2605.13221 | `quarantined_bad_locator`: current arXiv content is unrelated UAV logistics scheduling, not Agent Skills/security. Do not use for Skill/security conclusions until the correct source is restored. |
| SkillSmith | https://arxiv.org/abs/2605.15215 | Skill boundary/compiler and token-cost reference. |
| LLM-Oriented IR | https://arxiv.org/abs/2605.00505 | Retrieval/eval design reference. |
| OCC-RAG | https://arxiv.org/abs/2606.00683 | Answerability/abstention eval reference. |
| SkillAdaptor paper | https://arxiv.org/abs/2606.01311 | Failure-trajectory and Skill revision reference. |
| Adaptive Auto-Harness | https://arxiv.org/abs/2606.01770 | Harness routing/steering reference. |
| SAAS | https://arxiv.org/abs/2605.29796 | Stop-condition and over-search reference. |
| Stale observation masking | https://arxiv.org/abs/2606.00408 | Temporal evidence/eval warning reference. |
| JAMEL | https://arxiv.org/html/2606.01528v1 | GUI/browser exploration memory reference. |
| Visual Skills | https://arxiv.org/html/2606.01414v1 | Visual/spatial workflow reference. |

## Articles, Blogs, And Community Sources

| Source | Locator | Handling |
|---|---|---|
| Claude Code self-improving loop | https://zenn.dev/sonicgarden/articles/claude-code-self-improving-loop | Self-improvement workflow case study. |
| TOKIUM AI tech researcher | https://zenn.dev/tokium_dev/articles/20260427_ai_tech_researcher | Automated research/report/Slack workflow case study. |
| Hatena comments on TOKIUM | https://b.hatena.ne.jp/entry/s/zenn.dev/tokium_dev/articles/20260427_ai_tech_researcher | Community risk signal, not primary evidence. |
| LangChain agent harness | https://www.langchain.com/blog/the-anatomy-of-an-agent-harness | Agent harness concept reference. |
| Prompt as Server | https://huggingface.co/blog/loaiabdalslam/prompt-as-server | PromptContract/MNP reference; not backend replacement. |
| note MNP article | https://note.com/art_reflection/n/nccfe6cc57073?sub_rt=share_pb | Intermediate notation/MNP reference. |
| VS Code token efficiency | https://code.visualstudio.com/blogs/2026/06/17/improving-token-efficiency-in-github-copilot | Context budget and token-efficiency reference. |
| GitHub Copilot context handling | https://github.blog/ai-and-ml/github-copilot/getting-more-from-each-token-how-copilot-improves-context-handling-and-model-routing/ | Context routing reference. |
| Bosun blog | https://huggingface.co/blog/Hanno-Labs/bosun | Relevance/eval model reference. |
| pdgkit note article | https://note.com/nonoonenono/n/n0701699bbf3c | DSL to validate/render artifact pattern reference. |

## GitHub And OSS Code

| Source | Locator | Handling |
|---|---|---|
| headroom | https://github.com/chopratejas/headroom | Context compression tool candidate; security/local-dependency review required. |
| supermemory | https://github.com/supermemoryai/supermemory | Memory architecture reference; hosted/cloud memory not default. |
| agentmemory | https://github.com/rohitg00/agentmemory | Memory/hooks/MCP comparison candidate; disabled. |
| mem0 | https://github.com/mem0ai/mem0 | Cloud/provider memory candidate; privacy/provider gate required. |
| core | https://github.com/RedPlanetHQ/core | Memory/AI-OS style reference. |
| automem | https://github.com/verygoodplugins/automem | Auto-memory reference; no silent capture. |
| Pallium (formerly codex-memory locator) | https://github.com/tszaks/pallium | Redirect/identity drift from `https://github.com/tszaks/codex-memory`; read-only repo intelligence canary only, not generic Codex memory. Session indexing and embeddings stay disabled until explicitly reviewed. |
| memoryoss | https://memoryoss.com/ | Memory architecture/proxy reference; binary/runtime review required. |
| memories-sh | https://memories.sh/docs | Memory lifecycle candidate; CLI/MCP/cloud sync disabled. |
| SkillAdaptor | https://github.com/zjunlp/SkillAdaptor | Self-improvement research repo; no automatic Skill rewrite. |
| EvoSkill | https://github.com/sentient-agi/EvoSkill | Self-improvement candidate; no auto-edit. |
| GEPA | https://github.com/gepa-ai/gepa | Prompt/code optimization reference. |
| TextGrad | https://github.com/zou-group/textgrad | Text-gradient optimization reference. |
| Trace2Skill | https://github.com/Qwen-Applications/Trace2Skill | Trace-to-Skill candidate; proposal-only. |
| SkillGrad | https://github.com/wwwhy725/SkillGrad | Skill update/ranking candidate. |
| single-file-wbs | https://github.com/piguo45/single-file-wbs | Pinned local WBS viewer; limited control artifact. |
| Archify | https://github.com/tt-a1i/archify | Diagram/review aid candidate; generated diagrams are not evidence. |
| pdgkit | https://github.com/shibayamalicht/pdgkit | Historical/limited diagram canary; active lane decommissioned. |
| OCC-RAG repository | https://github.com/optimal-cognitive-core/OCC-RAG | Eval shape reference; runtime not imported. |
| Zvec | https://github.com/alibaba/zvec | Local vector backend candidate; dependency review required. |
| SAAS repository | https://github.com/XMUDeepLIT/SAAS | Stop-condition eval reference; runtime not imported. |
| AdaptiveHarness | https://github.com/A-EVO-Lab/AdaptiveHarness | Harness research repo reference. |
| WarrantBench | https://github.com/Hanno-Labs/warrantbench | Benchmark/eval candidate. |
| PaddleOCR | https://github.com/PaddlePaddle/PaddleOCR | Local OCR candidate; dependency/model review required. |
| manga-ocr | https://github.com/kha-white/manga-ocr | Specialist Japanese/manga OCR candidate. |
| PaddleOCR-VL | https://huggingface.co/PaddlePaddle/PaddleOCR-VL | OCR/VLM model candidate; model download/inference gated. |

## Skill Repositories, Catalogs, And Frameworks

These are about Skill packaging, command systems, or Skill catalogs. They are not
automatically active Skills.

| Source | Locator | Handling |
|---|---|---|
| Superpowers | https://github.com/obra/superpowers | Optional strict-engineering workflow candidate; disabled unless reviewed. |
| SuperClaude Framework | https://github.com/SuperClaude-Org/SuperClaude_Framework | Claude-specific framework reference only. |
| MiniMax skills | https://github.com/MiniMax-AI/skills | Stack-specific Skill template reference. |
| Anthropic skills | https://github.com/anthropics/skills | Skill package structure reference. |
| Vercel Agent Skills | https://github.com/vercel-labs/agent-skills | Frontend Skill reference. |
| Planning with Files | https://github.com/OthmanAdi/planning-with-files | Persistent planning workflow reference; avoid duplicate trackers. |
| Context Engineering Skills | https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering | Context management Skill reference. |
| Composio Skills | https://github.com/ComposioHQ/skills | Connector Skill catalog; credential/connector risk, do not global install. |
| Antfu skills | https://github.com/antfu/skills | Developer Skill style reference. |
| Awesome Agent Skills | https://github.com/VoltAgent/awesome-agent-skills | Catalog only; never bulk install. |
| Matt Pocock skills | https://github.com/mattpocock/skills | Engineering Skill style reference. |
| ian-xiaohei-illustrations | https://github.com/helloianneo/ian-xiaohei-illustrations | Creative/illustration reference and optional explicit style adapter. |
| ai-assistant-workspace | https://github.com/karaage0703/ai-assistant-workspace | Workspace layout reference. |
| goal-setter | https://github.com/gotalab/goal-setter-skill | Installed personal plugin; owns goal intake only. |
| Ponytail | referenced through X item 33 and foundation vendor locks | Over-implementation guard plugin candidate; source review required before hooks/plugins. |

## Provider, API, Search, And Managed-Service Sources

All real calls remain gated by the no-quota/provider rules unless explicitly
lifted in the current conversation and budget/source-restoration checks pass.

| Source | Locator | Handling |
|---|---|---|
| Serper | https://serper.dev | Search API candidate; provider-gated. |
| Firecrawl | https://www.firecrawl.dev/ | Crawl/fetch API candidate; provider-gated. |
| SearXNG | https://docs.searxng.org/ | Self-host search candidate; dependency/network staging. |
| Webshare | https://www.webshare.io/ | Proxy source; rejected by default. |
| Tavily | https://docs.tavily.com/documentation/api-reference/introduction | Search API candidate; provider-gated. |
| Exa | https://exa.ai/docs/reference/search-api-guide | Search API candidate; provider-gated. |
| Perplexity Search API | https://docs.perplexity.ai/docs/search/quickstart | Search/API candidate; provider-gated. |
| Jina Reader lane | `C:/Users/maasa/research_x/src/research_x/memory/reader.py` | Code lane exists; real provider calls disabled. |
| Brave LLM Context lane | `C:/Users/maasa/research_x/src/research_x/memory/llm_context.py` | Code lane exists; real provider calls disabled. |
| Mistral OCR lane | `C:/Users/maasa/research_x/src/research_x/memory/ocr.py` | Code lane exists; real provider calls disabled. |
| Gemini media embedding lane | `C:/Users/maasa/research_x/src/research_x/memory/media_embeddings.py` | Code lane exists; real provider calls disabled. |
| AWS Bedrock / Bedrock AgentCore | AWS docs/pricing and X items 25/31 | Managed provider candidate; gated by IAM/billing/provider freeze. |
| Google Agentic RAG / Vertex / Gemini | X item 26 | Managed provider architecture reference; provider-gated. |
| Unofficial ChatGPT backend API | rejected; official export docs used instead | Rejected default. |
| GPT backend API idea | rejected; official provider surfaces only | Rejected default. |

## Official OpenAI And Codex Documentation

| Source | Locator | Handling |
|---|---|---|
| OpenAI Codex Skills docs | https://developers.openai.com/codex/skills/ | Official Codex Skill behavior reference. |
| OpenAI Codex AGENTS.md docs | https://developers.openai.com/codex/agents-md/ | Official AGENTS.md behavior reference. |
| OpenAI Codex customization docs | https://developers.openai.com/codex/customization/ | Official Codex customization reference. |
| ChatGPT export docs | https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data | Official export path; safer than unofficial backend API. |

## Local Code Sources

These are already local implementation or control surfaces. They are not external
sources and not Skills unless explicitly named as a Skill.

| Source | Locator | Handling |
|---|---|---|
| research_x tool contract | `C:/Users/maasa/research_x/src/research_x/tool_interface/memory_tool_contract.py` | Adopted AI-facing contract. |
| research_x Codex bridge | `C:/Users/maasa/research_x/src/research_x/tool_interface/codex_bridge.py` | Adopted thin bridge contract. |
| SQLite/FTS baseline | `C:/Users/maasa/research_x/src/research_x/memory/search.py` | Adopted local retrieval baseline. |
| Vector projection | `C:/Users/maasa/research_x/src/research_x/memory/vector_projection.py` | Adopted local benchmark/projection harness. |
| External search lane | `C:/Users/maasa/research_x/src/research_x/memory/external.py` | Provider/fake lane; real calls gated. |
| Reader lane | `C:/Users/maasa/research_x/src/research_x/memory/reader.py` | Provider/fake lane; real calls gated. |
| LLM context lane | `C:/Users/maasa/research_x/src/research_x/memory/llm_context.py` | Provider/fake lane; real calls gated. |
| OCR lane | `C:/Users/maasa/research_x/src/research_x/memory/ocr.py` | Provider/local candidate lane. |
| Media embedding lane | `C:/Users/maasa/research_x/src/research_x/memory/media_embeddings.py` | Provider/local candidate lane. |
| Relevance/stale warning | `C:/Users/maasa/research_x/src/research_x/memory/relevance.py` | Local eval/relevance code. |
| Evals | `C:/Users/maasa/research_x/src/research_x/memory/evals.py` | Local eval framework. |
| Workflow | `C:/Users/maasa/research_x/src/research_x/memory/workflow.py` | Local workflow state. |
| X raw source schema | `C:/Users/maasa/research_x/src/research_x/x_store.py` | Local raw-source schema. |
| Codex improvement pipeline | `C:/Users/maasa/.codex/foundation/codex_improvement` | Local foundation package; proposal-only. |
| Codex Skill audit | `C:/Users/maasa/.codex/foundation/skill_audit.py` | Local audit tool. |
| Codex Skill factory | `C:/Users/maasa/.codex/foundation/skill_factory.py` | Local Skill creation/governance helper. |
| Route memory | `C:/Users/maasa/.codex/route_memory/route-memory.json` | Local operation-route registry. |

## Actual Installed Skill Surfaces

Only this section lists real active Skill surfaces. Many sources above informed
these surfaces, but are not themselves Skills.

| Skill | Locator | Handling |
|---|---|---|
| basic-memory-cli | `C:/Users/maasa/.codex/skills/basic-memory-cli/SKILL.md` | Local Codex memory Skill. |
| codex-retrospective | `C:/Users/maasa/.codex/skills/codex-retrospective/SKILL.md` | Codex self-review Skill. |
| codex-fluent | `C:/Users/maasa/.codex/skills/codex-fluent/SKILL.md` | Session hygiene Skill. |
| codex-strict-engineering | deleted 2026-06-26: `C:/Users/maasa/.codex/skills/codex-strict-engineering` | Retired source-inspired method Skill; project instructions now own engineering discipline. |
| chatgpt-control-router | `C:/Users/maasa/.codex/skills/chatgpt-control-router/SKILL.md` | Visible ChatGPT routing Skill. |
| planning-files | `C:/Users/maasa/.codex/skills/planning-files/SKILL.md` | Persistent planning Skill. |
| context-handoff-export | `C:/Users/maasa/.codex/skills/context-handoff-export/SKILL.md` | Context export Skill. |
| context-budget | `C:/Users/maasa/.codex/skills/context-budget/SKILL.md` | Context budget Skill. |
| prompt-contract-testing | `C:/Users/maasa/.codex/skills/prompt-contract-testing/SKILL.md` | Prompt/tool-boundary testing Skill. |
| skill-security-review | `C:/Users/maasa/.codex/skills/skill-security-review/SKILL.md` | Source/Skill trust review Skill. |
| research-x-publishing-illustration | `C:/Users/maasa/.codex/skills/research-x-publishing-illustration/SKILL.md` | Visual planning Skill; outputs are not evidence. |
| ian-xiaohei-illustrations | deleted 2026-06-26: `C:/Users/maasa/.codex/skills/ian-xiaohei-illustrations` | Retired external style adapter; upstream remains reference-only. |
| goal-setter | `C:/Users/maasa/.codex/plugins/cache/personal/goal-setter/0.9.3/skills/goal-setter/SKILL.md` | Installed personal plugin Skill for goal intake. |
| research_x repo Skills | `C:/Users/maasa/research_x/.agents/skills/*/SKILL.md` | Project-local workflow Skills only. |

## Design Archives And Provenance Sources

These are retained because they are source history, original package material,
or disabled artifacts. Do not delete them as duplicates.

| Source | Locator | Handling |
|---|---|---|
| SOURCE_MANIFEST | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/SOURCE_MANIFEST.md` | Layout/provenance manifest. |
| Foundation pattern docs 00-06 | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/00_foundation_pattern_sources/` | Imported design sources, not active instructions. |
| Foundation policy docs 07, 09-11 | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/01_foundation_policy_sources/` | Imported policy/source-review sources, not active instructions. |
| Inactive project plan 08 | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/02_inactive_do_not_execute/08_research_x_project_specific_plan.md` | Historical plan; do not execute wholesale. |
| Inactive execution prompt 12 | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/02_inactive_do_not_execute/12_codex_execution_prompt.md` | Historical prompt; do not execute. |
| Provenance context | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/03_provenance_context/context.md` | Session context record. |
| Original ZIP archives | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/04_original_archives/` | Original archives; not expanded/executed here. |
| Duplicate complete design references | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/05_duplicate_references/` | Recovery/comparison copies. |
| Disabled reproducibility scripts | `C:/Users/maasa/.codex/_foundation_sources/research_x_codex_inbox_20260609/06_reproducibility_artifacts_disabled/` | Script artifacts; execution disabled. |
| X/GPT consultation capture | `C:/Users/maasa/.codex/foundation/project_reviews/research_x_chatgpt_control/x-url-analysis-20260622/` | Historical consultation capture, not evidence. |
| Pre-layer WBS archive | `C:/Users/maasa/.codex/foundation/work_state/research-x-pre-layer-wbs-archive-20260625.json` | Historical mixed WBS archive. |
| Foundation adjunct move record | `C:/Users/maasa/.codex/foundation/work_state/research-x-codex-foundation-adjuncts.json` | Record of Codex foundation tasks moved out of research_x state. |

## X/GPT 35-Item Candidate Flow

These entries are X-derived candidate locators. They are not evidence, not
restored source bundles, and not Skills by default.

| # | Candidate | Type | Current handling |
|---:|---|---|---|
| 1 | Firecrawl Keyless | x_candidate -> provider_api | Provider-gated closed for no-quota local flow. |
| 2 | VS Code/Copilot token efficiency | x_candidate -> article/practice | Absorbed into context-budget/tool-deferral practice. |
| 3 | Harness decomposition | x_candidate -> architecture principle | Absorbed by Skill boundaries and scoped workflows. |
| 4 | Self-improving agents/local optimum | x_candidate -> self-improvement reference | Codex foundation lesson; needs branching/eval/human gates. |
| 5 | YAML-to-HTML structure-view split | x_candidate -> artifact pattern | Second-wave local artifact-pattern candidate. |
| 6 | RAG Knowledge Hub | x_candidate -> source-intake/reference | Closed/reference-only due to dependency/source-restoration concerns. |
| 7 | OCC-RAG | x_candidate -> paper/retrieval_eval | Local answerability fixture lane processed. |
| 8 | Stale observation masking | x_candidate -> paper/eval_warning | Route-level warning processed; no universal masking. |
| 9 | Ontology mention | x_candidate -> unknown | Not actionable without restored context. |
| 10 | Archify | x_candidate -> repo_code/control_artifact | Second-wave diagram/review aid candidate. |
| 11 | WBS Viewer | x_candidate -> repo_code/control_artifact | Pinned local WBS viewer processed. |
| 12 | Agentmemory | x_candidate -> repo_code/memory | Disabled source-lock decision processed. |
| 13 | Adaptive Auto-Harness | x_candidate -> paper/harness | Design input only. |
| 14 | SkillAdaptor | x_candidate -> paper/repo/self_improvement | Local ImprovementSignal qualifier pattern processed. |
| 15 | Devin/Manus mention | x_candidate -> vendor mention | Not actionable without separate vendor evaluation. |
| 16 | Zvec | x_candidate -> repo_code/local_backend | Local benchmark gate processed; dependency-review only. |
| 17 | SAAS | x_candidate -> paper/repo/retrieval_eval | Stop-condition audit processed; no full runtime import. |
| 18 | Amazon State-Aware RAG | x_candidate -> provider/reference | Reference only; provider shape is heavy. |
| 19 | AI code-review responsibility split | x_candidate -> review principle | Absorbed by review stance and human-on-the-loop policy. |
| 20 | /grill-me | x_candidate -> workflow idea | Absorbed by decision-loop workflow. |
| 21 | grill-me plus parallel review | x_candidate -> workflow idea | Absorbed by decision-loop and parallel-review policy. |
| 22 | Hanno-Lab Bosun | x_candidate -> model/eval | Local relevance/support fixture lane processed. |
| 23 | JAMEL | x_candidate -> paper/gui_research | Condition-triggered only. |
| 24 | MUSE-Autoskill | x_candidate -> paper/self_improvement | Codex foundation design input only. |
| 25 | Slack/RAG loop on Bedrock | x_candidate -> provider_api | AWS provider-gated closed. |
| 26 | Google Agentic RAG | x_candidate -> provider_api | Google provider-gated closed. |
| 27 | Unknown | x_candidate -> unknown | Not actionable. |
| 28 | State separated from LLM | x_candidate -> architecture principle | Absorbed by workflow state and gap tracking. |
| 29 | Visual Skills | x_candidate -> visual workflow/research | Condition-triggered only. |
| 30 | Decision rules as Markdown | x_candidate -> documentation/workflow | Absorbed by AGENTS and Skill surfaces. |
| 31 | Bedrock AgentCore | x_candidate -> provider_api | AWS provider-gated closed. |
| 32 | LLM-Oriented IR | x_candidate -> paper/retrieval_eval | Use as retrieval denoising/citation-yield checklist. |
| 33 | Ponytail plugin | x_candidate -> plugin/hook candidate | Source-review-only; no hook/plugin adoption. |
| 34 | pdgkit article | x_candidate -> article/pattern | Dormant pattern; item 35 owns the body canary. |
| 35 | pdgkit OSS | x_candidate -> repo_code/control_artifact | Limited canary processed; active lane decommissioned/limited. |

## Consolidation Decision

Keep this file as the single quick-read source-origin classification. Keep the
source locks, adoption registries, manifests, archives, and historical captures
because they are provenance or machine-readable governance records. Do not keep
separate temporary "latest analysis" Markdown files as durable classification
surfaces.

## Quarantined And Redirected Locators

| Source | Locator ID | Current state | Required handling |
|---|---|---|---|
| Agent Skills ecosystem/security papers | `2605.13221` | `quarantined_bad_locator`; current arXiv content is unrelated UAV logistics scheduling. | Do not use `https://arxiv.org/abs/2605.13221`, `https://arxiv.org/html/2605.13221`, `arxiv:2605.13221`, or bare `2605.13221` as an active Agent Skills/security source in registry, vendor lock, plans, or source-decision JSON until the correct source is restored. |
| Pallium / old codex-memory locator | canonical `https://github.com/tszaks/pallium`; legacy `https://github.com/tszaks/codex-memory` | Identity drift repaired. The current canonical project is Pallium, not generic Codex memory. | Keep `codex-memory` only as a legacy surface alias. Promotion remains read-only, no install, no session indexing, no embeddings, no hooks, no writes, and no hidden memory injection until source/dependency review and explicit approval. |

## Skill Surface Triage

Checked: 2026-06-26

Evidence used:

- Actual personal Skill directories under `C:/Users/maasa/.codex/skills`
- Plugin Skill surfaces under `C:/Users/maasa/.codex/plugins/cache/*/skills`
- research_x repo Skills under `C:/Users/maasa/research_x/.agents/skills`
- Retired research_x operation Skills under
  `C:/Users/maasa/.codex/foundation/project_skills/research_x_retired_codex_ops`
- Codex foundation registry:
  `C:/Users/maasa/.codex/foundation/codex-foundation-registry.toml`
- Codex foundation Skill audit:
  `C:/Users/maasa/.codex/foundation/skill_quality_audit.toml`
- research_x Skill manifest:
  `C:/Users/maasa/research_x/.codex/skill_manifest.lock`

### Keep: Actual System Or Plugin Skills

These are actual callable Skills, but they are owned by system/runtime/plugins.
They are not source-intake outputs and should not be deleted as part of
source-origin cleanup.

| Skill surface | Classification | Evidence | Decision |
|---|---|---|---|
| `.system/imagegen` | actual_skill | System Skill directory | Keep; system image generation surface. |
| `.system/openai-docs` | actual_skill | System Skill directory | Keep; official OpenAI docs route. |
| `.system/plugin-creator` | actual_skill | System Skill directory | Keep; plugin creation owner. |
| `.system/skill-creator` | actual_skill | System Skill directory | Keep; Skill creation owner. |
| `.system/skill-installer` | actual_skill | System Skill directory | Keep; install owner. |
| Browser/Chrome/computer-use plugin Skills | actual_skill | Bundled plugin cache | Keep; runtime capabilities, not user source-derived Skills. |
| GitHub, Google Drive, Linear plugin Skills | actual_skill | Curated plugin cache | Keep; connector/plugin-owned surfaces. |
| Documents, PDF, Presentations, Spreadsheets, template-creator | actual_skill | Primary runtime plugin cache | Keep; artifact runtime capabilities. |
| `goal-setter` | actual_skill | Personal plugin cache and foundation registry | Keep; explicit goal intake owner. |
| `codex-chatgpt-control` | actual_skill | Personal plugin cache and router Skill | Keep; visible ChatGPT route, gated by explicit request. |
| `webwright` | actual_skill | Personal plugin cache | Keep; browser-task code-as-action tool. |

### Keep: Codex Foundation Personal Skills

These are actual Codex-wide Skills. Their current triggers are explicit or
bounded enough that deletion would remove useful owned behavior rather than
cleaning source clutter.

| Skill | Classification | Evidence | Decision |
|---|---|---|---|
| `basic-memory-cli` | actual_skill | Foundation registry `basic-memory`, installed local Skill | Keep; explicit local memory only. |
| `chatgpt-control-router` | actual_skill | Foundation registry and plugin bridge | Keep; thin router prevents hidden/API ChatGPT misuse. |
| `codex-fluent` | actual_skill | Foundation registry watchlist `context_and_session` | Keep; session hygiene, explicit use case. |
| `codex-retrospective` | actual_skill | Foundation registry `codex_operations` | Keep; explicit self-review periods. |
| `codex-strict-engineering` | deleted_source_derived_skill | Foundation registry now reference-only | Deleted; method guidance had been put into a Skill surface before any concrete imported implementation. |
| `context-budget` | actual_skill | Foundation registry and watchlist | Keep; cross-project context packs. |
| `context-handoff-export` | actual_skill | Foundation registry | Keep; factual handoff package owner. |
| `planning-files` | actual_skill | Foundation registry | Keep; long-running state files when needed. |
| `prompt-contract-testing` | source-derived_skill | Foundation registry, prompt-contract source family | Keep; deterministic local prompt/tool-boundary tests. |
| `skill-security-review` | actual_skill | Foundation registry and current goal route | Keep; source/Skill trust gate. |

### Deleted: Source-Derived Skill Surfaces

These were the clearest matches for the cleanup rule: an external source or
method idea had been turned into an always-visible Skill surface before the
source was adopted as code, plugin, fixture, bridge, or reference-only source.

| Skill | Classification | Evidence | Decision |
|---|---|---|---|
| `skillopt-sleep` | deleted_source_derived_skill | Foundation registry `skillopt`, imported source `vendor_imports/SkillOpt` | Deleted 2026-06-26; SkillOpt remains source material until code/plugin/fixture adoption is reviewed. |
| `codex-strict-engineering` | deleted_source_derived_skill | Foundation registry and Superpowers-like source family | Deleted 2026-06-26; generic method discipline belongs in project rules or an actual reviewed tool, not a source-inspired Skill. |
| `ian-xiaohei-illustrations` | deleted_source_derived_skill | Foundation registry, external creative style source | Deleted 2026-06-26; parent visual-planning boundary remains, upstream style source is reference-only. |
| `research-x-publishing-illustration` | retained_boundary_skill | Foundation registry, visual-output helper watchlist | Kept; it guards evidence/visual separation and is not a style-source clone. |

### Keep: research_x Repo Skills

The repo manifest currently lists only enabled repo-local Skills. External
source candidates were removed from the repo Skill manifest and live in source
locks/adoption registries instead. This is aligned with the current objective.

| Skill | Classification | Evidence | Decision |
|---|---|---|---|
| `research-x-decision-loop` | actual_skill | `.codex/skill_manifest.lock` enabled repo-local | Keep; decision sufficiency loop. |
| `research-x-doc-governance` | actual_skill | `.codex/skill_manifest.lock` enabled repo-local | Keep; Markdown/source-of-truth placement. |
| `research-x-implementation-plan-flow` | actual_skill | `.codex/skill_manifest.lock` enabled repo-local | Keep; converts candidate sets to gated local work. |
| `research-x-memory-workflow` | actual_skill | `.codex/skill_manifest.lock` enabled repo-local | Keep; evidence/source-bundle workflow. |
| `research-x-observability-review` | actual_skill | `.codex/skill_manifest.lock` enabled repo-local | Keep; run/evidence visibility. |
| `research-x-prompt-contract` | actual_skill | `.codex/skill_manifest.lock` enabled repo-local | Keep; prompt/tool contract tests. |
| `research-x-provider-gate` | actual_skill | `.codex/skill_manifest.lock` enabled repo-local | Keep; no-quota/provider gate. |
| `research-x-research-intake` | actual_skill | `.codex/skill_manifest.lock` enabled repo-local | Keep; source-candidate classification. |

### Retired Candidates

These are no longer active repo Skills and are already outside
`research_x/.agents/skills`. They are evidence of prior thinning, not active
surfaces to invoke.

| Retired Skill | Classification | Evidence | Deletion stance |
|---|---|---|---|
| `research-x-context-budget.20260625` | deleted_retired_candidate | `skill_quality_audit.toml` says `retired_do_not_enable` | Deleted physical retired Skill folder 2026-06-26; provenance row remains. |
| `research-x-goal-runner` | deleted_retired_candidate | `skill_quality_audit.toml` says `retired_do_not_enable` | Deleted physical retired Skill folder 2026-06-26; provenance row remains. |
| `research-x-parallel-review` | deleted_retired_candidate | `skill_quality_audit.toml` says `retired_do_not_enable` | Deleted physical retired Skill folder 2026-06-26; provenance row remains. |
| `research-x-skill-source-review` | deleted_retired_candidate | `skill_quality_audit.toml` says `retired_do_not_enable` | Deleted physical retired Skill folder 2026-06-26; provenance row remains. |
| `research-x-skillization-intake` | deleted_retired_candidate | `skill_quality_audit.toml` says `retired_do_not_enable` | Deleted physical retired Skill folder 2026-06-26; provenance row remains. |

### Duplicate Or Overbroad Findings

Current cleanup resolves the clearest active source-derived Skill noise. Remaining
items below are retained because they are plugin bridges, system/plugin cache, or
boundary Skills with a real guard role.

| Surface | Classification | Evidence | Current decision |
|---|---|---|---|
| `research-x-publishing-illustration` + `ian-xiaohei-illustrations` | resolved_duplicate | Style adapter was the narrower source-derived surface | Deleted `ian-xiaohei`; retained parent evidence/visual boundary Skill. |
| `chatgpt-control-router` + `codex-chatgpt-control` | duplicate_or_overbroad watch | Router points to plugin and forbids ordinary search/API use | Keep both; router is a safety bridge, not a duplicate implementation. |
| `codex-strict-engineering` + normal engineering behavior | resolved_overbroad | Project AGENTS and default Codex engineering rules already own this | Deleted source-inspired generic method Skill. |
| Plugin cache version duplicates, such as `chrome/latest` | not_user_owned_cache | Plugin cache layout | Do not delete manually from source-origin cleanup. |

## Deletion Plan

Active large deletion is justified only for surfaces that match the user's
cleanup rule: external source first became a Skill-shaped note instead of being
adopted as code, plugin, fixture, bridge, or reference-only source. The current
cleanup path is:

1. Keep all active system/plugin Skills and all eight current research_x repo
   Skills.
2. Keep Codex foundation Skills that actively guard behavior boundaries:
   source/security review, provider gates, context/handoff, memory, ChatGPT
   routing, prompt contract testing, and visual evidence separation.
3. Delete source-derived Skill surfaces that merely held external-source
   concepts without a concrete local integration:
   `skillopt-sleep`, `codex-strict-engineering`, and
   `ian-xiaohei-illustrations`.
4. Delete the five already-retired research_x operation Skill folders from the
   archive path after preserving their names and decisions in this inventory and
   `skill_quality_audit.toml`.
5. Never delete source locks, adoption registries, `_foundation_sources`,
   historical consultation captures, or WBS archives as part of Skill cleanup.

The key correction from the source-origin review is conceptual: an external
paper, article, GitHub repo, provider API, or X post should first be evaluated
as a finished outside object and then routed to `use_as_is`, `bridge`,
`code_import`, `fixture_only`, `reference_only`, `provider_gated`, or `retire`.
Only recurring Codex behavior with a distinct trigger and ongoing value should
become an actual Skill.
