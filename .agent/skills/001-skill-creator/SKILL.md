---
name: 001-skill-creator
description: >
  Create, scaffold, validate, audit, and improve Agent Skills (SKILL.md packages)
  for Antigravity or any compatible agent runtime. Use this skill when the user
  wants to build a new skill from scratch, scaffold a skill directory, check or
  validate an existing skill's structure or frontmatter, audit a SKILL.md for
  quality issues, improve a skill's description for better triggering accuracy,
  run trigger-rate evals against a skill, or iterate on a skill using eval-driven
  feedback. Trigger even when the user simply asks to "make a skill for X",
  "write a SKILL.md", "review this skill", or "why isn't my skill triggering"
  without using the word "skill" explicitly.
compatibility: Requires Python 3.11+. All scripts use only stdlib — no install step.
metadata:
  author: skill-creator
  version: "1.1"
---

# Skill Creator

Scaffold new Agent Skills, validate existing ones, and run eval-driven improvement
loops — all from within Antigravity.

## Available scripts

| Script | Purpose |
|---|---|
| `scripts/validate.py <skill-dir>` | Validate a skill against the spec. Exits 0 on pass, 1 on errors. |
| `scripts/scaffold.py <name> [--desc "..."] [--dest <path>]` | Create a new skill directory with a template SKILL.md. Pass `--full` to also generate `scripts/`, `references/`, and `evals/` stubs. |
| `scripts/eval-triggers.py <queries.json> [--skill-dir <path>] [--runs 3]` | Run trigger-rate evals for a skill's description. |

---

## Workflows

### A — Create a skill from scratch

Use when the user asks to build a new skill, "make a skill for X", or "write a
SKILL.md" for a domain they describe.

**Step 1 — Gather intent.** Ask (or infer from context) the single task the
skill should own and the typical user phrasing that should trigger it. Resist
scope creep: one coherent unit of work per skill.

**Step 2 — Scaffold the directory.**

```bash
python scripts/scaffold.py <name> --desc "draft description" --dest .agent/skills/
```

This creates `<dest>/<name>/SKILL.md` with placeholders plus empty `scripts/`,
`references/`, and `assets/` stubs.

**Step 3 — Fill `SKILL.md`.** Edit the generated file following the
[Body structure](#body-structure) rules below. Read `references/SPEC.md` for
full field constraints.

**Step 4 — Validate.**

```bash
python scripts/validate.py .agent/skills/<name>
```

Fix every ERROR. Review every WARNING.

**Step 5 — Dry-run the description.** Ask 3–5 prompts that *should* trigger the
skill and 3–5 that *shouldn't*. Use the result to tighten the description before
writing evals.

**Step 6 — Write evals and iterate** (see Workflow C).

---

### B — Validate or audit an existing skill

Use when the user asks to "check", "validate", "review", or "audit" a skill they
already have.

**Step 1 — Run the validator.**

```bash
python scripts/validate.py <path-to-skill-dir>
```

The script checks:
- Frontmatter parses cleanly as YAML
- `name` is present, ≤ 64 chars, matches the directory name, is lowercase with
  hyphens only, no consecutive hyphens, no leading/trailing hyphens
- `description` is present and ≤ 1024 chars
- `compatibility` (if present) is ≤ 500 chars
- All files referenced in the Markdown body exist relative to the skill root
- Body is present (non-empty after frontmatter)
- Body line count warning if > 500 lines

**Step 2 — Review description quality.** Beyond spec compliance, ask:
- Does it use imperative phrasing ("Use this skill when…")?
- Does it describe user *intent*, not implementation mechanics?
- Does it list specific keywords and near-miss exclusions?
- Is it under 1024 characters?

Read `references/DESCRIPTION-GUIDE.md` for the full rubric. Propose a revised
description and explain each change.

**Step 3 — Review body quality.** Check for:
- Vague filler ("handle errors appropriately") the agent already knows → cut it
- Missing gotchas (environment-specific surprises, naming quirks, API edge cases)
- Missing examples or output templates for structured output
- Scripts that should be bundled in `scripts/` (any logic reinvented > once)
- Body > 500 lines → move detailed reference material to `references/`

---

### C — Run trigger-rate evals

Use when the user asks "why isn't my skill triggering", "test my skill", "optimize
the description", or wants to iterate systematically.

**Step 1 — Create `evals/evals.json`** inside the skill directory if it doesn't
exist yet. The format:

```json
[
  { "query": "...", "should_trigger": true },
  { "query": "...", "should_trigger": false }
]
```

Aim for ~20 queries: half positive (varied phrasing, some oblique), half
negative (near-misses that share keywords but need something different).
See `references/DESCRIPTION-GUIDE.md` for guidance on writing good eval queries.

**Step 2 — Run evals.**

```bash
python scripts/eval-triggers.py evals/evals.json \
  --skill-dir .agent/skills/<name> \
  --runs 3
```

The script prints a pass-rate table per query and an overall score. The
detection logic defaults to checking whether Antigravity loaded the skill's
`SKILL.md` during the run (requires `ANTIGRAVITY_CLI` env var; see script
`--help` for other agent backends).

**Step 3 — Interpret results.**

| Symptom | Likely cause | Fix |
|---|---|---|
| Should-trigger queries failing | Description too narrow or missing keywords | Broaden scope; add more intent patterns |
| Should-not-trigger queries firing | Description too broad | Narrow with explicit exclusions |
| Inconsistent (same query sometimes passes) | Description ambiguous | Add imperative phrasing; avoid synonyms with adjacent skills |

**Step 4 — Revise the description.** Give the eval results, current description,
and any failure patterns to the agent and ask for a proposed rewrite. Apply it,
re-run evals. Repeat up to five iterations. Select the version with the highest
validation-set pass rate (not necessarily the last one).

**Step 5 — Apply and verify.**
- Update `description` in `SKILL.md`.
- Confirm it is ≤ 1024 characters.
- Run `validate.py` once more as a final check.

---

## Body structure

Well-structured skill bodies follow this pattern (adapt as needed — not every
section is required):

```markdown
## Goal
One sentence: what does this skill achieve for the user?

## Instructions
Stepwise procedure. Be prescriptive where the task is fragile;
give freedom where multiple approaches are equally valid.

## Gotchas
- Concrete, environment-specific surprises the agent would otherwise get wrong.
- Not general advice — specific corrections.

## Output format
Template or example of what the agent should produce.

## Constraints
Hard "do not" rules.
```

---

## Install locations

| Scope | Path |
|---|---|
| Workspace (version-controlled) | `<workspace-root>/.agent/skills/<name>/` |
| Global (all projects) | `~/.gemini/antigravity/skills/<name>/` |

Prefer workspace scope for team skills. Commit the skill directory into the repo
so teammates get it automatically on clone.

---

## Gotchas

- **`name` must match the directory name exactly** — case-sensitive on macOS/Linux.
  Naming the folder `MySkill` but setting `name: myskill` will pass frontmatter
  validation but cause the skill to silently fail to load in some runtimes.
- **Antigravity marks `name` as optional** (defaults to directory name), but the
  agentskills.io open spec requires it. Always include it for cross-runtime
  portability.
- **After adding or editing a skill**, restart the Antigravity agent (`Cmd/Ctrl+Shift+P`
  → "Restart Agent") — unlike Claude Code, Antigravity does not hot-reload skills
  mid-session.
- **`description` is the only trigger mechanism.** Improving it is almost always
  more effective than rewriting the body when a skill isn't activating.
- **Don't put secrets or credentials in `SKILL.md`.** It is plain text committed
  to the repo. Use environment variables and reference them by name.
- **Script paths in `SKILL.md` are relative to the skill directory root**, not the
  workspace root. all file paths are resolved relative to the skill root, not the workspace root.
