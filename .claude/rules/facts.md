---
globs: ["**/facts/**", "**/knowledge/**"]
---

# Fact System Rules

- All facts must be typed and validated through the fact system API
- Never hardcode facts that should be dynamic
- Fact mutations go through the proper API — no direct state manipulation
- Fact conflicts must be explicitly handled (never silently overwrite)
- New fact types require schema definition
