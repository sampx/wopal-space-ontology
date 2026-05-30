# Agent Skills Reference

## Core Concept

Agent Skills is an open format for extending AI agent capabilities with specialized knowledge and workflows. A skill is a folder containing a `SKILL.md` file with metadata and instructions.

## Directory Structure

```
skill-name/
├── SKILL.md       # Required: YAML frontmatter + Markdown instructions
├── scripts/       # Optional: executable code (Python, Bash, JS)
├── references/    # Optional: REFERENCE.md, FORMS.md, domain-specific docs
└── assets/        # Optional: templates, images, data files
```

## SKILL.md Format

### Frontmatter Fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | 1-64 chars, lowercase a-z + hyphens only, no leading/trailing/consecutive hyphens |
| `description` | Yes | 1-1024 chars, describes what + when to use, includes keywords |
| `license` | No | License name or reference to bundled LICENSE.txt |
| `compatibility` | No | 1-500 chars, environment requirements |
| `metadata` | No | Arbitrary key-value map (author, version, etc.) |
| `allowed-tools` | No | Space-delimited pre-approved tools (experimental) |

```yaml
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

### Body Content

- Markdown with step-by-step instructions, examples, edge cases
- No format restrictions
- Keep under 500 lines; move detailed references to separate files

### Optional Directories

**scripts/**: Executable code, self-contained, include error handling
**references/**: REFERENCE.md, FORMS.md, domain-specific docs - load on demand
**assets/**: Templates, images, data files - static resources

## Progressive Disclosure

1. **Metadata** (~100 tokens): `name` + `description` loaded at startup
2. **Instructions** (< 5000 tokens): Full SKILL.md body loaded on skill activation
3. **Resources**: Files in scripts/, references/, assets/ loaded as needed

## Agent Integration Requirements

### Core Workflow

1. **Discover**: Scan configured directories for folders with SKILL.md
2. **Load Metadata**: Parse frontmatter at startup (low context usage)
3. **Match**: Match user tasks to relevant skills via description
4. **Activate**: Load full SKILL.md instructions when skill matches
5. **Execute**: Run scripts, access resources as needed

### Metadata Injection Format

```xml
<available_skills>
  <skill>
    <name>pdf-processing</name>
    <description>Extracts text and tables from PDF files, fills forms, merges documents.</description>
    <location>/path/to/skills/pdf-processing/SKILL.md</location>
  </skill>
</available_skills>
```

- Each skill adds ~50-100 tokens to context
- Include `location` for filesystem-based agents; omit for tool-based agents

### Integration Approaches

**Filesystem-based agents**: Operate in bash/unix environment, activate skills via shell commands (`cat /path/to/skill/SKILL.md`)
**Tool-based agents**: Implement custom tools to trigger skills and access assets

### Security Considerations

- **Sandboxing**: Run scripts in isolated environments
- **Allowlisting**: Only execute scripts from trusted skills
- **Confirmation**: Ask users before dangerous operations
- **Logging**: Record all script executions for auditing

## File References

Use relative paths from skill root, one level deep:

```
See [reference](references/REFERENCE.md)
Run: scripts/extract.py
```

Avoid deeply nested reference chains.

## Validation

```bash
skills-ref validate ./my-skill
```

Reference library: https://github.com/agentskills/agentskills/tree/main/skills-ref

## GitHub Resources

- Skills spec: https://github.com/agentskills/agentskills
- Example skills: https://github.com/anthropics/skills
- Authoring best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
