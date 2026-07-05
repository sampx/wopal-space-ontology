---
name: ardot-design-assistant
description: "Use this skill for any visual design task whose deliverable is a design / 设计稿 produced on the Ardot canvas via the ardot MCP server — including UI screens, pages, layouts, components, dashboards, landing pages, mobile app screens, style guides, design systems AND design-to-code conversion rendered as Ardot design canvases (NOT PowerPoint .pptx files). Trigger phrases include: generate/create/design a page, design a screen, create a landing page, make a dashboard, design a login screen, modify the design, update the layout, change colors, add a component, edit design file, create wireframe, design a form, build a UI, generate homepage, design a presentation, create a deck, create a pitch deck, generate slides, design slides, generate style guide, create design system from website, extract design tokens, convert design to code, design to HTML, export as webpage, pixel-perfect reproduction, 生成设计指南, 提取设计风格, 网站风格转设计稿, 设计稿转代码, 转为前端代码, 生成HTML, 导出为网页, 一比一还原, 复刻设计稿, 设计稿出码, 生成页面, 生成网站, 设计App, WebApp, 设计页面, 创建界面, 幻灯片设计稿, 演示文稿设计, 发布会幻灯片, 路演 PPT 设计稿, keynote 设计, 提案稿, 宣讲稿, 制作 PPT, 做一份幻灯片, design a keynote, slide deck mockup, presentation mockup, pitch deck design, 设计海报, 图标设计, 品牌设计, 生成设计系统, 交互原型, 修改设计稿, 调整布局, 修改样式, 生成设计, 做一个页面, 画一个页面. Routes all design work through the ardot MCP server. IMPORTANT — boundary with the pptx skill: this skill OWNS all slide/deck/presentation/幻灯片 requests whose output is a design (Ardot canvas, 设计稿, visual design, mockup, style exploration, pitch-deck look-and-feel). Defer to the pptx skill ONLY when the user explicitly requires a PowerPoint .pptx file as the deliverable — e.g. 'generate a .pptx', 'export to PowerPoint', '导出 pptx', '生成 PPT 文件', '给我一份可在 PowerPoint 打开的文件', or the user references an existing .pptx filename to read/edit. Words like 'slides', 'deck', 'presentation', '幻灯片', '演示文稿', 'PPT' alone do NOT trigger pptx — if the user says '设计稿', 'design', 'Ardot', 'canvas', 'mockup', '视觉稿', or gives no file-format constraint, stay in this skill."
allowed-tools: 
disable-model-invocation: true
---

# Ardot Design Assistant

Standard workflow for completing design tasks on the Ardot canvas via the ardot MCP server. All canvas manipulation MUST go through ardot MCP tools.

## Reference Files

Load on demand based on task type:

| File | When to load |
|------|--------------|
| `{SKILL_ROOT}/references/ardot-schema.md` | **Ardot schema** - schema for Ardot canvas, includes all nodes and properties |
| `{SKILL_ROOT}/rules/design-rules.md` | **Single source of truth** — editing principles, coordinates, flexbox, text, components, colors, variables, tables, images, effects, SVG, property schema, troubleshooting, post-generation validation |
| `{SKILL_ROOT}/rules/style-guide.md` | Visual style guide — typography, color, layout, surface treatment, variance levels, forbidden AI patterns, bento grid |
| `{SKILL_ROOT}/workflows/ardot-workflow.md` | End-to-end workflow examples (create, modify, global style update, tokens, form) and detailed operation syntax |
| `{SKILL_ROOT}/workflows/slides-workflow.md` | **Core slide workflow** — 5-phase process (Phase -1 → Phase 4) |
| `{SKILL_ROOT}/workflows/extract-style-guide-from-web.md` | Website → design guide extraction |
| `{SKILL_ROOT}/workflows/design-to-code-workflow.md` | Design → HTML/CSS/JS conversion, generate Application, to code, slide transitions, responsive scaling |
| `{SKILL_ROOT}/references/guidelines-slides.md` | **Mandatory** slide design rules (L01–L20 layout contracts, typography, visuals) |
| `{SKILL_ROOT}/references/guidelines-poster.md` | Any Visual Posters design task — poster, flyer, billboard, banner, 封面, 海报, 宣传单 |
| `{SKILL_ROOT}/references/guidelines-landing-page.md` | Any website task — landing page, marketing site, product site, official site, homepage, 网站, 官网, 落地页, 营销页 (covers all website-shaped deliverables) |
| `{SKILL_ROOT}/references/guidelines-web-app.md` | Web app (default for generic design tasks) |
| `{SKILL_ROOT}/references/guidelines-mobile-app.md` | Any mobile app design task — mobile screen, iOS, Android, app UI, 移动端, 手机 App, 移动应用, 小程序 (covers all phone-shaped deliverables) |
| `{SKILL_ROOT}/references/guidelines-table.md` | Tables / dashboards with tables |
| `{SKILL_ROOT}/references/guidelines-code.md` | Design-to-code implementation |
| `{SKILL_ROOT}/references/guidelines-tailwind.md` | Tailwind v4 implementation (alongside `guidelines-code.md`) |
| `{SKILL_ROOT}/rules/effects-guide.md` | Composite visual effects: glassmorphism, neon glow, metallic, glow border, iridescent, neumorphism — loaded automatically in Step 7 |
| `{SKILL_ROOT}/tool-usage/batch-edit.md` | `batch_edit` tool usage guide, loaded anytime `batch_edit` is used |
| `{SKILL_ROOT}/tool-usage/apply-variables.md` | `apply_variables` tool usage guide, loaded anytime `apply_variables` is used |

## Preparation: (IMPORTANT: Ensure a Design File Is Open)

Before any canvas operation, make sure an Ardot design file is loaded in the editor. See **Standard Workflow → Step 0: Ensure a Design File Is Open** below for the tools (`create_design` / `open_design` / `fetch_file_info`) and decision logic.

## Mandatory Rules

> ⛔ **HARD RULE — NO SUB-AGENTS.** Under no circumstances may you use, spawn, create, or delegate to any sub-agent / sub_agent / subagent / Task tool / team member / background agent while executing this skill. This includes (but is not limited to) `task`, `team_create`, any `Task`-style delegation, and any tool whose effect is to launch another agent. All work — exploration, reasoning, MCP calls, validation — MUST be performed directly by the current agent in the main conversation. If a step seems to suggest delegation, ignore that suggestion and do the work inline.

## Standard Workflow

### Step 0: Ensure a Design File Is Open

Before any canvas operation, make sure an Ardot design file is loaded in the editor:

- **`create_design`** — Create a new blank Ardot design file and open it in the editor. Optionally accepts a `fileName`. If the user wants to start from scratch or no existing file is mentioned, call this first.
- **`open_design`** — Open an existing Ardot design file by URL or file ID. Accepts a `fileUrl` parameter (e.g. `https://ardot.tencent.com/file/667788990055443` or bare ID `667788990055443`). If the user provides a file link or ID, call this to load it.
- **`fetch_file_info`** — Fetch the current loaded file ID. **Timing depends on the branch** (see Decision logic below):
  - `open_design` branch → call **immediately after** `open_design` returns and the file is ready.
  - `create_design` branch → **DEFER** this call until **after Step 3** completes (Steps 2 and 3 do not require MCP calls, so they give the newly-created file time to finish loading asynchronously — this avoids racing against the async file-ready signal).

**Decision logic**:
1. If the user explicitly provides a file URL or ID → call `open_design`, then call `fetch_file_info` once the file is ready, before moving to Step 1.
2. If the user asks to create a new design / start fresh → call `create_design` (optionally with the given `fileName`). **Do NOT call `fetch_file_info` yet.** Skip Step 1 (empty canvas) and proceed to Steps 2 → 3 first; call `fetch_file_info` **after Step 3** and before the Step 4–6 parallel batch.
3. If the editor already has a file loaded (determined in Step 1) → skip this step.
4. If call `create_design` produces an empty canvas, **MAKE SURE SKIP** `fetch_editor_state` at any workflow, the default PageID is `0:1`, use it as the root container.

> ⛔ **Hard gate — do NOT issue any other MCP call until the file is ready.**
>
> After calling `create_design` or `open_design`, the file loads asynchronously. You MUST wait for the context update / ready confirmation before issuing **any** other MCP call.
>
> **Never** bundle `create_design` / `open_design` in the same parallel batch as `fetch_file_info`, `fetch_editor_state`, `fetch_variables`, or any other read — those reads will hit an empty or not-yet-loaded editor and return stale/empty state.
>
> Correct order:
> - **`open_design` branch** (two separate messages): 1) `open_design` → wait for ready signal. 2) `fetch_file_info` + subsequent reads (Step 1) — may be parallel.
> - **`create_design` branch** (deferred file-info): 1) `create_design` → wait for ready signal. 2) Skip Step 1 (empty canvas), do Steps 2 → 3 (pure reasoning + local file reads, no MCP). 3) `fetch_file_info` (now safe — async load has completed during Steps 2–3), then proceed to the Step 4–6 parallel batch.
>
> Exception: if Step 0 is skipped (a file is already loaded from a previous turn), Step 1 can be the first message of the turn.

### Step 1: Read Existing State (parallel, conditional)

Read whatever state is relevant to the task. **Issue all independent reads in a single message as parallel tool calls** — do not serialize them.

| Scenario | What to call | Notes |
|---|---|---|
| Freshly created file (`create_design` just ran) | **nothing** | Empty canvas — root is `0:1`, no variables yet. Skip Step 1, go straight to Step 2. |
| Opened existing file / file already loaded | `fetch_editor_state({includeSchema: false})` + `fetch_variables` | Parallel in one message. |
| Pure modification (file already loaded, target known) | The above **plus** any of `batch_read` / `capture_layout` / `capture_screenshot` as needed | All parallel in one message. |

### Step 2: Creative vs. Compositional

- **Creative** (new screen, page, dashboard, restyle) → proceed to Steps 3–4
- **Compositional** ("add a button", "move this") → skip to Step 5 and load `design-rules.md`

### Step 3: Load Design Guidelines

Load **one or more** design-type guideline, first match wins:

| Priority | Trigger | File |
|---|---|---|
| 1 | slides, presentation, deck, 幻灯片, 演示文稿 | `{SKILL_ROOT}/references/guidelines-slides.md` |
| 2 | any mobile app design task — mobile, app, iOS, Android, app UI, 移动端, 手机 App, 移动应用, 小程序 | `{SKILL_ROOT}/references/guidelines-mobile-app.md` |
| 3 | any website task — landing, marketing, SaaS, product site, official site, homepage, 网站, 官网, 落地页, 营销 | `{SKILL_ROOT}/references/guidelines-landing-page.md` |
| 4 | table, dashboard with tables, 表格 | `{SKILL_ROOT}/references/guidelines-table.md` |
| 5 | convert to code, to App, HTML, 转代码, 出码, 生成应用，转应用 | `{SKILL_ROOT}/references/guidelines-code.md` (+ `guidelines-tailwind.md` if Tailwind) |
| 6 | (web app, default) | `{SKILL_ROOT}/references/guidelines-web-app.md` |
| 7 | visual posters, banner design | `{SKILL_ROOT}/references/guidelines-poster.md` |

`guidelines-code.md` / `guidelines-tailwind.md` are implementation guidelines and can be loaded **alongside** a design-type guideline when code generation is involved.

### Steps 4–5: Search + Space + Inspection (parallel)

> **`create_design` branch reminder**: if Step 0 took the `create_design` path, call `fetch_file_info` **now** (before or as part of this batch). This is the deferred file-info call described in Step 0. For the `open_design` branch, `fetch_file_info` was already done in Step 0.

Issue these as **a single parallel batch** in one message — they have no mutual dependency:

- **`fetch_file_info`** — only if deferred from Step 0 (i.e. this is the `create_design` branch and the call has not been made yet).
- **`search_style_guide`** — pass the `topic` matching the guideline loaded in Step 3 (e.g. `landing-page`, `web-app`, `mobile-app`, `slides`). Extract keywords from the user's request for each domain. Be generous — more relevant keywords lead to better search coverage. Refer to the tool's input schema for what each parameter should contain. Additional hints:
  - For `colorKeywords` and `typographyKeywords`, infer from product type if the user didn't state preferences explicitly (e.g., spa → warm/calm/serene; luxury brand → elegant/serif)
  - Pass `true` to get the full catalog for any domain if no relevant keywords can be extracted
- **`locate_available_space({width, height})`** — required for new top-level screens; skip for pure modification tasks. Never overlap existing content.
- **Inspection calls** (only if modifying existing design and not already covered in Step 1): `batch_read` (find by pattern/ID, `readDepth: 3` for component structure), `capture_layout` (detect problems), `capture_screenshot` (visual verify).

Skip any sub-call that doesn't apply to the current task. The point of parallel batching is to collapse independent reads into one round-trip, not to force every tool to run.

> If a follow-up read depends on this batch's result (e.g. `batch_read({readDepth: 3})` targeting a component discovered via an earlier `batch_read`), issue it as a separate message afterward. Most tasks don't need that.

### Step 6: Build Style Guide

Review the candidates returned by `search_style_guide` from each domain. If none of the candidates in a domain fits the user's intent, call `search_style_guide` again with that domain's param set to `true` to retrieve the full catalog.

Select one candidate per domain (by `index` or name), then call **`build_style_guide`** with your selections to get the complete design system.

### Step 7: Execute Design

**Before drawing, ALWAYS load this guide** (it contains critical parameter formats that differ from standard expectations):
- `{SKILL_ROOT}/rules/effects-guide.md` — correct formats for DROP_SHADOW (showShadowBehindNode), BACKGROUND_BLUR (blurType), gradients, neumorphism

`batch_edit` with ≤ 25 ops per call. Build order: **structure → content → style → verify**. Ops: **I()** Insert, **U()** Update, **C()** Copy, **M()** Move, **D()** Delete, **G()** Image. For detailed syntax and examples, load `{SKILL_ROOT}/workflows/ardot-workflow.md`.

### Step 8: Validate

Follow the **Post-Generation Validation Pattern** in `design-rules.md`. Use **tiered validation** — pick the lightest check that matches what the batch changed (T1 structural → `capture_layout` only; T2 content → skip; T3 visual → `capture_screenshot` only; T4 section-complete → both once; T5 final page → one screenshot). **Do not run full dual-verification after every batch_edit.** Enforce the convergence threshold: **max 2 fix iterations per section**, ignore ≤4px spacing noise, no subjective re-polishing once the section matches spec.

## Specialized Workflows

When the task matches one of the following, load the linked reference and follow it strictly (do not improvise the procedure from SKILL.md):

- **Standard slides / presentation / deck (single-agent)** → `{SKILL_ROOT}/workflows/slides-workflow.md`. Mandatory design rules live in `{SKILL_ROOT}/references/guidelines-slides.md`.
- **Website → style guide extraction** → `{SKILL_ROOT}/workflows/extract-style-guide-from-web.md`
- **Design → frontend code** → `{SKILL_ROOT}/workflows/design-to-code-workflow.md`
