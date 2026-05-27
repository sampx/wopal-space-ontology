# Memory Extraction Prompt

**Must output JSON. Do NOT output `<system-reminder>` or other formats.**

**Output language must match the language used by the user in the conversation.** Infer from the conversation below.

Output template:
{"memories": [{"category": "knowledge", "body": "Title\n\nCore content...", "tags": ["tag"]}]}

If nothing to extract, output: {"memories": []}

---

## Recent Conversation
{{conversation}}

---

# Extraction Criteria

## Core Principles

Your goal is to extract memories with **lasting guidance value for future sessions**, not to record what happened in this conversation. Prefer omission over journaling.

**Prioritize extracting**:
- Deep preferences and principles distilled from user dissatisfaction, criticism, or corrections
- Cross-scenario reusable experiences, methodologies, and judgment criteria
- Recurring patterns (user emphasizes the same thing repeatedly → high signal)
- Lessons from mistakes (error + cause + correct approach — all three required)

## What is Worth Remembering?

- **Long-term valid**: Information that remains useful in future sessions, doesn't expire with time
- **Cross-scenario reusable**: Not just solving the current problem, but forming transferable practices
- **Personalized**: Specific to this user, not general domain knowledge
- **Specific and clear**: Has concrete details, not vague generalizations
- **Independently understandable**: A third party can understand without the original conversation context

## What is NOT Worth Remembering?

**Never record**:
- **Resolved one-off issues**: Technical problems raised, discussed, and resolved in this session — code itself is the most authoritative documentation
- **Code change logs**: "Modified file X", "Refactored function Y" — that's what git log is for
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
2. **Direct description**: No `## [Category]:` prefix (category is identified by the category field)
3. **Concise formatting**: Use plain text, no `**Bold Label**:` format. Use `Label:` when annotation is needed
4. **Background necessary**: Include "why this matters" or "in what scenarios it's useful", but after the conclusion
5. **Content complete**: Retain necessary code/paths/commands, don't over-simplify
6. **No truncation**: Keep complete, but remove redundant descriptions

## Format Templates

### Profile
{"category": "profile", "body": "<identity description>\n\n- Profession: ...\n- Tech stack: ...", "tags": ["背景", "profile"]}

### Preference
{"category": "preference", "body": "<preference description>\n\nBackground: ...\nApplies to: ...", "tags": ["偏好", "code-style"]}

### Knowledge
{"category": "knowledge", "body": "<precise topic>\n\n<core content>\n\nSource: ...", "tags": ["internal-mechanism", "api"]}

### Fact
{"category": "fact", "body": "<finding/decision>\n\n<conclusion and details>", "tags": ["convention", "deployment"]}

### Gotcha
{"category": "gotcha", "body": "<conclusion/correct approach>\n\nProblem: ...\nSolution: ...\nApplies to: ...", "tags": ["mistake", "workaround", "opencode"]}

### Experience
{"category": "experience", "body": "<process/pattern description>\n\nProcess: ...\nReason: ...", "tags": ["workflow", "best-practice"]}

### Requirement
{"category": "requirement", "body": "<rule description>\n\nBackground: ...\nApplies to: ...", "tags": ["rule", "gate", "git-commit"]}

---

# Tags Specification

Tags are **critical for retrieval quality**. They serve two roles: (1) full-text search matching, and (2) concept boost during injection — English tags matching a query term each give +0.05 relevance boost (max +0.15). Poor tags directly cause retrieval failure.

## Selection Rules

1. **Use search scenario words, not content fragments** — `delegation` is a scenario someone would search; `Done` is a fragment nobody searches for. `verification-discipline` is a scenario; `checkbox` is a fragment.
2. **English tags are the primary boost channel** — conceptBoost only applies to English words. Chinese tags act as FTS-only fallback with no boost. Cover all core concepts with English tags first.
3. **No compound invented words** — nobody searches for `context-manage-detail`. Use existing, natural words people would actually type.
4. **No overly broad words** — `operation`, `handling`, `fix`, `update` are too vague to help retrieval.
5. **≤5 tags** — more than 5 means the memory's focus is unclear. Refine the body instead of adding more tags.

## Self-check Before Output

For each tag, answer: "What would someone search to hit this tag?" If you can't name a real scenario, replace it. Ensure English tags cover all core concepts as the primary boost channel.

---

# Few-shot Examples

User said: "I used tail -f to monitor logs before, the interface froze. Now I always use tail -n 30"

Output:
{"memories": [{"category": "gotcha", "body": "Don't use tail -f for log monitoring, use tail -n 30 instead\n\nProblem: tail -f monitoring caused the OpenCode interface to hang\nSolution: Use tail -n 30 instead, or periodically read file content\nApplies to: Monitoring logs during OpenCode plugin development and debugging", "tags": ["log-monitoring", "tail", "interface-hang", "opencode"]}]}

User said: "Review code changes with me before committing"

Output:
{"memories": [{"category": "requirement", "body": "Code changes must be reviewed before committing\n\nBackground: User wants oversight on code changes\nRequirement: Before git commit, must present change list for user review. Only commit/push when explicitly requested\nApplies to: All git commit scenarios", "tags": ["code-review", "git-commit", "user-approval", "gate"]}]}

---

# Quality Check

After extraction, self-check each memory:

1. **Worth remembering?** — Will this information be needed in future sessions? If uncertain, discard
2. **Title precise?** — Does the title accurately describe "what this is"
3. **Has background?** — Does it include "why this matters"
4. **Third-party understandable?** — Can someone who didn't see the original conversation understand it
5. **Information complete?** — Missing any critical code/paths/commands
6. **Is it a log entry?** — If removing this memory, could future sessions obtain the information through code/docs/search, then discard
7. **Tags are specific scenario words?** — Can you name a real search query that would hit each tag? English tags cover core concepts? No compound words or broad terms? ≤5 tags?

**Discard or retry if not qualified.**

---

# Notes

- Prefer fewer, higher quality. 3 high-quality memories > 8 log entries
- Each memory must be independently understandable, don't assume the reader saw the original conversation
- User **dissatisfaction, corrections, repeated emphasis** in conversations are high-value signals — distill the underlying principle, not the surface event
