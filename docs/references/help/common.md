# How This Space Works — Common Reference

## How to Work Here

There are two ways to interact with this space:

**1. Talk directly to the Agent.**
Just tell me what you want. "帮我创建一个项目", "review 这段代码", "看看这个 Issue". I'll figure out which skill to load and whether to handle it myself or delegate to a sub-agent.

**2. Use slash commands for common operations.**
Shortcuts for frequent actions (see Commands section below). Slash commands are available inside the ellamaka session.

**3. Use the wopal CLI for system operations.**
For checking space status, managing ontologies, and other deterministic system operations, use `wopal` in your terminal.

A simple rule: **semantic work → tell the Agent; system operations → use the CLI.**

---

## Important Files and Directories

| Location | What It Is | When You'll Use It |
|----------|-----------|-------------------|
| `projects/` | Code projects | Clone repos, create new projects |
| `contents/` | Content creation | Blog posts, tutorials |
| `docs/` | Cross-project docs | Product docs, design docs |
| `AGENTS.md` | Space entry point | Add your own Agent rules |
| `.wopal-space/STRUCTURE.md` | Space structure index | Agent uses it to understand the space |
| `.wopal-space/REGULATIONS.md` | Space regulations | Read or modify Agent behavior rules |
| `.wopal-space/memory/USER.md` | User profile | Agent reads it on every start |

---

## Core Commands

| Command | What It Does | When To Use |
|---------|-------------|-------------|
| `/help` | Show space usage guide | You forgot how to work |
| `/init` | Calibrate space structure | After adding new projects/directories |
| `/commit` | Stage and commit with规范的提交格式 | Code changes ready to commit |
| `/review` | Review code quality | Want the Agent to check your code |
| `wopal space status` | Check space ↔ type sync status | Need to know if space is up to date |
| `wopal ontology status` | Check ontology source sync status | Need to know about upstream changes |

---

## Core Skills

Skills are the Agent's workflow modules. They load automatically when needed; you don't need to trigger them manually.

| Skill | What It Handles | When It Loads |
|-------|----------------|---------------|
| `space-master` | Workflow routing, space maintenance, ontology collaboration | Agent isn't sure what to do |
| `agents-collab` | Sub-agent delegation protocol | Before any fae/rook delegation |
| `dev-flow` | Issue/Plan driven development | Creating issues, progressing plans |

---

## Rules and Customization

**Where rules live:**
- `.wopal-space/REGULATIONS.md` — regulations the Agent must follow (safety, git, delegation rules)
- `AGENTS.md` — your space-specific customization entry point

**How to change Agent behavior:**
1. Edit `REGULATIONS.md` to adjust the rules the Agent must follow
2. Edit `AGENTS.md` to add your own space rules
3. Tell the Agent "记住我的偏好" and I'll update `USER.md`

You don't need to read or understand all the rules immediately. Just know where they are. When you want to change something, tell me.
