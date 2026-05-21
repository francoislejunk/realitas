# UTAS Hard Rules (Symmetry + No Defaults)

This document codifies the hard rules that govern interpretation, resolution, reporting, and narrative behavior in UTAS. It exists to preserve design intent across sessions and chats.

## Core Principles
- **Symmetry end-to-end**: Proactor and Reactor are treated as carbon copies in interpretation, validation, resolution, and reporting (with the one asymmetry: Proactor uses Self-Effects; Reactor uses Secondary Effects).
- **No defaults**: Missing mandatory UTAS factors must NOT be silently defaulted. Instead, re-prompt or abort.
- **Winner’s intent controls sign**: The winner’s `shift_polarity` determines positive/negative sign of shifts. Missing polarity → no shift, visible warning.
- **Diegetic, natural feel**: Four-Mode Narrative Loop guides pacing; no gamey UI.

## Mandatory UTAS Factors

### Proactor (UA/NUA – Steps 1/2)
Required in `utas_factors`:
- `exchange_type` ∈ {Supply, Stamina, Spirit, Sympathy}
- `status_to_shift` ∈ {SPIRIT, STAMINA, SUPPLY, SYMPATHY}
- `s_trait_to_use` ∈ {SWIFTNESS, SOCIABILITY, STURDINESS, SMARTS, SHADOW}
- `s_trait_value` ∈ [0..5]
- `skill` = { name, value:int }
- `super` = { name, value:int }
- `supplement` = { name, value:int }
- `stress_level` ∈ [1..5]
- `shift_type` ∈ {Lasting, Temporary}
- `shift_polarity` ∈ {Additive, Subtractive}
- `self_effects` (non-empty list)

Justifications (recommended, surfaced in reporter):
- `s_trait_justification`, `skill_justification`, `stress_justification`, `shift_type_justification`, `shift_polarity_justification`, `self_effects_justification`

### Reactor (NUA/UA – Steps 3/4)
Required in `utas_factors`:
- `reactor_reaction_description`
- `reactor_reaction_skill` = { name, value:int }
- `reactor_reaction_s_trait` ∈ {SWIFTNESS, SOCIABILITY, STURDINESS, SMARTS, SHADOW}
- `reactor_reaction_super` = { name, value:int }
- `reactor_reaction_supplement` = { name, value:int }
- `reactor_primary_defensive_status_type` ∈ {SPIRIT, STAMINA, SUPPLY}
- `status_to_shift` ∈ {SPIRIT, STAMINA, SUPPLY, SYMPATHY}
- `shift_polarity` ∈ {Additive, Subtractive}
- `has_secondary_effect` ∈ {TRUE/FALSE}
- `stress_level` ∈ [1..5]

If `has_secondary_effect == TRUE`, provide:
- `secondary_effect_justification`
- `secondary_effect_target` ∈ {Proactor, Self}
- `secondary_effect_target_justification`
- `secondary_effect_target_status_type` ∈ {SPIRIT, STAMINA, SUPPLY}
- `secondary_effect_target_status_justification`
- `secondary_effect_shift_polarity_numeric` ∈ {+1, -1}
- `secondary_effect_shift_polarity_justification`
- `secondary_effect_shift_type_multiplier` ∈ {1.0, 0.5}
- `secondary_effect_shift_type_justification`

Reactor **does not** have `self_effects`.

## Normalization & Validation (response_normalizer.py)
- Proactor and Reactor responses are validated strictly.
- Canonicalization:
  - `status_to_shift` uppercased to SPIRIT/STAMINA/SUPPLY/SYMPATHY.
  - `shift_polarity` capitalized to Additive/Subtractive.
  - `s_trait_to_use` canonical SFactorType.
- Objects must be `{ name, value:int }`.
- Proactor `self_effects` must be non-empty and each item must include `{condition, target_status, polarity, shift_type, severity ∈ [1..4]}`; severity validated via table/logic.
- Missing/invalid → raise error (no default insertions).

## Exchange Resolution (exchange_system.py)
- Compute success difference; `shift_magnitude = round_half_away_from_zero(abs(diff) * (0.5 if Temporary else 1.0))`.
- Winner’s intent sets sign:
  - If Proactor wins and `p_intended != 0`: `final_shift_amount = shift_magnitude * p_intended`.
  - Else if Reactor wins and `r_intended != 0`: `final_shift_amount = shift_magnitude * r_intended`.
  - Else (missing polarity): `final_shift_amount = 0` and `shift_calc` includes `missing_polarity` marker.
- Apply effects to the loser on the targeted status.
- Sympathy modifier uses explicit `shift_polarity`; if missing → sympathy skipped with visible warning.
- INUA exchanges mirror the above; no hardcoded damage path.

## Reporting Symmetry (enhanced_reporter.py)
- Step 1/3: Display roles and **missing UTAS warnings** for both Proactor and Reactor.
- Action interpretations: narrative lines for both.
- **UTAS Factors blocks** for both roles with symmetric labels.
- Proactor: `Self-Effects (Proactor)`; Reactor: `Secondary Effect (Reactor)`.
- Step 2/4: Success Overview shows totals and optional calc strings for both.
- Step 5: Status Shifts list with explicit before/after values.
- Step 6: Single comprehensive narrative. If `shift_calc` contains `missing_polarity`, print a warning and do not imply a shift.
- If Conductor aborts: print `⚠️ Exchange Aborted`, the reason, and `re_prompt_attempts`, then skip shifts and Step 6.

## Conductor Hard Stop (MAIN/redesigned_main.py)
- Before Exchange, validate Proactor and Reactor via `ResponseNormalizer`.
- On error, re-prompt Interpreter up to 2 times with a targeted “repair” note.
- If still invalid: set `exchange_aborted = True` with `abort_reason` and `re_prompt_attempts`; skip mechanics.

## Temporary vs Lasting & Recovery (summary)
- Temporary shifts use 0.5 multiplier and are tracked for recovery.
- At each initiative (turn start), +1 recovery to the lowest current status affected by temporary subtractive shifts.
- Lasting subtractive shifts reduce current and max capacity.
- Death if any status max capacity reaches 0 (checked at end of turn).

## Four-Mode Narrative Loop (summary)
- Modes: Roam, Spark, Pressure, Outcome.
- Use soft signals (want/friction/closure) to transition.
- No visible meters; diegetic cues only.
- Narrative and scene framing respect mode; mechanics remain symmetric and explicit when contested.

## Do-Not-Do List
- Do **not** silently default `shift_polarity`, `status_to_shift`, or any mandatory UTAS fields.
- Do **not** inject Reactor `self_effects`.
- Do **not** duplicate Step 6 narrative; prefer single comprehensive line and/or deterministic phrase.
- Do **not** apply harm by default when Reactor wins; always use winner’s intended polarity.

## Testing Checklist
- **Friendly SPIRIT test ("fist bump")**: contested, winner Additive → loser gets SPIRIT Boost; Step 6 shows Magnitude + Boost.
- **Missing polarity**: exchange aborted or no shift with `missing_polarity` warning; Step 6 warns.
- **Reactor self-effects absent**: no reactor `self_effects` anywhere.
- **Sympathy modifier**: applied/skipped based on explicit polarity; no defaults.
- **INUA**: winner intent sets sign; no hardcoded damage path.
- **Reporter symmetry**: UTAS blocks, justifications, success overview for both roles.

## File References
- Interpretation prompts: `agents/interpreter_agent.py`
- Normalization: `response_normalizer.py`
- Resolution: `exchange_system.py`
- Conductor: `MAIN/redesigned_main.py`
- Reporter: `enhanced_reporter.py`
- Narrative loop: `llm_agents/narrative_loop_system.py`
- Sympathy: `sympathy_utils.py`

---
This document is the source of truth. Any change to behavior must be reflected here.
