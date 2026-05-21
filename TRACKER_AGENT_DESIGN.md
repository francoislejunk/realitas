# Tracker_Agent Data Schema Design

## Overview

The Tracker_Agent data schema is designed to capture every aspect of a UTAS simulation session with complete fidelity, enabling perfect reconstruction of any simulation state and providing comprehensive historical context that transcends LLM context window limitations.

## Schema Architecture

### Hierarchical Structure
```
Simulation Session
├── Initial Setup & Metadata
├── Scenes
│   ├── Scene Data & Context
│   └── Exchanges
│       ├── Exchange Metadata
│       └── Rounds
│           ├── Initiative System
│           └── Turns (6-Step Process)
│               ├── Step 1: Proactor Interpretation
│               ├── Step 2: Proactor Success Calculation
│               ├── Step 3: Reactor Interpretation
│               ├── Step 4: Reactor Success Calculation
│               ├── Step 5: Exchange Resolution
│               └── Step 6: Narrative Outcome
├── Session Statistics
└── Error Log
```

## Key Design Principles

### 1. Complete State Capture
- **Before/After Snapshots**: Every turn includes pre and post-turn actor sheet states
- **Mathematical Transparency**: All calculations are broken down step-by-step
- **LLM Interaction Logging**: Full prompts, responses, and processing metadata
- **Enrichment Tracking**: Both raw LLM output and enriched data with actual values

### 2. Temporal Consistency
- **UUID-based Tracking**: Every entity (session, scene, exchange, round, turn) has unique identifiers
- **ISO 8601 Timestamps**: Precise timing for all events
- **Sequential Numbering**: Clear ordering within each hierarchical level
- **Processing Time Tracking**: Performance monitoring for optimization

### 3. Multi-Agent Integration
- **Agent-Specific Data**: Captures inputs/outputs for each agent type
- **Model Attribution**: Tracks which AI model was used for each decision
- **Prompt Engineering**: Full prompt text for debugging and optimization
- **Response Normalization**: Both raw and processed LLM responses

### 4. Comprehensive Error Handling
- **Error Context**: Full situational data when errors occur
- **Recovery Actions**: Documentation of how errors were resolved
- **Validation Tracking**: Records of data validation and correction

## Data Categories Explained

### Session Level
- **Metadata**: Session identification, timing, versioning
- **Initial State**: Complete actor sheets at simulation start
- **Statistics**: Aggregated metrics for analysis and optimization

### Scene Level
- **Scene Elements**: Environment, NPCs, objectives from CreatorAgent
- **NUA Data**: Non-User Actor information and motivations
- **Scene Transitions**: How scenes connect and flow

### Exchange Level
- **Participant Tracking**: Which actors are involved
- **Outcome Classification**: Victory conditions and results
- **State Changes**: How the exchange affected the overall simulation

### Round Level
- **Initiative System**: Complete breakdown of initiative calculations
- **Turn Order**: Determined sequence of actions
- **Serendipity Tracking**: Random elements and their effects

### Turn Level (6-Step Process)
Each turn captures the complete UTAS process:

#### Step 1: Proactor Interpretation
- **Input Context**: User action (if applicable), scene state, actor data
- **LLM Processing**: Full prompt, response, and processing metadata
- **UTAS Factor Analysis**: Complete breakdown of action components
- **Self-Effects Prediction**: Anticipated consequences of the action

#### Step 2: Proactor Success Calculation
- **Mathematical Breakdown**: Every component of the success formula
- **Actual Values**: Enriched data from actor sheets
- **Narrative Generation**: Descriptive text of the attempt

#### Step 3: Reactor Interpretation
- **Response Analysis**: How the reactor interprets and responds
- **Strategic Decisions**: NUA decision-making process (if applicable)
- **Counter-Action Planning**: Reactive strategy formulation

#### Step 4: Reactor Success Calculation
- **Defensive Calculations**: Reactor's success formula breakdown
- **Comparative Analysis**: How reactor success relates to proactor

#### Step 5: Exchange Resolution
- **Winner Determination**: Mathematical comparison of success values
- **Status Shift Application**: Actual changes to actor sheets
- **Self-Effects Processing**: Application of inherent action costs

#### Step 6: Narrative Outcome
- **Story Generation**: Final narrative describing the exchange
- **Context Integration**: How the outcome fits into the larger story
- **Transition Setup**: Preparation for the next turn or scene

## Implementation Benefits

### For LLMs
- **Context Reconstruction**: Can access any previous simulation state
- **Consistency Checking**: Reference past decisions and outcomes
- **Pattern Recognition**: Learn from previous similar situations
- **Narrative Continuity**: Maintain story coherence across sessions

### For Code Systems
- **State Validation**: Verify simulation integrity
- **Debugging**: Trace any issue to its source
- **Performance Analysis**: Identify bottlenecks and optimization opportunities
- **Replay Capability**: Reconstruct any simulation state for testing

### For Users
- **Session History**: Review past decisions and outcomes
- **Character Development**: Track actor growth and changes
- **Story Archive**: Preserve complete narrative experiences
- **Analysis Tools**: Understand patterns in gameplay and outcomes

## File Storage Strategy

### JSON Format Benefits
- **Human Readable**: Easy to inspect and debug
- **LLM Compatible**: Natural language models can easily parse and understand
- **Structured Data**: Maintains relationships and hierarchy
- **Extensible**: Easy to add new fields without breaking existing data

### File Organization
```
simulation_data/
├── sessions/
│   ├── session_[UUID].json (complete session data)
│   └── session_[UUID]_summary.json (lightweight overview)
├── actors/
│   ├── actor_[ID]_history.json (cross-session actor development)
│   └── actor_[ID]_snapshots/ (detailed state history)
├── analytics/
│   ├── session_statistics.json (aggregated metrics)
│   └── pattern_analysis.json (behavioral insights)
└── backups/
    └── [timestamp]/ (versioned backups)
```

## Query and Retrieval Methods

### Context Reconstruction
- **Turn Lookup**: Find any specific turn by ID or criteria
- **State Restoration**: Rebuild actor sheets at any point in time
- **Narrative Threads**: Follow story arcs across multiple sessions
- **Decision Chains**: Trace cause-and-effect relationships

### Analysis Queries
- **Success Patterns**: Identify effective strategies and tactics
- **Character Development**: Track actor growth and change
- **Scene Effectiveness**: Evaluate which scenarios work best
- **System Performance**: Monitor processing times and error rates

### LLM Integration
- **Prompt Enhancement**: Include relevant historical context in prompts
- **Consistency Validation**: Check new decisions against past behavior
- **Narrative Coherence**: Ensure story elements align with history
- **Character Voice**: Maintain consistent personality across sessions

This schema provides the foundation for a truly persistent, comprehensive simulation tracking system that eliminates the limitations of context windows while providing unprecedented insight into the UTAS simulation process.
