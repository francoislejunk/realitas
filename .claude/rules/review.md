---
globs: ["**"]
description: "QA review checklist — loaded when /review command is used"
---

# Review QA Checklist

When `/review` is invoked, run this full checklist against `git diff`:

## Terminology (CRITICAL — blocks PR)
- No banned terms (NPC, character, user, player, level, scene, game)
- Code, comments, docs, UI text all use Realitas terms

## UTAS Compliance
- Personality modeling uses UTAS framework
- Valid UTAS dimensions only

## Fact System
- Facts typed and validated
- No hardcoded dynamic facts
- Mutations through API
- Conflicts handled

## Code Quality
- No `any` types without justification
- No `console.log` (use logger)
- Error handling present
- Functions < 50 lines
- No duplicated logic

## Testing
- New logic has tests
- Edge cases covered
- Tests assert behavior

## Architecture
- Module boundaries respected
- No circular dependencies
- Files in correct directories

## Output
Report pass/fail per section. Verdict: ✅ SHIP IT / ⚠️ FIX FIRST / ❌ BLOCKED
