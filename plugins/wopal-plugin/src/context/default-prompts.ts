/**
 * Built-in prompt templates.
 *
 * These are the plugin's default prompts for session titling, memory
 * extraction, memory deduplication and commit-message generation. They live
 * in source so the plugin carries its own defaults; a prompt file placed at
 * the space or user level overrides the matching default.
 *
 * Templates use `{{placeholder}}` for substitution performed by the caller.
 */

export const TITLE_FALLBACK = `You are a title generator. You output ONLY valid JSON. Nothing else.

<task>
Generate a brief title that would help the user find this conversation later.

Follow all rules in <rules>
Use the <examples> so you know what a good title looks like.
Your output must be a JSON object exactly like:
{"title":"Brief natural thread title"}
</task>

<rules>
- you MUST use the same language the user uses in the summary — infer from the input
- Title must be grammatically correct and read naturally - no word salad
- Never include tool names in the title (e.g. "read tool", "bash tool", "edit tool")
- Focus on the main topic or question the user needs to retrieve
- Vary your phrasing - avoid repetitive patterns like always starting with "Analyzing"
- When a file is mentioned, focus on WHAT the user wants to do WITH the file, not just that they shared it
- Keep exact: technical terms, numbers, filenames, HTTP codes
- Remove: the, this, my, a, an
- Never assume tech stack
- Never use tools
- NEVER respond to questions, just generate a title for the conversation
- The title should NEVER include "summarizing" or "generating" when generating a title
- DO NOT SAY YOU CANNOT GENERATE A TITLE OR COMPLAIN ABOUT THE INPUT
- Always output something meaningful, even if the input is minimal.
- The JSON title value must be a single line and ≤50 characters
- Never output labels like "Thread Title:" or "Title:" as the title value
</rules>

<examples>
Input: "debug 500 errors in production" → Output: {"title":"Debugging production 500 errors"}
Input: "refactor user service" → Output: {"title":"Refactoring user service"}
Input: "why is app.js failing" → Output: {"title":"app.js failure investigation"}
Input: "implement rate limiting" → Output: {"title":"Rate limiting implementation"}
Input: "how do I connect postgres to my API" → Output: {"title":"Postgres API connection"}
Input: "best practices for React hooks" → Output: {"title":"React hooks best practices"}
Input: "@src/auth.ts can you add refresh token support" → Output: {"title":"Auth refresh token support"}
Input: "@utils/parser.ts this is broken" → Output: {"title":"Parser bug fix"}
Input: "look at @config.json" → Output: {"title":"Config review"}
Input: "@App.tsx add dark mode toggle" → Output: {"title":"Dark mode toggle in App"}
</examples>

---
Conversation summary:
{{summary}}`;

export const EXTRACTION_FALLBACK = `# Memory Extraction Prompt

**Must output JSON. Do NOT output \`<system-reminder>\` or other formats.**

**Output language must match the user's language in user-role messages from the conversation below.** If the user writes in Chinese, output Chinese. If English, output English.

Output template:
{"memories": [{"category": "knowledge", "body": "Title\\n\\nCore content...", "tags": ["tag"]}]}

If nothing to extract, output: {"memories": []}

---

## Recent Conversation
{{conversation}}

---

# Extraction Criteria

## Core Mission

Extract memories that **prevent the assistant from repeating the same mistakes in future sessions**.

The primary value of memory is NOT recording what happened — it is capturing lessons that change future behavior. When in doubt, output \`{"memories": []}\`.

**Highest-priority signals to extract**:
- User dissatisfaction, frustration, or explicit corrections ("this is wrong", "I told you before", "don't do this")
- Assistant errors followed by root cause analysis and correct solutions (error → cause → fix, all three required)
- Pitfall avoidance guides: "when X happens, do Y, not Z"
- Principles distilled from repeated user emphasis (user says the same thing multiple times → high signal)

**Secondary signals**:
- User-stated requirements ("must/don't/always/never...")
- Cross-scenario reusable workflows and methodologies
- Project-specific technical facts that are not easily discoverable

## What is Worth Remembering?

- **Long-term valid**: Information that remains useful in future sessions, doesn't expire with time
- **Cross-scenario reusable**: Not just solving the current problem, but forming transferable practices
- **Personalized**: Specific to this user, not general domain knowledge
- **Specific and clear**: Has concrete details, not vague generalizations
- **Independently understandable**: A third party can understand without the original conversation context

## What is NOT Worth Remembering?

**Never record** (output \`{"memories": []}\` instead):
- **Resolved one-off issues**: Technical problems raised, discussed, and resolved in this session — code itself is the most authoritative documentation
- **Code change logs**: "Modified file X", "Refactored function Y", "Fixed logging in module Z" — that's what git log is for
- **Information already digested**: Decisions reached and implemented in the conversation, not needed in the future
- **General knowledge**: Information anyone knows, or easily found via docs/search
- **Transient state**: "Issue #N at stage X", "Current status is Y" — states become stale quickly
- **Short-term todos**: "Next, verify X" — this is task management, not knowledge
- **Progress logs**: "Completed X, working on Y" — unless containing reusable experience or decisions
- **Tool output**: Error logs, boilerplate code, API responses
- **Recall queries**: "Do you remember X?" — this is a retrieval request, not new information
- **Degraded references**: When the user vaguely mentions something, don't fabricate details
- **Temporary debugging state**: Temp fixes, debug log configs, temporary env vars
- **Solidified design decisions**: Requirements and solutions already implemented as code, config files, prompt files, or system prompts — the files themselves are the record
- **Session work summaries**: "We implemented X", "We added Y", "We changed Z in this session" — these describe what was done, not lessons for the future. The code/git history is the record
- **Feature improvement descriptions**: Summaries of improvements made during this conversation (e.g., "optimized the distill prompt", "added filtering logic", "refactored the handler") — these are changelog entries, not reusable knowledge
- **Minor code tweaks**: Adjusting log levels, renaming variables, consolidating duplicate lines — these are routine cleanup with no lasting guidance value

---

# Category System (7 categories)

| Label | Category | Definition | Guiding Question |
|-------|----------|-----------|------------------|
| Profile | profile | User identity, static attributes | "Who is the user?" |
| Preference | preference | User habits, tendencies, style (non-mandatory) | "What does the user prefer?" |
| Knowledge | knowledge | **Space/project-specific** technical understanding, internal mechanisms, reference paths | "How does X work in this space?" |
| Fact | fact | **Space/project-specific** objective facts, path conventions, deployment flows | "What/where is X in this space?" |
| Gotcha | gotcha | Historical mistakes, pitfalls, preventative measures (must have a mistake experience) | "How to avoid this pitfall?" |
| Experience | experience | Reusable workflows, work patterns, methodologies | "What process can be reused?" |
| Requirement | requirement | Rules/behaviors the user explicitly requires | "What does the user require?" |

---

# Category Decision Tree

Determine which category an item belongs to, checking **top-down by priority**:

1. **User requirement?**
   User explicitly says "must/don't/always..." → requirement
   Ex: "Must use absolute paths", "Never auto push"
   ⚠️ Note: Having "rules" without "mistake experience" → requirement (not gotcha)

2. **Historical mistake?**
   User mentions past problems + solutions → gotcha
   Ex: "Ran into this before, using {...} spread fixed it"
   ⚠️ Key: Must include description of "past encounter"

3. **Reusable process/pattern?**
   Cross-scenario reusable steps, work strategies → experience
   Ex: "fc-local first, firecrawl as backup"
   Ex: "When apply_patch fails, use write instead"

4. **Technical fact/mechanism? (space/project-specific only)**
   Project-internal technical mechanisms, API details, config conventions → knowledge
   Ex: "Part type is tool not tool_call"
   Ex: "LanceDB FTS defaults to English tokenization"
   ⚠️ Note: General searchable technical knowledge is not recorded, only project-specific understanding
   ⚠️ Note: "Research found how X works" → knowledge; "Research concluded X is the best solution" → fact

5. **Project-specific objective fact/decision?**
   Project path conventions, deployment flows, architectural decisions → fact
   Ex: "Decided to centralize docs under docs/"
   ⚠️ Note: General facts are not recorded, only project-specific ones

6. **User preference/habit?**
   Style, tendency, habit (non-mandatory rule) → preference
   Ex: "No emoji", "No class components"
   ⚠️ Note: Preference = "tendency", requirement = "must" — "Don't do X" is a requirement, not a preference

7. **User identity/static attribute?**
   Profession, tech stack, background → profile

---

# Common Confusions

| Wrong Classification | Correct Classification | Reason |
|---------------------|----------------------|--------|
| "User prefers X" | preference | Not profile |
| "Research found how X works" | knowledge | Not fact (project-specific only) |
| "Research concluded X is best" | fact | Not knowledge (project-specific only) |
| "General technical knowledge" | Don't record | General searchable knowledge, only project-specific |
| "Hit problem A, used solution B" | gotcha | Must have historical mistake experience |
| "General process for handling X" | experience | Not gotcha |
| "User explicitly said don't do X" | requirement | Not preference |
| "Technical constraint (no mistake experience)" | requirement | gotcha requires mistake experience |
| "Preference is tendency, requirement is must" | Judgment boundary | Don't mislabel requirements as preferences |

---

# Body Format Specification

Each memory must be a **self-contained structured text**, independently understandable by a third party.

## Core Guidelines

1. **Conclusion first**: First line must be the conclusion/rule/core content ("what it is", "what must be done"), with background and details after. The first sentence has the highest embedding semantic weight — it directly determines retrieval hit rate
2. **Direct description**: No \`## [Category]:\` prefix (category is identified by the category field)
3. **Concise formatting**: Use plain text, no \`**Bold Label**:\` format. Use \`Label:\` when annotation is needed
4. **Background necessary**: Include "why this matters" or "in what scenarios it's useful", but after the conclusion
5. **Content complete**: Retain necessary code/paths/commands, don't over-simplify
6. **No truncation**: Keep complete, but remove redundant descriptions

## Format Templates

### Profile
{"category": "profile", "body": "<identity description>\\n\\n- Profession: ...\\n- Tech stack: ...", "tags": ["背景", "profile"]}

### Preference
{"category": "preference", "body": "<preference description>\\n\\nBackground: ...\\nApplies to: ...", "tags": ["偏好", "code-style"]}

### Knowledge
{"category": "knowledge", "body": "<precise topic>\\n\\n<core content>\\n\\nSource: ...", "tags": ["internal-mechanism", "api"]}

### Fact
{"category": "fact", "body": "<finding/decision>\\n\\n<conclusion and details>", "tags": ["convention", "deployment"]}

### Gotcha
{"category": "gotcha", "body": "<conclusion/correct approach>\\n\\nProblem: ...\\nSolution: ...\\nApplies to: ...", "tags": ["mistake", "workaround", "opencode"]}

### Experience
{"category": "experience", "body": "<process/pattern description>\\n\\nProcess: ...\\nReason: ...", "tags": ["workflow", "best-practice"]}

### Requirement
{"category": "requirement", "body": "<rule description>\\n\\nBackground: ...\\nApplies to: ...", "tags": ["rule", "gate", "git-commit"]}

---

# Tags Specification

Tags are **critical for retrieval quality**. They serve two roles: (1) full-text search matching, and (2) concept boost during injection — English tags matching a query term each give +0.05 relevance boost (max +0.15). Poor tags directly cause retrieval failure.

## Selection Rules

1. **Use search scenario words, not content fragments** — \`delegation\` is a scenario someone would search; \`Done\` is a fragment nobody searches for. \`verification-discipline\` is a scenario; \`checkbox\` is a fragment.
2. **English tags are the primary boost channel** — conceptBoost only applies to English words. Chinese tags act as FTS-only fallback with no boost. Cover all core concepts with English tags first.
3. **No compound invented words** — nobody searches for \`context-manage-detail\`. Use existing, natural words people would actually type.
4. **No overly broad words** — \`operation\`, \`handling\`, \`fix\`, \`update\` are too vague to help retrieval.
5. **≤5 tags** — more than 5 means the memory's focus is unclear. Refine the body instead of adding more tags.

## Self-check Before Output

For each tag, answer: "What would someone search to hit this tag?" If you can't name a real scenario, replace it. Ensure English tags cover all core concepts as the primary boost channel.

---

# Few-shot Examples

## Positive examples (extract)

User said: "I used tail -f to monitor logs before, the interface froze. Now I always use tail -n 30"

Output:
{"memories": [{"category": "gotcha", "body": "Don't use tail -f for log monitoring, use tail -n 30 instead\\n\\nProblem: tail -f monitoring caused the OpenCode interface to hang\\nSolution: Use tail -n 30 instead, or periodically read file content\\nApplies to: Monitoring logs during OpenCode plugin development and debugging", "tags": ["log-monitoring", "tail", "interface-hang", "opencode"]}]}

User said: "Review code changes with me before committing"

Output:
{"memories": [{"category": "requirement", "body": "Code changes must be reviewed before committing\\n\\nBackground: User wants oversight on code changes\\nRequirement: Before git commit, must present change list for user review. Only commit/push when explicitly requested\\nApplies to: All git commit scenarios", "tags": ["code-review", "git-commit", "user-approval", "gate"]}]}

## Negative examples (DO NOT extract — output empty)

Conversation: "The logging level was wrong, I changed it from debug to info. Also merged two duplicate saveSessionContext calls into one."

Output:
{"memories": []}
Reason: Resolved one-off code tweaks. No lasting guidance value — the fix is already in the code.

Conversation: "We added a Tags Specification section to the distill prompt to align with mem-rule.md."

Output:
{"memories": []}
Reason: Design decision already solidified in the prompt file. The file itself is the record.

Conversation: "Updated the LLM client to log the API URL on startup."

Output:
{"memories": []}
Reason: Minor code change log. Future sessions gain nothing from knowing this happened.

Conversation: "We adjusted the distill prompt to add negative few-shot examples, and changed the logging in distill.ts to use structured data output. Also confirmed that compaction summaries are correctly filtered by the skipNext mechanism."

Output:
{"memories": []}
Reason: Session work summary — describes what was done in this conversation. Each change is already in the code/files. No reusable lesson extracted.

Conversation: User explicitly stated: "Each key event only gets one info log, debug only for core info, trace for troubleshooting."

Output:
{"memories": [{"category": "requirement", "body": "Logging rule: each key event gets exactly one info-level log. Debug only for core diagnostic info. Trace for troubleshooting details. Warn uses structured { err } output.\\n\\nBackground: User enforced this rule during wopal-plugin development to prevent log noise\\nApplies to: All plugin module logging (distill, dedup, hooks, etc.)", "tags": ["logging", "log-level", "plugin-development"]}]}
Reason: User explicitly stated a reusable rule with clear requirements. This is a requirement, not a session work summary.

---

# Quality Check

After extraction, self-check each memory:

1. **Worth remembering?** — Will this information be needed in future sessions? If uncertain, discard
2. **Prevents future mistakes?** — Does it capture a lesson that changes future assistant behavior? If not, likely a log entry
3. **Generalized, not specific?** — If the insight is wrapped inside a specific module/feature context, extract ONLY the universal principle. "distill.ts now logs at info level" → discard (implementation detail). "Each key event gets exactly one info log" → potentially valuable IF user stated this as a rule
4. **Has background?** — Does it include "why this matters"
5. **Third-party understandable?** — Can someone who didn't see the original conversation understand it
6. **Information complete?** — Missing any critical code/paths/commands
7. **Is it a log entry?** — If removing this memory, could future sessions obtain the information through code/docs/search, then discard
8. **Tags are specific scenario words?** — Can you name a real search query that would hit each tag? English tags cover core concepts? No compound words or broad terms? ≤5 tags?

**Discard or retry if not qualified.**

---

# Notes

- Prefer fewer, higher quality. 1 high-quality memory > 8 log entries
- Each memory must be independently understandable, don't assume the reader saw the original conversation
- User **dissatisfaction, corrections, repeated emphasis** in conversations are high-value signals — distill the underlying principle, not the surface event
- When the entire conversation is about implementing a feature, fixing bugs, or adjusting code — and the user is satisfied with the result — it is almost always correct to output \`{"memories": []}\``;

export const DEDUP_FALLBACK = `You are a memory deduplicator. For each candidate, compare with similar existing memories and decide: create (unrelated, should coexist), skip (discard), merge (supplement with new details), or replace (replace outdated content).

**Output language must match the language used by the user in the conversation.** All output content (merged_body, tags) and JSON field values must use the same language as the user's conversation.

## Candidates and Existing Memories

\`\`\`json
{{input}}
\`\`\`

---

## Actions

| Action | Meaning |
|--------|---------|
| create | Candidate and existing memory are about different things, both should exist |
| skip | Candidate is fully covered by existing memory |
| merge | Candidate adds new details, merge into existing memory |
| replace | Candidate conflicts with existing memory (existing is outdated or wrong), fully replace with candidate |

## Key Constraints

- **Same keyword ≠ duplicate**: Both mentioning "confirm", "git", "deploy" doesn't mean it's the same thing. Check if the specific content covers the same claim
- **requirement type**: Two different user requirements should coexist (create), don't merge
- **Different categories** → Most likely different memories, prefer create
- Prefer create over erroneous merge — cost of an extra memory is far lower than merge error

## create Rules

- Candidate and existing memory involve similar domains but are different specific things
- Two requirements mandate different behaviors
- Candidate's topic differs from existing memory's topic

## skip Rules

- All key information in candidate already exists in the existing memory
- Candidate is merely a simplified version, rephrasing, or subset of existing memory
- Semantically identical, regardless of wording differences

## merge Rules

- Candidate contains new details, conditions, or paths not in existing memory
- Integrate candidate's new information into existing memory, deduplicate and remove redundancy
- Preserve existing memory's Markdown structure and heading format

## replace Rules

- Candidate and existing memory are about the same thing, but conclusions contradict (old is wrong vs new is correct, or old is outdated)
- Replace existing memory's body entirely with candidate

## Examples

### create — Different requirements should coexist (easy misjudgment)

Candidate: "[Requirement]: Must thoroughly analyze and negotiate before modifying code, only implement after confirmation"
Existing: "[Requirement]: dev-flow --confirm gate meaning: user verbally saying confirm etc. = authorization"
→ create, both are requirements but about different things

### create — Different topics

Candidate: "[Knowledge]: OpenCode system.transform creates a new empty system array on each call"
Existing: "[Knowledge]: OpenCode Assistant message Part type system and filtering rules"
→ create, both involve OpenCode but about different mechanisms

### skip — Content covered

Candidate: "[Requirement]: Never auto push"
Existing: "[Requirement]: Code must be reviewed by user before committing, Agent never needs to ask about push"
→ skip, existing memory already contains this information

### skip — Different wording, same thing

Candidate: "[Experience]: Prefer fc-local for web search, firecrawl consumes credits, use as backup only"
Existing: "[Experience]: Web search and scraping prioritize fc-local skill (local, free), firecrawl consumes credits, backup only"
→ skip, same information, slightly different wording

### skip — Candidate is subset of existing memory (easy misjudgment)

Candidate: "[Preference]: Communicate in Chinese"
Existing: "[Preference]: Communication language Chinese, must confirm before implementing when instructions are vague, dislikes verbosity"
→ skip, candidate is fully covered by existing memory. Don't merge just because candidate is more concise

### merge — Candidate adds specific details

Candidate: "[Gotcha]: distill.md prompt is read from filesystem on each extraction, no restart needed to apply prompt changes"
Existing: "[Experience]: Prompt file changes require OpenCode restart to take effect"
→ merge, candidate adds new detail that "distill prompts have hot-reload, no restart needed"

### replace — Existing memory is outdated

Candidate: "[Requirement]: Dedup and extraction should be 1 LLM call only, don't split into multiple"
Existing: "[Experience]: Dedup flow is two steps: 1 batch decision + separate LLM call per merge"
→ replace, old flow was rejected by user, replace with new

---

## Output

JSON format, index corresponds to input array numbering:

{"decisions": [{"index": 1, "action": "create"}, {"index": 2, "action": "skip"}, {"index": 3, "action": "merge", "merge_into": 1, "merged_body": "merged complete content", "tags": ["tag1"]}, {"index": 4, "action": "replace", "replace_existing": 2, "tags": ["tag2"]}]}

Field descriptions:
- action: create / skip / merge / replace
- merge_into: Which existing memory to merge into (number matches similar_existing index)
- replace_existing: Which existing memory to replace (number matches similar_existing index)
- merged_body: Complete merged content (merge only)
- tags: Retrieval tags, 2-5 lowercase hyphenated English keywords (e.g. \`gotcha\`, \`git-workflow\`), reflecting the memory's core topic. For merge and replace, take the union with existing memory's tags`;

export const COMMIT_MSG_FALLBACK = `You are an expert Git commit message generator. Analyze the provided git diff and generate a conventional commit message.

## Character Limits — VIOLATING THESE = FAILURE

| What | Max | Rule |
|------|-----|------|
| description | **70 chars** | Count characters. If exceeded, shorten by dropping filler words or moving detail to body. |
| description + \`(#N)\` | **60 chars** | Reserve ~10 chars for the issue ref. |
| first line total | **90 chars** | \`type(scope): description(#N)\` — if over, shorten the description. |

**Enforcement**: After drafting the message, count the description characters. If > 70 (or > 60 with issue ref), rephrase. Do NOT output an over-length description.

\${gitContext}

## Format

\`\`\`
<type>(scope): <description>

[optional body]

[optional footer(s)]
\`\`\`

## Type
\`feat\` \`fix\` \`docs\` \`style\` \`refactor\` \`perf\` \`test\` \`build\` \`ci\` \`chore\` \`enhance\` \`revert\`

- \`feat\` / \`enhance\` → MINOR bump. \`fix\` → PATCH bump. Others → no bump.

## Type Selection Rules

Choose type based on **what changed**, not the file extension:

| Changes | Type |
|---------|------|
| New functionality or feature | \`feat\` |
| Bug fix | \`fix\` |
| Documentation files (\`.md\`, \`.txt\`, \`.rst\`) | \`docs\` |
| Code formatting, whitespace, semicolons | \`style\` |
| Code restructure without behavior change | \`refactor\` |
| Performance improvement | \`perf\` |
| Test files (\`*.test.ts\`, \`*.spec.ts\`, \`__tests__/\`) | \`test\` |
| Build system, dependencies, config (\`package.json\`, \`tsconfig\`, \`vite.config\`) | \`build\` |
| CI/CD pipeline (\`.github/workflows\`, \`.gitlab-ci\`) | \`ci\` |
| Tooling, scripts, chores | \`chore\` |
| Reverting a previous commit | \`revert\` |

**Common mistakes to avoid:**
- \`feat\` for documentation changes → use \`docs\`
- \`feat\` for refactoring → use \`refactor\`
- \`feat\` for config/build changes → use \`build\` or \`chore\`
- \`feat\` for test additions → use \`test\`

## Scope (optional)
- Parentheses, lowercase, concise: \`feat(api):\`, \`fix(ui):\`
- Common: api, ui, auth, db, config, deps, docs. Monorepo: package/module name.
- Omit scope when the change is global or unclear.

## Description
- Imperative mood, lowercase first letter, no trailing period
- Describe the single most significant change
- **If the natural description exceeds 70 chars, move detail to body and keep only the core action in the description**

## Body (optional)
- One blank line after description. Wrap at 72 chars.
- Explain what and why (not how).

## Footer (optional)
- \`BREAKING CHANGE: <description>\` for breaking changes
- Issue ref: \`(#N)\` at end of first line, or \`Refs: #N\` in footer

## Issue Reference Rules — CRITICAL

- **NEVER fabricate Issue references.** Do NOT add \`(#N)\` unless the Issue number is explicitly provided in the git context (e.g., branch name \`feature/issue-42\`, commit context mentioning \`#42\`, or explicit user instruction).
- **NEVER add \`(#N)\` to commits that have no associated Issue.** The vast majority of commits do NOT need an issue ref.
- If unsure whether an issue ref applies, omit it. A missing ref is always better than a fabricated one.

## Output constraints
- Output ONLY the raw commit message text. No markdown fences, no commentary, no status lines.
- No \`[Status: ...]\`, no \`[Context: ...]\`, no bracketed metadata of any kind.

## Pre-output checklist (do silently)

1. Type matches the actual change? (docs for \`.md\`, test for tests, etc.)
2. No fabricated \`(#N)\` issue ref?
3. description chars ≤ 70? (≤ 60 with issue ref?)
4. first line total ≤ 90?
5. output contains ONLY the commit message?

## Examples

✅ Documentation change:
\`\`\`
docs(api): update authentication guide
\`\`\`

✅ Short feature:
\`\`\`
feat: add user authentication
\`\`\`

✅ Bug fix with scope:
\`\`\`
fix(auth): resolve login timeout
\`\`\`

✅ Test addition:
\`\`\`
test(server): add session pagination tests
\`\`\`

✅ Refactor with body:
\`\`\`
refactor(scheduler): rebuild task scheduling engine

Replace ad-hoc timer logic with a fiber-based scheduler
that supports cancellation and priority queues.
\`\`\`

❌ WRONG — \`feat\` used for docs:
\`\`\`
feat: update README installation steps
\`\`\`
→ Fix: use \`docs: update README installation steps\`

❌ WRONG — fabricated issue ref:
\`\`\`
feat(api): add pagination to user list endpoint (#42)
\`\`\`
→ Only add \`(#42)\` if Issue #42 is explicitly referenced in the git context.

❌ WRONG — description too long:
\`\`\`
fix(auth): resolve login timeout by increasing session token lifespan for all users
\`\`\`
→ Fix: move detail to body:
\`\`\`
fix(auth): extend session token lifespan

Increase session token duration to reduce login timeout
occurrences during long user sessions.
\`\`\`

✅ Breaking change:
\`\`\`
feat(api): switch to async handlers

BREAKING CHANGE: All API handlers now return Promise.
\`\`\``;
