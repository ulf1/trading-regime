# Agent Skills Spec — Quick Reference

Read this file when you need to check a specific constraint or field definition.
Full spec at: https://agentskills.io/specification

---

## Directory layout

```
skill-name/         ← must match SKILL.md `name` field exactly
├── SKILL.md        ← REQUIRED
├── scripts/        ← optional; executable code
├── references/     ← optional; documentation loaded on demand
├── assets/         ← optional; templates, images, data files
└── evals/          ← optional; eval test cases (not loaded by agent)
    └── evals.json
```

---

## SKILL.md structure

```
---                         ← opening delimiter
<YAML frontmatter>
---                         ← closing delimiter
<Markdown body>
```

---

## Frontmatter fields

| Field | Required | Constraints |
|---|---|---|
| `name` | **Yes** | 1–64 chars. `[a-z0-9]` and single hyphens only. No leading/trailing/consecutive hyphens. Must match parent directory name exactly. |
| `description` | **Yes** | 1–1024 chars. Non-empty. Should include WHAT the skill does and WHEN to use it. |
| `compatibility` | No | 1–500 chars if present. System requirements, runtime versions, network access. |
| `license` | No | License name or path to bundled license file. |
| `metadata` | No | Arbitrary key-value map for additional properties. |
| `allowed-tools` | No | Space-separated pre-approved tool names. Experimental — support varies. |

### `name` validation rules

```
✓ pdf-processing
✓ data-analysis
✓ code-review
✗ PDF-Processing     # uppercase
✗ -pdf               # leading hyphen
✗ pdf--processing    # consecutive hyphens
✗ pdf-               # trailing hyphen
✗ my skill           # space
```

### `description` best practices

- Imperative phrasing: "Use this skill when…" not "This skill does…"
- Focus on user *intent*, not implementation mechanics
- Include specific keywords users are likely to type
- Mention near-miss exclusions: "even if they don't say 'CSV' directly"
- Max 1024 chars — concise descriptions reduce context overhead across many skills

---

## Progressive disclosure — three loading levels

| Level | Tokens | When loaded |
|---|---|---|
| Frontmatter only | ~100/skill | Always, at session start — all skills simultaneously |
| Full SKILL.md body | ≤5000 recommended | When agent decides skill is relevant to the task |
| scripts/, references/, assets/ | As needed | Only when SKILL.md explicitly instructs the agent to read/run them |

**Implication:** keep `SKILL.md` under 500 lines. Heavy content goes in
`references/` with explicit load conditions ("Read references/api-errors.md
if the API returns a non-200 status").

---

## File references

Use **relative paths from the skill directory root**:

```markdown
Run: `scripts/check.py`         ✓ correct
Run: `./scripts/check.py`       ✓ also valid
Run: `/home/user/.../scripts`   ✗ absolute — breaks portability
```

---

## Antigravity-specific notes

| Item | Value |
|---|---|
| Workspace skills path | `<workspace-root>/.agent/skills/` |
| Global skills path | `~/.gemini/antigravity/skills/` |
| `name` field | Optional in Antigravity (defaults to dir name), **required** by agentskills.io spec |
| Hot-reload | Antigravity does NOT hot-reload skills mid-session — restart agent after changes |
| Trigger check CLI | `Cmd/Ctrl+Shift+P` → "Restart Agent" after editing |
| Path quirk | Official path is `.agent/skills/` (singular); some docs show `.agents/skills/` — use singular |

---

## Validation quick-check

```bash
python skill-creator/scripts/validate.py <skill-dir>
```

Or use the open-source reference library:

```bash
skills-ref validate ./my-skill
```

---

## Cross-runtime portability

The same `SKILL.md` format works across Antigravity (`.agent/skills/`),
Claude Code (`.claude/skills/`), Cursor, Gemini CLI, and Codex CLI.
Only the install path differs per tool. Always include the `name` field
for portability even when using Antigravity alone.
