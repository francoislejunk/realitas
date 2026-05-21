UTAS Core Gameplay Loop
A UTAS simulation proceeds in a series of Turns. Each Turn is composed of three sequential Phases.

1. Start of Turn Phase
1.1. Scene Update: The LLM describes the current situation.
1.2. Initiative Roll: The LLM rolls for initiative for all actors.
Initiative Score = Swiftness + Serendipity Roll
1.3. Initiative Tie-Breakers:
Highest Swiftness: The actor with the higher base Swiftness acts first.
Multi-Headed Coin Toss: If still tied, the order is resolved by sequential random selection.
2. Turn Execution Phase
The LLM executes a Turn for each actor according to the initiative order. Each Turn is resolved using the six Action Resolution Steps:

Step 1: Interpret Proactor's Action
Step 2: Calculate Proactor's Success & Narrate
Step 3: Interpret Reactor's Reaction
Step 4: Calculate Reactor's Success & Narrate
Step 5: Calculate Final Outcome & Update Statuses
Step 6: Generate Final Narrative Description
3. End of Turn Phase
This phase begins after the last actor's turn is complete.

3.1. Resolution Check: The LLM determines if the conflict is over.
3.2. Status Decay: The LLM resolves temporary status effects.
Once this phase is complete, the simulation loops back to the Start of Turn Phase for the next Turn, unless the conflict has been resolved.

Example of SIMULATION:
Scene Description
You find yourself in a toy store, the air filled with the faint scent of plastic and cardboard. Your mission: acquire the coveted G.I. Joe action figure, Commander Cobra, for your son, Jimmy. You navigate to the action figure aisle, and there it is—the very last one, pristine in its packaging. Unfortunately, a woman with a determined look in her eyes is standing right next to you, clearly after the same toy. You both know you're here for your kids, but only one of you will go home with it. Conflict is imminent.

TURN 1
START OF TURN PHASE - INITIATIVE AND INITIATIVE TIE BREAKER (IF NEEDED)

John Smith's Initiative: Swiftness (2) + Serendipity (2D6-7 -> 7-7=0) = 2
Unknown Lady's Initiative: Swiftness (3) + Serendipity (2D6-7 -> 8-7=+1) = 4
Turn Order: Unknown Lady (Proactor) -> John Smith (Reactor)

STEP1 - PROACTOR ACTION INTERPRETATION (In this case, the Proactor is the Unknown Lady)

(IF NUA THEN LLM DECIDES ON ACTION)(IF UA THEN ASK USER FOR ACTION THEN PROCEED)
Actor Sheet:
┌─────────────────────────────────────────────────────────┐
│ 🎭 Unknown Lady (NUA) │
│ ═══════════════════════════════════════════════════════ │
│ 🧠 quick-tempered (Internal) • 🎯 stoic (External) │
│ 💼 Worker                   Affiliation: None            │
│ 🎯 Goal: Buy a present for her son                           │
├─────────────────────────────────────────────────────────┤
│ ⚡ CORE ATTRIBUTES │
│ Swiftness: Average(3) │ Sociability: Subpar(2) │ Sturdiness: Extraordinary(4) │
│ Smarts: Average(3) │ Shadow: Minimal(1) │
├─────────────────────────────────────────────────────────┤
│ 💪 STATUS & CONDITION │
│ Stamina: █████ 5/5 Superb (-2) │
│ Spirit: █████ 5/5 Superb (-2) │
│ Supply: █████ 5/5 Superb (-2) │
├─────────────────────────────────────────────────────────┤
│ 🛠️  SKILLS & ABILITIES │
│ • Acrobatics: Subpar (2) │
└─────────────────────────────────────────────────────────┘
LLM Action: Snatching the Commander Cobra action figure off the shelf before you can.
Continuity Check: (Repeat until the action is valid)
Judgement: (Repeat until the action is valid)
Continuity Narrative Justification: (Repeat until the action is valid)
Proactor: Unknown Lady
Interpreted Action: Seeing you as direct competition, the Unknown Lady decides to act decisively. She will attempt to quickly snatch the Commander Cobra action figure off the shelf before you can.
UTAS Factors:
Exchange Type: Supply (The conflict is over a tangible resource).
Targeted Reactor Status: Supply.
S-Trait: Swiftness (3). The action is primarily about speed and reflexes.
Skill: Acrobatics (3).
Justification: While not a direct "grabbing" skill, Acrobatics represents her overall physical agility, coordination, and ability to perform a quick, precise physical maneuver, which is directly applicable to snatching an item before someone else can react.
Endowment: None (0).
Supplement: None (0).
Stress Level: 2 (Subpar). Grabbing a toy is simple, but doing so while being contested by someone right next to her adds a minor level of difficulty.
Shift Type (on Reactor): Lasting. If she succeeds, your access to this specific resource is permanently lost for this scene.
Shift Polarity (on Reactor): Subtractive. A successful action will take away from your potential resources.
Possible Self-inflicted Action Effects (for Unknown Lady):
Effect 1:
Possible Self-Effect Condition: On Action Success.
Possible Self-Inflicted Target Status: Spirit.
Possible Proactor Polarity Shift: Additive (A feeling of victory/relief).
Possible Proactor Type Shift: Temporary.
Self-Effect Severity: 1. (Initial Base Magnitude from table is 1 for Stress 2 Success. The narrative doesn't warrant an adjustment).
Effect 2:
Possible Self-Effect Condition: On Action Failure.
Possible Self-Inflicted Target Status: Spirit.
Possible Proactor Polarity Shift: Subtractive (A feeling of frustration).
Possible Proactor Type Shift: Temporary.
Self-Effect Severity: 1. (Initial Base Magnitude from table is 1 for Stress 2 Failure. The narrative doesn't warrant an adjustment).

STEP 2 - Calculate Proactor's Success & Narrate

Proactor Action Successes Calculation:
(S-Trait: 3 + Skill: 3 + Endowment: 0 + Supplement: 0 + Serendipity: +4) - (Stress Modifier: -1 + Status Modifier: 0) = 11
Narrative of Proactor's Attempt:
The Unknown Lady initiates a Subpar difficulty attempt at snatching the last Commander Cobra figure, focusing on your Supply. To achieve this, she employs her Average Acrobatics and Average Swiftness. This action is undertaken with Extraordinary Serendipity.

Step 3: REACTOR ACTION INTERPRETATION (In this case, the Reactor is John Smith)

┌────────────────────────────────────────────────────────┐
│ 🎭 John Smith (UA) │
│ ═══════════════════════════════════════════════════════ │
│ 🧠 Shrewd (Internal) • 🎯 Altruistic (External) │
│ 💼 Middle Management               Affiliation: Walmart │
│ 🎯 Goal: Buy a present for his son │
├─────────────────────────────────────────────────────────┤
│ ⚡ CORE ATTRIBUTES │
│ Swiftness: Average(3) │ Sociability: Subpar(2) │ Sturdiness: Average(2) │
│ Smarts: Average(3) │ Shadow: Minimal(1) │
├─────────────────────────────────────────────────────────┤
│ 💪 STATUS & CONDITION │
│ Stamina: █████ 5/5 Superb (-2) │
│ Spirit: █████ 5/5 Superb (-2) │
│ Supply: █████ 5/5 Superb (-2) │
├─────────────────────────────────────────────────────────┤
│ 🛠️  SKILLS & ABILITIES │
│ • Fencing: Average (3) │
│ • Engineering: Average (1) │
│ • Business: Extraordinary (4) │
│ • Linguistics: Average (2) │
│ • Acting: Average (2) │
│ ENDOWMENT ABILITIES │
│ • Superstrength: Minimal (1) │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ 🎭 Kaelen (UA)                                          │
│ ═══════════════════════════════════════════════════════ │
│ 🧠 Determined (Internal) • 🎯 Confident (External)      │
│ 💼 Warrior                  Affiliation: Independent    │
│ 🎯 Goal: Protect the innocent                           │
├─────────────────────────────────────────────────────────┤
│ ⚡ CORE ATTRIBUTES                                      │
│ Swiftness: Competent(3) │ Sociability: Novice(2) │ Sturdiness: Expert(4) │
│ Smarts: Competent(3) │ Shadow: Beginner(1)              │
├─────────────────────────────────────────────────────────┤
│ 💪 STATUS & CONDITION                                   │
│ Stamina: ████░ 4/5 Energetic (+0)                      │
│ Spirit: ███░░ 3/5 Steady (+0)                          │
│ Supply: ██░░░ 2/5 Limited (+0)                         │
├─────────────────────────────────────────────────────────┤
│ 🛠️  SKILLS & ABILITIES                                 │
│ • Swordsmanship: Novice (2)                            │
│ • Intimidation: Beginner (1)                           │
├─────────────────────────────────────────────────────────┤
│ ✨ ENDOWMENT ABILITIES                                      │
│ • No supernatural abilities                             │
├─────────────────────────────────────────────────────────┤
│ 🎒 SUPPLEMENTS                                          │
│ • No equipment bonuses                                  │
├─────────────────────────────────────────────────────────┤
│ 💝 SYMPATHIES                                           │
│ • No special relationships                              │
└─────────────────────────────────────────────────────────┘

User Action: I try to guilt trip her into hesitating her action by saying: "are you sure that's the example you want to give your kid? Snatching a toy like an uncivilized wild animal?!"
Continuity Check: (Repeat until the action is valid)
Judgement: (Repeat until the action is valid)
Continuity Narrative Justification: (Repeat until the action is valid)
Reactor: John Smith (UA)
Intended Reaction: You attempt to use a sharp, guilt-inducing comment to psychologically interrupt the lady's physical action, targeting her resolve.
UTAS Factors:
Reaction Type: This is a Spirit-based reaction against a Supply-based action. You are using social/mental tactics to defend against a physical resource grab.
S-Trait: Sociability (3). The core of your action is interpersonal influence.
Skill: Acting (2).
Justification: This is the most relevant skill as you are putting on a performance of moral outrage to elicit a specific emotional response (guilt/hesitation), which is a form of social manipulation.
Endowment: None (0).
Supplement: None (0).
Primary Defensive Status: Spirit. You are drawing on your mental and social fortitude to execute this reaction.
Secondary Effect: None. Your action is entirely focused on negating her attempt; it does not include a separate counter-attack or self-buff.

STEP 4 - Calculate Reactor's Success & Narrate
Reactor Action Successes Calculation:
(S-Trait: 3 + Skill: 2 + Endowment: 0 + Supplement: 0 + Serendipity: +2) - (Stress Modifier: -1 + Status Modifier: 0) = 6
Narrative of Reactor's Attempt:
You initiate a Subpar difficulty attempt at snatching the last Commander Cobra figure, focusing on the Unknown Lady's Supply. To achieve this, you employ your Average Acting and Average Sociability. This action is undertaken with Extraordinary Serendipity.

STEP 5 - Calculate Final Outcome & Update Statuses

Reactor Reaction Successes Calculation:
The Unknown Lady's action was Stress Level 2 (Subpar), making it easier for you to react against.
Your current Spirit (3) provides no modifier to your roll.
(S-Trait: 3 + Skill: 2 + Endowment: 0 + Supplement: 0 + Serendipity: +2) - (Stressor Mod: +1 + Status Mod: 0) = 6 Reaction Successes.
Final Outcome Calculation:
Proactor Successes (Lady): 11
Reactor Successes (John): 6
Raw Success Difference: 11 - 6 = +5 (Proactor Wins).
Status Shift Calculation (John):
The Lady's successful action results in a Lasting, Subtractive shift to your Supply.
Shift Value: 5. Your Supply of 3 is reduced by 5, which is floored at 0.
Your new Supply is 0 (Bankrupt).
Status Shift Calculation (Lady):
Due to her success, the Lady's "On Action Success" self-effect is triggered.
She gains a Temporary, Additive shift of 1 to her Spirit.
Her new Spirit is 4 (Extraordinary).
STEP 6 - NARRATIVE TURN OUTCOME

Attempting to snatch the last Commander Cobra figure, the Unknown Lady is met by your sharp, guilt-inducing comment. You leverage your Average Sociability and Competent Acting with Subpar Serendipity to try and stop her.
However, her physical speed overcomes your psychological tactic. The Lady’s snatching succeeds, resulting in a Superb shift to your Supply. Your Supply changes from Average to Bankrupt.

Additionally, as a result of her actions, the Unknown Lady experiences a consequence: Following the success of her snatch, she undergoes a Minimal shift to her own Spirit as a rush of victory washes over her. Her Spirit changes from Average to Extraordinary.

SCENE RESOLUTION
The contest over the toy is decisively over. The Unknown Lady clutches the Commander Cobra action figure triumphantly, her will bolstered by her success. You are left empty-handed, the resource you came for now completely gone. The tense moment in the aisle has passed, leaving only the awkward aftermath.