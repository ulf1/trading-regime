# Description Optimization Guide

Read this file when improving a skill's `description` field or when a skill
isn't triggering reliably. Full guide at:
https://agentskills.io/skill-creation/optimizing-descriptions

---

## Why the description matters so much

At session start, the agent loads **only** the `name` and `description` of every
skill — not the body. The description is the sole triggering mechanism. A vague
or over-broad description is the single most common reason a skill fails in
production.

---

## Principles for effective descriptions

### 1. Use imperative phrasing

Tell the agent when to act, not what you built:

```yaml
# ✗ Passive — describes the artifact
description: A skill that processes PDF files and extracts text.

# ✓ Imperative — instructs the agent
description: >
  Use this skill when the user wants to extract text from a PDF,
  fill a PDF form, merge multiple PDFs, or convert a PDF to
  another format.
```

### 2. Focus on user intent, not implementation

Match what users say, not how the skill works:

```yaml
# ✗ Implementation-focused
description: Invokes pdfplumber to extract page content via Python bindings.

# ✓ Intent-focused
description: >
  Extract text, tables, or images from PDF files. Use when the user
  mentions PDF, a document they can't edit, or scanned pages.
```

### 3. Be explicit about indirect phrasings

The most valuable lines are the ones covering oblique requests:

```yaml
description: >
  Analyze CSV and tabular data — compute stats, add columns, generate
  charts, and clean messy data. Use even if the user doesn't mention
  "CSV" explicitly but describes a spreadsheet, data file, or says
  "my boss wants a chart from this data."
```

### 4. Add scope boundaries for near-miss exclusions

When adjacent skills exist (or could exist), state what this skill does NOT do:

```yaml
description: >
  Review code for bugs, security issues, and style. Use for pull requests,
  diff reviews, and "what's wrong with this code?" prompts.
  Does NOT scaffold new files or refactor — use the scaffolding skill for that.
```

### 5. Stay concise — hard limit 1024 chars

Long descriptions add context overhead for every query, even irrelevant ones.
A few clear sentences outperform exhaustive lists.

---

## Writing trigger-eval queries

### Should-trigger queries — vary along these axes

| Axis | Example pair |
|---|---|
| Formality | "please extract text from this PDF" vs "hey can u pull text outta this pdf" |
| Explicitness | "analyze this CSV" vs "my data file has sales figures, I need a chart" |
| Brevity | "clean the CSV" vs full context with file path and column names |
| Embedding | Single-step vs the skill's task buried in a multi-step request |

The most valuable positives are **oblique** — the skill clearly helps but
the user never says the domain keyword. These are where description wording
makes the difference.

### Should-NOT-trigger queries — use near-misses

Weak negatives (clearly unrelated topics) test nothing useful:

```json
{ "query": "what is the meaning of life", "should_trigger": false }
```

Strong negatives share keywords but need a different skill or no skill:

```json
{ "query": "write a python script that reads a csv and uploads rows to postgres",
  "should_trigger": false }
```

The CSV skill might help, but the task is database ETL — not analysis.

---

## The optimization loop

1. Write ~20 eval queries (10 positive, 10 negative)
2. Split into train (~60%) and validation (~40%) sets — keep split fixed
3. Run evals: `python scripts/eval-triggers.py evals/evals.json --runs 3`
4. Identify failures in the **train set only**
5. Revise the description:
   - Failures on positives → description too narrow → broaden scope
   - Failures on negatives → description too broad → add exclusions
   - **Generalise the fix** — don't add specific keywords from failed queries
6. Re-run evals in a new iteration
7. Select the description with the highest **validation** pass rate
8. Stop after ~5 iterations or when improvement plateaus

### Common pitfalls

| Pitfall | Effect | Fix |
|---|---|---|
| Adding keywords verbatim from failed queries | Overfits; fails on different phrasing of same intent | Fix the underlying concept, not the specific words |
| Description grows > 1024 chars during iteration | Spec violation; context overhead | Trim filler; move edge cases to body |
| Optimising on all queries (no validation set) | Overfits; doesn't generalise | Always hold out 40% before starting |
| Stopping at first iteration with all positives passing | May overfit to train set | Check validation set before declaring done |

---

## Before / after example

```yaml
# Before (72 chars) — under-specified; misses indirect phrasings
description: Process CSV files.

# After (268 chars) — specific scope + indirect cases + exclusion
description: >
  Analyze CSV and tabular data files — compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use
  when the user has a CSV, TSV, or Excel file and wants to explore,
  transform, or visualize it, even if they don't say "CSV" or
  "analysis" explicitly. Does not handle database migrations.
```

---

## Quick rubric for reviewing a description

- [ ] Imperative phrasing ("Use this skill when…")?
- [ ] Describes user *intent*, not implementation mechanics?
- [ ] Covers direct AND oblique phrasings?
- [ ] Lists scope boundaries / near-miss exclusions if relevant?
- [ ] Under 1024 characters?
- [ ] No filler ("this skill helps with", "a powerful tool for")?
