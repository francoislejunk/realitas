# Tracker_Agent Integration Guide

## Overview

This guide shows exactly how to integrate the Tracker_Agent into your existing UTAS simulation without changing any current logic or behavior. The tracker acts as a passive observer that records everything for historical reference.

## Step 1: Basic Integration Setup

### Import and Initialize

Add these imports to your `main.py`:

```python
from agents.tracker_agent import TrackerAgent
```

Initialize the tracker at the start of your main function:

```python
def main():
    load_dotenv()
    colorama.init()
    logger = UTASLogger()
    
    # Initialize Tracker_Agent
    tracker = TrackerAgent()
    
    # Set up actors as usual
    actor_sheet = ActorSheet(...)
    actor = UserActor(actor_sheet)
    
    # Start tracking session
    tracker.start_session([actor])
    
    # ... rest of your existing code
```

## Step 2: Scene-Level Integration

### Scene Start Tracking

When you start a new scene:

```python
# Your existing scene creation
scene_data = scene_creator.start_new_simulation(actor)
nua = scene_creator.get_current_nua()
scene_description = narrator.narrate_scene_introduction(...)

# Add tracker call (no changes to existing logic)
tracker.start_scene(
    scene_number=1,  # increment for each scene
    scene_data=scene_data,
    nua_data=nua.sheet.__dict__ if nua else None,
    scene_description=scene_description
)
```

### Scene Conclusion Tracking

When a scene ends:

```python
# Your existing scene conclusion logic runs normally
# Then add tracking:
tracker.conclude_scene(
    conclusion_type="victory",  # or "defeat", "transition", "interrupted"
    final_narrative="The scene concludes...",
    next_scene_trigger="continue" if scene_data else None
)
```

## Step 3: Exchange-Level Integration

### Exchange Start

At the beginning of each exchange:

```python
# Your existing exchange setup
exchange_in_progress = True
exchange_outcome = None

# Add tracker call
participants = [
    f"actor_{actor.sheet.name.lower().replace(' ', '_')}",
    f"actor_{nua.sheet.name.lower().replace(' ', '_')}"
]
tracker.start_exchange(exchange_number=1, participants=participants)
```

### Exchange Conclusion

When an exchange ends:

```python
# Your existing exchange resolution logic
# Then add tracking:
tracker.conclude_exchange(
    winner=f"actor_{winner.sheet.name.lower().replace(' ', '_')}" if winner else None,
    final_state="resolved",  # or "ongoing", "interrupted"
    scene_transition=True if scene_transition else False
)
```

## Step 4: Round-Level Integration

### Round Start with Initiative

When starting a round:

```python
# Your existing round start
initiative_data = round_manager.start_round()

# Add tracker call
tracker.start_round(
    round_number=round_manager.round_number,
    initiative_data=initiative_data
)
```

## Step 5: Turn-Level Integration (6-Step Process)

This is where the most detailed tracking happens. Here's how to integrate each step:

### Turn Start

```python
# Your existing turn setup
proactor = turn_queue[0]
reactor = turn_queue[1]

# Add tracker call
tracker.start_turn(
    turn_number=turn_number,
    proactor=proactor,
    reactor=reactor
)
```

### Step 1: Proactor Interpretation

```python
# Your existing Step 1 logic
if proactor.is_user_actor:
    user_input = input("What do you want to do? ")
    proactor_action_data = conductor.interpret_user_action(user_input, proactor, scene_context)
else:
    proactor_action_data = conductor.determine_nua_proaction(proactor, reactor, scene_context)

# Add tracker call (capture the LLM interaction data)
tracker.track_step1_proactor_interpretation(
    agent_type="InterpreterAgent" if proactor.is_user_actor else "DeciderAgent",
    input_data={
        "user_action": user_input if proactor.is_user_actor else None,
        "scene_context": scene_context,
        "actor_sheet_data": proactor_sheet_data
    },
    llm_interaction={
        "model_used": "your_model_name",  # Get from your agent
        "prompt_sent": "full_prompt_text",  # Get from your agent
        "raw_response": "raw_llm_response",  # Get from your agent
        "processing_time": processing_time  # Measure this
    },
    normalized_output=proactor_action_data,
    enriched_factors=enriched_factors  # From your enrichment process
)
```

### Step 2: Proactor Success

```python
# Your existing Step 2 logic
success_data = _calculate_detailed_success(proactor, proactor_action_data, conductor)
attempt_narrative = _generate_attempt_narrative(proactor, proactor_action_data, success_data)

# Add tracker call
tracker.track_step2_proactor_success(
    calculation_breakdown=success_data,
    attempt_narrative=attempt_narrative
)
```

### Step 3: Reactor Interpretation

```python
# Your existing Step 3 logic
reactor_action_data = conductor.determine_nua_reaction(reactor, proactor, proactor_action_data, scene_context)

# Add tracker call
tracker.track_step3_reactor_interpretation(
    agent_type="DeciderAgent",
    input_data={
        "proactor_action": proactor_action_data,
        "scene_context": scene_context,
        "reactor_sheet_data": reactor_sheet_data
    },
    llm_interaction={
        "model_used": "your_model_name",
        "prompt_sent": "full_prompt_text",
        "raw_response": "raw_llm_response",
        "processing_time": processing_time
    },
    normalized_output=reactor_action_data,
    enriched_factors=enriched_factors
)
```

### Step 4: Reactor Success

```python
# Your existing Step 4 logic
reactor_success_data = _calculate_detailed_success(reactor, reactor_action_data, conductor)
reactor_attempt_narrative = _generate_attempt_narrative(reactor, reactor_action_data, reactor_success_data)

# Add tracker call
tracker.track_step4_reactor_success(
    calculation_breakdown=reactor_success_data,
    attempt_narrative=reactor_attempt_narrative
)
```

### Step 5: Exchange Resolution

```python
# Your existing Step 5 logic
exchange = Exchange(proactor, reactor, proactor_action_data, reactor_action_data)
exchange_results = exchange.execute()
outcome_data = _build_comprehensive_outcome_data(proactor, reactor, proactor_action_data, reactor_action_data, exchange_results)

# Add tracker call
tracker.track_step5_exchange_resolution(
    exchange_calculation={
        "proactor_final_success": exchange_results.get("proactor_success", 0),
        "reactor_final_success": exchange_results.get("reactor_success", 0),
        "winner": exchange_results.get("winner", "draw"),
        "success_difference": exchange_results.get("success_difference", 0)
    },
    status_shifts=outcome_data.get("status_shifts", {}),
    self_effects_applied=outcome_data.get("applied_self_effects", [])
)
```

### Step 6: Narrative Outcome

```python
# Your existing Step 6 logic
final_narrative = narrator.narrate_turn_outcome(outcome_data, scene_context)

# Add tracker call
tracker.track_step6_narrative_outcome(
    agent_type="NarratorAgent",
    input_data={
        "outcome_data": outcome_data,
        "scene_context": scene_context
    },
    llm_interaction={
        "model_used": "your_model_name",
        "prompt_sent": "full_prompt_text",
        "raw_response": "raw_llm_response",
        "processing_time": processing_time
    },
    final_narrative=final_narrative
)
```

### Turn Completion

```python
# Your existing turn completion logic
reporter_output = reporter.report_step6_narrative_outcome(final_narrative, outcome_data)

# Add tracker call
tracker.complete_turn(proactor, reactor, reporter_output)
```

## Step 6: Session Management

### Auto-Save (Optional)

Add periodic auto-saves:

```python
# After each turn or exchange
tracker.auto_save()
```

### Session End

At the end of the simulation:

```python
# Your existing cleanup
print("Simulation ended.")

# Add tracker call
tracker.end_session()
```

## Step 7: Using Historical Data

### Generate Context for LLMs

To provide historical context to LLM prompts:

```python
# Get recent context for better LLM decisions
historical_context = tracker.get_context_for_llm(lookback_turns=5)

# Include in your prompt
enhanced_prompt = f"""
{your_existing_prompt}

{historical_context}

Based on this history, please...
"""
```

### Query Actor History

```python
# Get complete history for an actor
actor_id = f"actor_{actor.sheet.name.lower().replace(' ', '_')}"
history = tracker.get_actor_history(actor_id)

# Use for character development or consistency checking
for turn_data in history:
    print(f"Turn {turn_data['turn_id']}: {turn_data['role']}")
```

### Load Previous Sessions

```python
# Resume a previous session
if tracker.load_session("previous_session_id"):
    print("Session loaded successfully!")
    # Continue from where you left off
```

## Integration Checklist

- [ ] Import TrackerAgent in main.py
- [ ] Initialize tracker at simulation start
- [ ] Add session start/end calls
- [ ] Add scene start/conclude calls
- [ ] Add exchange start/conclude calls
- [ ] Add round start calls
- [ ] Add all 6 turn step tracking calls
- [ ] Add turn start/complete calls
- [ ] Add auto-save calls (optional)
- [ ] Test that simulation runs exactly as before
- [ ] Verify data is being saved to simulation_data/ directory

## File Structure After Integration

```
Realitas Neo/
├── simulation_data/           # Created automatically
│   ├── sessions/
│   │   └── session_[UUID].json
│   ├── actors/
│   ├── analytics/
│   └── backups/
├── agents/
│   ├── tracker_agent.py      # Your new tracker
│   └── ... (existing agents)
├── main.py                   # Modified with tracker calls
└── ... (all other files unchanged)
```

## Important Notes

1. **No Logic Changes**: The tracker only observes and records - it never changes simulation behavior
2. **Performance**: Tracking adds minimal overhead (just JSON serialization)
3. **Storage**: Data files are human-readable JSON for easy inspection
4. **Error Handling**: If tracker fails, simulation continues normally
5. **Backwards Compatible**: Can be added/removed without affecting existing saves

## Testing Integration

1. Run your simulation as normal
2. Check that `simulation_data/sessions/` contains a new JSON file
3. Verify the simulation behaves exactly as before
4. Inspect the JSON file to see captured data
5. Test loading historical context with `get_context_for_llm()`

The tracker is now ready to eliminate context window limitations and provide comprehensive simulation history!
