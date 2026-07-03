# Slides Creation Workflow

This is the end-to-end workflow for creating presentation decks on the ardot canvas. Follow the phases in order — do NOT skip phases or reorder steps.

## Execution Protocol (read first, applies to entire workflow)

1. **Sequential Lock**: Phases -1→3 are strictly sequential. You MUST NOT
   start Phase X+1 until Phase X's Postconditions are all satisfied.
2. **State Echo**: At the start of each Phase, output a one-line status:
   `[Phase X.Y] <name> — preconditions: PASS/FAIL`
3. **No Silent Skips**: If you intentionally skip a step (e.g., 1.2 for
   fresh files), explicitly state the skip reason.
4. **No Fabrication**: Never invent values that should come from a tool
   call (palette, file ID, slide count). If a tool call is missing, halt.

## Table of Contents

- [Phase -1: Requirement Clarification](#phase--1-requirement-clarification) — confirm sources, scenario, style, slide count, generate `slide-outline.md`
- [Phase 0: Preparation](#phase-0-preparation) — read references, fetch state, guidelines, style guide
- [Phase 1: Planning](#phase-1-planning) — slide count, outline, canvas grid
- [Phase 2: Canvas Setup](#phase-2-canvas-setup) — locate space, create all slides
- [Phase 3: Slide Generation](#phase-3-slide-generation) — per-slide generate → layout check → fix
- [Phase 4: Final Review](#phase-4-final-review) — holistic visual pass

---

## Phase -1: Requirement Clarification (MANDATORY)

Before any preparation or canvas operation, you **MUST** confirm the user's requirements through a structured Q&A. Do NOT proceed to Phase 0 until all four dimensions below are confirmed and the outline file is generated.

The goal of this phase is to (1) eliminate ambiguity about content sources, scenario, style, and deck size, and (2) produce a persistent outline file (`slide-outline.md`) that serves as the single source of truth for Phase 1–4.

### Mandatory Rules

1. **MUST use the AskUserQuestion tool** — never output the questions as plain text.
2. **Ask all questions in a single call**: content source / use case / visual style / page count / (...).
3. **No default fallbacks** — unless the user explicitly says "you decide", any unanswered item blocks entry into Phase 0; do NOT silently fall back to "use Free creation if unsure".
4. **Style options MUST be tailored to the topic** — do not directly reuse the 8 generic archetypes; extract keywords from the topic and offer 5 concrete, topic-specific directions.
5. **After the AskUserQuestion call**, supplement with a plain-text note describing your assumptions/recommendation rationale (for transparency), then wait for the user's reply.

### -1.1 Question: Confirm Content Source (single-select)

Ask the user which content-source mode they want. Present these three options explicitly:
1. **Provided materials** — the user will supply existing content (text, links, files, images, data). If chosen, request the materials immediately and wait for them before continuing.
2. **Web research** — the assistant performs online research to gather facts, data, and references for the topic. If chosen, plan the search queries here (do not execute yet — execution happens in Phase 0/1 alongside style guide fetch).
3. **Free creation** — the assistant generates content based on its own knowledge and the topic alone, without external sources.

Record the chosen mode. If the user is unsure, default to **Free creation** but explicitly state the assumption.

### -1.2 Question: Confirm Scenario (MANDATORY)

Ask the user what scenario the deck will be used in (e.g., investor pitch, internal review, sales enablement, academic lecture, product launch keynote, training, conference talk). Scenario directly affects tone, density, and required slide roles (e.g., a pitch deck needs Problem/Solution/Market/Ask; a training deck needs Objectives/Modules/Quiz).

Record the scenario as a short phrase.

### -1.3 Question: Recommend & Confirm Style (MANDATORY)

Based on the deck topic and scenario, recommend **exactly 5 styles** that fit. For each, give a one-line description covering palette feel, typography character, and decorative direction. Examples of style archetypes you may draw from (do not always reuse the same five — tailor to topic):
- Minimal Editorial — neutral palette, generous whitespace, large serif/sans titles
- Bold Tech — saturated gradients (blue/purple/cyan), geometric shapes, mono accents
- Warm Corporate — earth tones, rounded sans, soft shadows
- Data-Dense Analytical — dark navy background, high-contrast charts, compact grid
- Playful Creative — vibrant multi-hue, hand-drawn motifs, irregular shapes
- Luxury Premium — deep dark + gold accents, thin serif, sparse decoration
- Eco/Organic — green/beige gradients, leaf/wave motifs, humanist sans
- Cyberpunk Neon — black + neon pink/cyan, glitch motifs, mono display

Present the 5 picks as a numbered list and ask the user to choose one (or to describe a custom variant). Record the final style choice and a 2–3 sentence elaboration of palette / type / motif direction — this will guide tag selection in Phase 0.4.

### -1.4 Question: Confirm Slide Count (Volume) (MANDATORY)

Ask the user how many slides they want. If unsure, recommend a default based on scenario:
- Pitch deck: 10–12
- Internal review: 6–8
- Keynote: 15–20
- Training module: 8–15
- Quick share / status: 5–7

Record the final count `N`. Confirm `N` is between 3 and 30; outside that range, double-check with the user.

### -1.5 Generate `slide-outline.md`

Synthesize the four answers into an outline file and **save it to the project workspace** (alongside the design file or in the conversation working directory) as `slide-outline.md`. This file is referenced in Phase 1.1 and Phase 3.1 — do **not** skip generation.

The file MUST follow this structure exactly:

```markdown
# Slide Outline

## Meta
- Topic: <one-sentence topic>
- Scenario: <from -1.2>
- Content Source: <provided | web research | free creation>
- Style: <chosen style name> — <2–3 sentence palette/type/motif direction>
- Slide Count: <N>
- Generated At: <ISO timestamp>

## Source Materials
<If "provided": list/summarize the user-supplied materials.
If "web research": list the planned search queries and target source types.
If "free creation": write "N/A — generated from topic knowledge.">

## Slide-by-Slide Outline
1. **Slide 1 — <Role: Cover>** — <one-line message> | Layout hint: L?? | Image provided: yes/no | Chart: yes/no
2. **Slide 2 — <Role: Agenda>** — <one-line message> | Layout hint: L?? | Image provided: yes/no | Chart: yes/no
... (continue for all N slides)

## Visual Rhythm Notes
- Chart-bearing slides at positions: <e.g., 4, 6>
- Slides are viewed on large screens, often from a distance. Small text is unreadable. Every text element must be sized generously and fill its container space rather than floating in emptiness.
- Slides should feel visually rich and layered, not like text pasted on rectangles. Decorative elements add polish, and SVG charts communicate data far more effectively than text or numbers alone.
```

Show the generated outline to the user and ask for explicit confirmation ("approve / revise"). If the user requests changes, update the file and re-confirm. **Only after explicit approval may you advance to Phase 0.**

**Output of Phase -1**: an approved `slide-outline.md` file containing topic, scenario, content source, style direction, slide count, and per-slide roles. This file is the contract for the rest of the workflow.

---

## Phase 0: Preparation

Before doing anything on the canvas, load all required knowledge and context. This phase is non-negotiable — skipping it will produce low-quality slides that violate design rules.

### 0.0 Ensure Design File Is Open

Before any canvas operation, make sure an Ardot design file is loaded:
- **`create_design`** — Create a new blank file and open it. Optionally accepts a `fileName`.
- **`open_design`** — Open an existing file by URL or file ID.
- **`fetch_file_info`** — Fetch the current loaded file ID.
  - `open_design` branch → call **immediately after** `open_design` returns and the file is ready (before 0.2).
  - `create_design` branch → **DEFER** until paired with `0.4`'s MCP batch. Reasons: 0.1 and 0.3 are local file reads (no MCP), so they cover the async load window; and `0.2 fetch_editor_state` is skipped for fresh files (see below).
- If the editor already has a file loaded (determined in Step 0.2) → skip this step.

### 0.1 Load Reference Knowledge (read these files if not already loaded)

- `{SKILL_ROOT}/rules/design-rules.md` — ardot design constraints (flexbox, text, components, property reference)
- `{SKILL_ROOT}/workflows/ardot-workflow.md` — `batch_edit` operation syntax, binding rules, full tool parameters

### 0.2 Fetch Editor State

**Skip this step for fresh `create_design` files** — empty canvas, root is `0:1`, no variables, no components yet. There is nothing to fetch.

Otherwise (opened existing file / file already loaded), call `fetch_editor_state` with `includeSchema: false` to get:
- Current page ID
- Active selection
- Available components in the file

### 0.3 Load Slide Design Guidelines

Load `{SKILL_ROOT}/references/guidelines-slides.md` — this is the **authoritative source** for all slide design rules, including:
- **Rule 1**: Large Typography (Title ≥56px, Body ≥28px, no text below 22px)
- **Rule 2**: Rich Backgrounds (gradients + decorative patterns, no pure white/black)
- **Rule 3**: Decorative Elements & SVG Data Charts (≥2 decorative elements per slide)
- 20 Layout Contracts (L01-L20) for different slide types
- Color, imagery, and content density guidelines

These rules are enforced throughout Phase 1-4. References to "Rule 1/2/3" in later phases point to this file.

### 0.4 Fetch Visual Style Inspiration

1. Call `search_style_guide` with `topic: "slides"` and keywords extracted from the deck's topic and tone. **For the `create_design` branch, issue `fetch_file_info` in the same parallel batch** (this is the deferred call from 0.0 — safe now because 0.1/0.3 ran in between).
2. Review the returned candidates, select best fit per domain
3. Call `build_style_guide` with your selections to get the complete design system
4. If the returned style does not fit the topic or contradicts the approved style, call `search_style_guide` again with adjusted keywords or `true` for full catalog, or make your own style guide

**Output of Phase 0**: a concrete color palette, type scale, spacing tokens, and decorative motif to apply consistently across all slides.

## Phase 1: Planning

Plan the deck before touching the canvas. Do NOT start creating slides until planning is complete.

### 1.1 Determine Slide Count & Outline

**Read `slide-outline.md` (generated in Phase -1.5) — it is the authoritative source for slide count, roles, and per-slide messages.** Do not invent a new count or re-decide roles here.

From the outline file, extract:
- Total slide count `N` (Meta → Slide Count)
- Per-slide role and one-line message (Slide-by-Slide Outline)
- Dark accent slide positions (Visual Rhythm Notes) — must satisfy guidelines-slides.md Rule 2 (at least 1–2 dark slides)
- Chart-bearing slide positions (Visual Rhythm Notes) — must align with guidelines-slides.md Rule 3

If the outline lacks any of the above, return to Phase -1.5 and amend it before proceeding.

### 1.2 Plan Canvas Grid Layout

Each slide is **1920 × 1080** px. Lay slides out on the canvas in a grid:
- **Max 5 slides per row**
- Horizontal gap between slides: **100px**
- Vertical gap between rows: **100px**

For N slides:
- `rows = ceil(N / 5)`
- `totalWidth = min(N, 5) × 1920 + (min(N, 5) - 1) × 100`
- `totalHeight = rows × 1080 + (rows - 1) × 100`

---

## Phase 2: Canvas Setup (MUST READ AND FOLLOW)

### 2.1 Locate Available Space

Call `locate_available_space` with `totalWidth` and `totalHeight` from Phase 1.2. Record the returned `space.x` and `space.y` as the grid origin.

### 2.2 Create All Slides in One Batch (MUST READ AND FOLLOW)

Use `batch_edit` (≤25 ops per call; split into multiple calls if N > 25) to create all slides up front.

For slide at grid position `(row, col)` where `row = floor(i / 5)` and `col = i % 5`:
- `x = space.x + col × (1920 + 100)`
- `y = space.y + row × (1080 + 100)`

Each slide node must set:
- `width: 1920, height: 1080`
- `clipsContent: true`
- Meaningful `name` (e.g., `"Slide 3 - Market Size"`)
- Base `fill` from the style guide (avoid pure white/black — see guidelines-slides.md Rule 2)

Example:
```javascript
slide1=I(document, {type: "slide", name: "Slide 1 - Cover", width: 1920, height: 1080, clipsContent: true, x: X1, y: Y1, fills: [/* gradient from style guide */]})
slide2=I(document, {type: "slide", name: "Slide 2 - Agenda", width: 1920, height: 1080, clipsContent: true, x: X2, y: Y2, fills: [/* gradient from style guide */]})
// ... continue for all N slides
```

**Do NOT populate slide content in this phase.** Only create the empty slides.
**Don't use `type: "frame"`, use `type: "slide"` to create root slides.**

---

## Phase 3: Slide Generation

Generate slides **one at a time, sequentially**. For each slide `i` from 1 to N, run this sub-loop:

### 3.1 Generate Slide Content

Before generating slide `i`, re-read its row in `slide-outline.md` (role, one-line message, layout hint, dark/chart flags) and treat it as the spec for this slide.

Call `batch_edit` (≤25 ops) to add content into slide `i`'s frame. Build order:
1. **Background layer** — gradient fill + decorative pattern (Rule 2)
2. **Structure** — title area, content area, footer/page number
3. **Content** — titles, body text, data elements (with font sizes from Rule 1)
4. **Decoration** — 2–3 decorative elements per slide (Rule 3)
5. **Charts** — if data is present, inline SVG chart (Rule 3)

If a single slide needs more than 25 ops, split into multiple sequential `batch_edit` calls on the same slide.

### 3.2 Verify & Fix

1. `capture_layout` on slide `i` with `problemsOnly: true` — check overlapping, clipping, misalignment
2. If issues found → `batch_edit` corrections → re-run 1 + 2

Only advance to slide `i+1` after the current slide passes both checks.
**IMPORTANT: Do not call `capture_screenshot` before Phase 4.**
---

## Phase 4: Final Review

After all N slides have passed their per-slide checks:

### 4.1 Deck-Level Screenshot

Screenshot each slide one more time to compare neighbors side-by-side. Verify:
- Consistent palette across all slides (Rule 2)
- Dark accent slides appear at planned positions
- Typography hierarchy is uniform (same title/body sizes across similar slide types)

### 4.2 Final Fixes

For any cross-slide inconsistencies, issue fix-up `batch_edit` calls and re-screenshot. Stop only when the full deck is visually cohesive.
