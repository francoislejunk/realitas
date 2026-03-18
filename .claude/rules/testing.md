---
globs: ["**/*.test.ts", "**/*.spec.ts", "**/tests/**", "**/__tests__/**"]
---

# Testing Rules

- Tests live next to source: `foo.ts` → `foo.test.ts`
- Test behavior, not implementation details
- Required edge cases: empty input, null/undefined, boundary values
- Every assertion must test actual behavior (not just "doesn't throw")
- Mock external dependencies, never internal modules
- `tsc --noEmit` must pass before tests run
