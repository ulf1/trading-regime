# Interaction Rules

## 1. Behavior

- **Conciseness:** Be brief. Omit explanations for standard code unless asked. Exception: always provide comprehensive tests and necessary documentation.
- **Code First:** Provide the solution first, then explanation if necessary.
- **Minimal Diffs:** Keep changes focused. Provide enough context to locate the change, but do not reprint entire files.
- **Prefer Standard Solutions:** Use framework-native or standard library approaches. Do not introduce new third-party dependencies without explicit justification.
- **Follow Existing Patterns:** Follow the project's established patterns. Prefer modifying existing modules over creating new ones.
- **No Drive-by Refactoring:** Do not refactor unrelated code unless explicitly requested.
- **Backward Compatibility:** Preserve backward compatibility unless told otherwise.

## 2. What to Avoid

- Introducing breaking changes without instruction.
- Overengineering simple solutions.
- Adding speculative abstractions.
- Rewriting stable, working code unnecessarily.
- Ignoring established architectural patterns.
