---
globs: ["**/scenario/**", "**/scenarios/**", "**/engine/**"]
---

# Scenario Engine Rules

- Scenarios are the unit of practice — they define the situation, Interlocutors, and objectives
- Scenario definitions are data, not code — keep logic in the engine, config in definitions
- Interlocutor initialization must load UTAS profiles and seed facts
- Session state management goes through the engine's state API
- New Scenario types need integration tests
