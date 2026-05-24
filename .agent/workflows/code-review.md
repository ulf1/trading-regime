---
description: Review code for security, correctness, performance, and standards compliance.
---

# Code Review

## Review Procedure

When reviewing code, evaluate in this priority order:

1. **Security** — Hardcoded secrets, injection vulnerabilities, auth logic, input validation.
2. **Correctness** — Logic errors, edge cases, silent failures, error handling gaps.
3. **Performance** — N+1 queries, inefficient loops, missing caching, resource leaks.
4. **Standards Compliance** — Adherence to Python style rules (see `rules/python-style.md`).
5. **Dead Code** — Unused imports, unreachable branches, commented-out code.

## Checklist

- [ ] No hardcoded secrets or credentials
- [ ] Input validation covers edge cases
- [ ] Error handling is specific (no bare `except:`)
- [ ] Functions ≤ 50 lines, nesting ≤ 3 levels
- [ ] New features include tests
- [ ] Tests cover error conditions
- [ ] Test names describe what they verify
- [ ] No unnecessary dependencies added
- [ ] Code follows naming and style conventions
- [ ] Documentation updated where necessary

## Feedback Style

- Be specific and actionable: cite the line and suggest a fix.
- Explain *why* a change is needed, not just *what* to change.
- Ask clarifying questions when intent is unclear.
