# CLAUDE.md — Realitas

You are working on **Realitas**, an AI-powered Reality Simulator for practicing interpersonal communication.

## Terminology — Hard Rules

| ❌ Never | ✅ Always |
|----------|----------|
| NPC, character, bot, agent | **Interlocutor** |
| User, player, student | **Practitioner** |
| Level, scene, simulation, game | **Scenario** |
| Play, game session | **Practice session** |

Violations block PRs. No exceptions.

## Commands

- `/spec <feature>` — Research codebase, write implementation spec → `docs/specs/`
- `/handoff` — Summarize session for next agent → `docs/handoffs/`
- `/review` — Run full QA checklist against current changes

## Architecture

- TypeScript strict mode. No `any` without justification.
- No `console.log` — use project logger.
- Functions < 50 lines.
- New logic requires unit tests.
- Module boundaries are sacred — don't reach across them.

## Core Systems

- **UTAS** — Universal Trait Attribution System. All Interlocutor personality/behavior goes through UTAS.
- **Fact System** — Typed, validated dynamic knowledge. Never silently overwrite facts.
- **Scenario Engine** — Orchestrates practice sessions, loads Scenarios, initializes Interlocutors.

## Before Starting Any Task

1. Check `docs/specs/` for existing specs related to your task
2. Check `docs/handoffs/` for recent session context
3. `git log --oneline -20` to see recent work
4. If unfamiliar with a subsystem, read its primary module before changing anything

## Git Conventions

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Commit messages reference the subsystem: `feat(utas): add trait interpolation`
- Small, atomic commits. One concern per commit.
- Branch naming: `feat/<name>`, `fix/<name>`, `refactor/<name>`

## Testing

- Unit tests live next to source: `foo.ts` → `foo.test.ts`
- Test behavior, not implementation
- Edge cases: empty input, null, boundary values
- `tsc --noEmit` must pass — type errors block everything
