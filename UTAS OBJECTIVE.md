# OUTDATED
This document is outdated and does not reflect the current UTAS implementation.

## UTAS OBJECTIVE
UTAS stands for Universal Turn-based Action System. It is a statistical model system that is used to resolve ALL actor exchanges (actions/reactions) within ANY context, social/psychological, combat, economical, etc. in the RealitasAI simulation. It is NOT a game, it is an alternate reality simulation -- a realita. It aims to strike a perfect balance between CONSISTENT realism and narrative immersion. All calculations are purely numerical and based on the 7 S-Factors to accomplish a statistical model of the simulated reality. At the same time, the system is designed to be flexible and extensible to accommodate new features and mechanics as needed in future as it grows while ALWAYS presenting the User with ONLY the narrative descriptors. This way the backend has a 100% consistent statistical model so it never "guesses/improvises" results. All this while presenting the User with narrative representations that also maintain that consistency without overwhelming with numbers or too much detail. IMPORTANT: Every single term used in this model is a term that is used in the Realitas simulation and is consistent with the narrative and realita state. If at any point a single term or calculation described in this document is not used in EXTREMELY STRICT ADHESION, the model will not work correctly and will BREAK the simulation. DO NOT deviate from this model in any way!

# Realitas Terminology, naming convention:
Realita: an instanced simulated reality, the world in which the UA and all other actors live.
Realitas: plural form of instanced simulated reality.
User: the person using the RealitasAI simulation.
Actor: this encompasses all the possible actors within the simulation, a UA, NUA, or INUA.
UA (user actor): the user's actor in the realita.
NUA (non-user actor): this encompasses ALL sentient beings that are NOT the UA (user actor). This includes but is NOT limited to: humans, animals (pets, guard dogs, wildlife), artificial intelligence (smart computers, autonomous robots, AI assistants, synthetic beings), and any other entity with intelligence, autonomy, and sentience.
INUA (inanimate non-user actor): this encompasses all the possible actors that are NOT the UA (user actor) or NUA (non-user actor). An inanimate actor in the realita, any object/environment/concept that acts but isn't alive or sentient.
Proactor: any actor that is initiating an action, especially during UTAS.
Reactor: any actor that is reacting to an proactor's actions, especially during UTAS.
To inhabit: the verb that conveys how the user experiences the realita. The user inhabits their UA to live in their landed realita.
To exchange: any action trade between actors. This could be combat, love making, socializing, even healing.
Actor Sheet: actor document to track and update an actor's updated state, inventory, and missions/goals.
Exchange: any action trade between actors. This could be combat, love making, socializing, or even healing.
Action Type: the type of action taking place with an intended effect that is either Lasting or Temporary to a Status.
Action Polarity: Indicates the intended action/reaction's effect on the actor's updated Status State. This can be either Subtractive or Additive.
Subtractive Action: an action that takes away from the actor's updated Status State. E.g. an insult will be Subtractive taking away from the actor's updated Spirit Status State.
Additive Action: an action that adds to the actor's updated Status State. E.g. a compliment will be Additive adding to the actor's updated Spirit Status State.
Status: a numeric value that represents the updated state of an actor's temporary state. There are 4 types of Status: Stamina, Spirit, Supply, and Sympathy. Only the first three are applicable to turn exchanges.
(Status) Shift: a change in an actor's updated Status State after an exchange.
Exchange Type: the type of exchange that is taking place. This can be either Spirit, Supply, or Stamina.
Turn: the most essential unit of time in UTAS and it dictates the basic actions/reactions and their outcomes. They can last anywhere from a THREE seconds to a THREE minutes depending on the action/context.
Exchange Scene: used to resolve a collection of turns and dictate when it's time to wrap up the situation and move on, or not.
## Action/Reaction S-Factors:
S-traits (min:0, max:5): There are only FIVE S-traits and they represent inherent traits of the Actor. They are NOT confined by one category, i.e. Swiftness is not confined to physical combat/feats, it is also used when needing to quickly swerve away from danger when driving or stock market trading. Every actor has these and every action/reaction is PRIMARILY governed by ONE of them. These are permanent and are applied equally to any actor. These can change but only through permanent events that are consistent with the events in the realita state. Only the most relevant (1) is chosen for the action/reaction roll. Since they are always picked by the LLM (AI), the LLM MUST STAY WITHIN THE ACTOR CAPABILITIES: The choice must be drawn from the actor’s sheet (no inventing traits!!!), ensuring statistical consistency. The 5 S-traits are:
Swiftness: Speed, precision, or agility (e.g., verbal rebuttal, dodging, quick strikes).
Sociability: Interaction, charming, or overall interpersonal connection (e.g., persuasion, charming, socializing).
Sturdiness: Power, endurance, or resilience (e.g., physical intimidation, heavy blows/lifting, bracing).
Smarts: Strategy or knowledge (e.g., outsmarting, crafting, strategizing).
Shadow: Stealth or deception (e.g., sneaking, feinting, manipulating).
Skills (min:0, max:5): There are any number of skills an actor possesses. Some actors will have many, while some just a few. They track the level of proficiency an actor possesses in a particular area. Every actor has a minimum of 5 knowledge/talent-based Skills on their actor sheet. Only the most relevant (1) is chosen for the action/reaction roll. If there isn't a relevant Skill for the action/reaction, use none (0).
How to Determine the “Most Relevant” skill
Direct Applicability (Primary)
Does the Skill's core definition or common understanding directly relate to the primary method or nature of the action being performed? Example: For "picking a lock," a "Lockpicking" skill is directly applicable. For "persuading a guard," a "Persuasion" or "Social Engineering" skill is directly applicable.
Supporting Contribution (Secondary)
If no Skill is directly applicable, consider if a Skill could plausibly and significantly support the execution of the action, even if it's not its primary purpose. The connection must be clear and contribute to the how of the action.
The Skill should enhance the effectiveness or method of the action in a tangible way. Example (for "quickly grabbing an item off a shelf"):
No "Quick Grabbing" skill exists.
"Acrobatics" (if defined as encompassing general agility, coordination, and quick reflexes for physical maneuvers) could be considered relevant as it supports the physical execution of a fast, precise grab.
"Sleight of Hand" (if defined as manual dexterity for subtle movements) could also be relevant for a deft, perhaps unnoticed, grab.
Give justification for your choice
If multiple skills apply pick the skill most specific to the action
Example: If an actor has "Melee Weapons" and "Swordsmanship," and is attacking with a sword, "Swordsmanship" is more relevant.
AVOID Overstretching definitions:
DO NOT force a Skill to fit if the connection is tenuous or metaphorical. The Skill must contribute to the statistical chance of success for the action as described. Example: "Cooking" would generally not be relevant to "intimidating a thug," unless the intimidation specifically involves a threat related to poisoned food prepared by the actor, and even then, "Intimidation" or "Deception" might be more primary.
Take Context into account
The current situation and the narrative intent of the action can influence which Skill is most relevant. Example: Is the "grab" a simple reach, or is it a desperate lunge across a gap where "Acrobatics" would be more critical?
Default to Null (0) if No Clear Relevance:
If no Skill on the actor's sheet offers a clear, justifiable contribution to the success of the specific action being attempted, the Skill value used is 0 ("Null Skill"). It is better to use Null Skill than to assign a tenuously related Skill.
Endowments (min:0, max:5): these track the level of supernatural powers of the Actor in a particular area. These aren't common abilities and are only available to a few select actors. Only the most relevant (1) is chosen for the action's roll, if it exists at all. If there isn't a relevant Endowment, use none (0).
Serendipity (min:-5, max:5): a 2D6-7 die roll result that reflects the level of luck of any given action/reaction.


2d6 (this is the value after rolling the 2d6)
2d6-7 (this is what it equates to for serendipity)




2
-5




3
-4




4
-3




5
-2




6
-1




7
0




8
+1




9
+2




10
+3




11
+4




12
+5







Status modifiers (min:3, max:-3): numerical modifier based on updated Stamina/Spirit/Supply Status.
Stress modifiers (min:2, max:-2): These are AI-decided numerical modifier based on action/reaction probability/difficulty with 0 representing no challenge and 5 representing almost impossible.
Successes (min:-∞, max:∞): numerical value that represents action against reaction outcome. Any positive results (>0) indicate an overall action/reaction Success, 0 represents a Failure.
Shift Types: a change in an actor's updated Status State after an exchange.
Lasting Status Shifts (Shift * 1): a more serious, long-term, sometimes lethal, change in an actor's updated Status State after an exchange.
Temporary Status Shifts (Shift * 0.5): a less serious, short-term, sometimes more blunt/superficial, change in an actor's updated Status State after an exchange.
Shift Polarity (Subtractive (Shift * -1) /Additive (Shift * 1)): Indicates the intended action/reaction's effect on the actor's updated Status State. E.g. an insult will be subtractive taking away from the actor's updated Spirit Status State, while a compliment will be additive adding to the actor's updated Spirit Status State.
Supplement: additional factors that can affect the action. A weapon, spell, potion, cover, etc.
## LLM Stress Levels Guidelines
Difficulty 1 (Minimal), Stressor modifier -2 (reverse subpar) (Action/reaction is routine, uncontested, or requires minimal effort given the actor’s capabilities. E.g. Opening an unlocked door, casual conversation)
Difficulty 2 (Subpar), Stressor modifier -1 (reverse minimal (Action/reaction is straightforward but involves minor effort or a low-risk obstacles. E.g. Climbing a short ladder, persuading a friend)
Difficulty 3 (Average), Stressor modifier 0 (null) (Action/reaction involves moderate effort, standard conditions, or a balanced contest with an opponent. E.g. Swinging a sword at a walking target, bartering)
Difficulty 4 (Extraordinary), Stressor modifier 1 (minimal)(Action/reaction faces notable resistance, complexity, or situational disadvantage. E.g. Dodging while off-guard, lockpicking under time pressure, skilled opposition)
Difficulty 5 (Superb), Stressor modifier 2 (subpar) (Action/reaction is highly demanding or near-impossible due to overwhelming odds, critical impairment, or environmental chaos. E.g. Hacking a secure system, disarming a bomb blindfolded, escaping a collapsing building)
## Status Types & Modifiers
Stamina (min:0, max:5): actor's updated physical/health integrity.
Spirit (min:0, max:5): actor's updated mental/spiritual integrity.
Supply (min:0, max:5): actor's updated resource/wealth integrity.
Sympathy (min:0, max:5): actor's updated social/psychological integrity with other individual actors. EACH SYMPATHY SCORE IS UNIQUE TO THE ACTOR ADRESSED AND NOT OTHERS. Also, they don't need to be reciprocal. John might have a Sympathy of 3 with Mary, but Mary might have a Sympathy of 2 with John.
Status Modifiers (min:3, max:-2): Status 0 = 3 modifier, Status 1 = 2 modifier, Status 2 = 1 modifier, Status 3 = 0 modifier, Status 4 = -1 modifier, Status 5 = -2 modifier
## Numerical-to-Narrative Descriptors
Level Descriptors: -5: "Superb Reverse", -4: "Extraordinary Reverse", -3: "Average Reverse", -2: "Subpar Reverse", -1: "Minimal Reverse", 0: "Null", 1: "Minimal", 2: "Subpar", 3: "Average", 4: "Extraordinary", 5: "Superb"
# Exchange types, Status Shift Types and Calculation
EXCHANGE TYPES: Regardless of what any Actor chooses to do, there are ONLY 3 exchange types that are interpreted by the AI before being converted into Status Shifts:
"Spirit" that covers any mental, psychological, or emotional exchanges
"Stamina" that covers any physical, bodily, or tangible exchanges
"Supply" that covers any economic, financial, or resource exchanges
STATUS SHIFT TYPES:
LASTING SHIFT: Full STATUS Shift applied, represents more permanent/severe harm
Calculated as: status_Shift * 1
Examples:
Stamina: targeting vital areas (throat punch, stab to heart)
Spirit: breaking someone's psyche
Supply: destroying livelihood, major fraud
TEMPORARY SHIFT: Half status_Shift applied (rounded down), represents temporary/minor harm
Calculated as: status_Shift * 0.5
Examples:
Stamina: subduing strikes (arm punch, leg sweep)
Spirit: temporary intimidation, mild insults
Supply: minor scams, temporary setbacks
IMPORTANT NOTES:
Status Shift Type is determined by INTENT, not action type.
Same action can be Lasting or Temporary depending on target and goal.
AI interprets severity based on narrative context.
## Handling Overkill and Negative Status
In the UTAS system, Status values (Stamina, Spirit, Supply) are strictly bounded between 0 and 5, representing an actor's integrity from "Collapsed" (0) to "Epic" (5). Shift calculations, including Reverses, must respect this range to maintain realism and narrative consistency. Overkill—where Shift exceeds an actor’s updated Status, pushing it below 0—requires specific handling to prevent illogical states (e.g., "more than Collapsed") and ensure the LLM can interpret outcomes correctly. The following guidelines apply:
### Overkill Status Shift Rules
**Shift Cap at Current Status:**
For both Lasting and Temporary Shift, the maximum Shift applied equals the target's updated Status value. Any excess Shift is discarded.
Example: If an actor has Stamina 2 and takes 5 Lasting Shifts, only 2 Shifts are applied, reducing Stamina to 0. The extra 3 is ignored.
**Reverse Shift Definition:**
A Reverse occurs when Status Shift < 0, indicating the actor’s action rebounds harmfully. A Reverse Shift equals the absolute value of the Shift, treated as Lasting Shift unless the narrative context specifies otherwise (e.g., a mental blunder might affect Spirit).
Like standard Shift, a Reverse Shift is capped at the actor’s updated relevant Status. Excess Shift does not push Status below 0.
Example: An actor with Stamina 2 and a -5 Shift (5 Reverse Shift) takes off 2 Shifts, reducing Stamina to 0; the extra 3 is discarded.
**Status Floor at 0:**
Under no circumstances can Status drop below 0. If a calculation yields a negative value (e.g., 2 - 5 = -3), the result is set to 0. This ensures the 0-5 range is never violated.
Example: Stamina 2 minus 5 Shift = 0, not -3.
**Status States at 0:**
A Status 0 (null) is a valid state, representing the absence of said status' integrity and it's represented differently depending on 1. Status Type (Stamina, Spirit, Supply) and 2. Shift Type (Lasting, Temporary).
Stamina 0 + Temporary = Unconscious
Stamina 0 + Lasting = Dead
Spirit 0 + Temporary = Unconscious
Spirit 0 + Lasting = Insane
Supply 0 + Temporary = Tapped out
Supply 0 + Lasting = Bankrupt
## Numerical-to-Narrative Formulas & Descriptors:
In order to deliver to the User a clear, concise, and consistent narrative of the exchanges, without the burden of soul-less numbers, the following formula is used: Numerical-to-Narrative Action Formula: "PROACTOR NAME" attempts a "Numerical-to-Narrative Descriptor Difficulty" difficulty "NOUN PROACTOR ACTION" directed at "REACTOR NAME" using their "Numerical-to-Narrative Descriptor Skill", "[IF Endowment>0 THEN Numerical-to-Narrative Descriptor Endowment", OTHERWISE omit variable] and "Numerical-to-Narrative Descriptor S-Trait" with "Numerical-to-Narrative Descriptor Serendipity", and a "Numerical-to-Narrative Descriptor Status Type Modifier" "Status Type" "[IF reverse THEN "Boost", OTHERWISE "Penalty"]".
Numerical-to-Narrative Action Formula Examples:
John (Skill > 0, Endowment > 0, Modifier -1): *Inputs: Skill 3 (Fencing), Endowment 1, S-Trait 2 (Swiftness), Serendipity 3, Stamina Modifier -1 *Output: "John attempts an Extraordinary difficulty punch directed at Mara in the face using their Average Fencing, Minimal Endowment and Subpar Swiftness with Average Serendipity, and a Minimal Reverse Stamina Boost."
No Endowment Case (Skill > 0, Endowment = 0, Modifier 0): *Inputs: Skill 3 (Acrobatics), Endowment 0, S-Trait 3 (Swiftness), Serendipity 2, Stamina Modifier 0 *Output: "Mara attempts an Extraordinary difficulty backflip directed at John using their Average Acrobatics and Average Swiftness with Subpar Serendipity, and a Null Stamina Penalty."
No Skill Case (Skill = 0, Endowment = 0, Modifier 0): *Imagine: "Mara shouts at John" (no applicable skill, just yelling). *Inputs: Skill 0, Endowment 0, S-Trait 1 (Sociability), Serendipity 1, Spirit Modifier 0 *Output: "Mara attempts an Average difficulty shout directed at John using their Null Skill and Minimal Sociability with Minimal Serendipity, and a Null Spirit Penalty."
Numerical-to-Narrative Reaction Formula: With "PROACTOR NAME" "PROACTOR ACTION", "REACTOR NAME" attempts a "Numerical-to-Narrative Descriptor Difficulty" difficulty "WHY FOR CHOSEN SKILL" using their "Numerical-to-Narrative Descriptor Skill", "[IF Endowment>0 THEN Numerical-to-Narrative Descriptor Endowment", OTHERWISE omit variable] and "Numerical-to-Narrative Descriptor S-Trait" with "Numerical-to-Narrative Descriptor Serendipity", and a "Numerical-to-Narrative Descriptor Status Type Modifier" "Status Type" "[IF reverse THEN "Boost", OTHERWISE "Penalty"]".
Numerical-to-Narrative Reaction Formula Examples:
Mara’s Reaction (Skill > 0, Endowment = 0, Modifier 0): *Inputs: Skill 3 (Acrobatics), Endowment 0, S-Trait 3 (Swiftness), Serendipity 2, Stamina Modifier 0 *Output: "With John punching Mara in the face, Mara attempts an Extraordinary difficulty backflip away from the punch using their Average Acrobatics and Average Swiftness with Subpar Serendipity, and a Null Stamina Penalty."
John’s Reaction (Skill > 0, Endowment > 0, Modifier -1): *Scenario: Mara punches, John reacts. *Inputs: Skill 3 (Fencing), Endowment 1, S-Trait 2 (Swiftness), Serendipity 3, Stamina Modifier -1 *Output: "With Mara punches John in the face, John attempts an Extraordinary difficulty parry with his sword using their Average Fencing, Minimal Endowment and Subpar Swiftness with Average Serendipity, and a Minimal Reverse Stamina Boost."
Mara’s Reaction (Skill = 0, Endowment = 0, Modifier 0): *Scenario: John punches, Mara yells back (no skill). *Inputs: Skill 0, Endowment 0, S-Trait 1 (Sociability), Serendipity 1, Spirit Modifier 0 *Output: "With John punches Mara in the face, Mara attempts an Average difficulty shout to intimidate using their Null Skill and Minimal Sociability with Minimal Serendipity, and a Null Spirit Penalty."
Numerical-to-Narrative Turn Outcome Formula: "With PROACTOR ACTION GERUND, [IF Proactor Successes > Reactor Successes THEN 'PROACTOR NAME overcomes REACTOR NAME’s REACTOR ACTION GERUND with a' ELSE IF Proactor Successes < Reactor Successes THEN 'REACTOR NAME overcomes PROACTOR NAME’s PROACTOR ACTION GERUND with a' ELSE 'PROACTOR NAME is neutralized by REACTOR NAME’s REACTOR ACTION GERUND with a'] [IF Proactor Successes < Reactor Successes & Shift Polarity = -1 THEN "Reverse"] "Numerical-to-Narrative Descriptor Shift" "Affected REACTOR Status Type" Shift causing REACTOR NAME's "Numerical-to-Narrative Descriptor Status Type" to go from "Current Numerical-to-Narrative Descriptor Status Type" to "Updated Numerical-to-Narrative Descriptor Status Type" with a "Numerical-to-Narrative Descriptor Status Type Modifier" "Status Type" "[IF reverse THEN "Boost", OTHERWISE "Penalty"]"."
Numerical-to-Narrative Turn Outcome Formula Examples: Setup: Proactor Action: "punching Mara in the face" Reactor Action: "backflipping away from the punch"
Example 1 - Proactor Wins (9 > 7): Shift: (9 - 7) * -1 * 0.5 = -1 Status: 3 - 1 = 2, Modifier 1 = "Minimal," ≥ 0 = "Penalty" Output: "With punching Mara in the face, John overcomes Mara’s backflipping away from the punch with a Minimal Reverse Stamina Shift causing Mara’s Stamina to go from Average to Subpar with a Minimal Stamina Penalty."
Example 2 - Reactor Wins (7 < 9): Shift: (7 - 9) * -1 * 0.5 = 1 Status: 3 + 1 = 4, Modifier: -1 (Status 4) = "Minimal Reverse," < 0 = "Boost" Condition: 7 < 9 & Polarity -1 = "Reverse" Output: "With punching Mara in the face, Mara overcomes John’s punching Mara in the face with a Reverse Minimal Stamina Shift causing Mara’s Stamina to go from Average to Extraordinary with a Minimal Reverse Stamina Boost."
Example 3 - Tie (8 = 8): Shift: (8 - 8) * -1 * 0.5 = 0 Status: 3 + 0 = 3, Modifier: 0 (Status 3) = "Null," ≥ 0 = "Penalty" Condition: 8 = 8 (no Reverse) Output: "With punching Mara in the face, John is neutralized by Mara’s backflipping away from the punch with a Null Stamina Shift causing Mara’s Stamina to go from Average to Average with a Null Stamina Penalty."
Numerical-to-Narrative Descriptors:
-5: "Superb Reverse"
-4: "Extraordinary Reverse"
-3: "Average Reverse"
-2: "Subpar Reverse"
-1: "Minimal Reverse"
0: "Null"
1: "Minimal"
2: "Subpar"
3: "Average"
4: "Extraordinary"
5: "Superb"
## Exchanges (Contested Actions), Turns and Scenes:
Exchanges (Contested Actions): Every time an Actor engages in an action that has any risk of failing and/or is contested in any way, the simulation registers it as an exchange and UTAS MUST be used.
Turns: turns are the most essential unit of time in UTAS and they dictate the basic actions/reactions and their outcomes. Each actor gets one action/reaction within each turn. Each turn can narratively last anywhere from a THREE seconds to a THREE minutes depending on the action/context.
Scenes: Scenes are used to resolve a collection of turns and dictate when it's time to wrap up the situation and move on, or not.
## Contest Resolution and Scene Transitions
In the UTAS system, every exchange—whether combat, persuasion, resource negotiation, or otherwise—is part of a contest that unfolds over turns. A scene resolves when the contest reaches a clear conclusion, allowing the simulation to transition smoothly to a new situation. To maintain narrative immersion and system consistency, the LLM must determine resolution based on the exchange type (Stamina, Spirit, Supply) and the actors’ intents.
IF a) CONTEST NOT YET RESOLVED THEN AUTOMATICALLY Next Turn with the opposite actor (NUA or UA, per turn order); b) OTHERWISE IF CONTEST ALREADY RESOLVED, 1) AUTOMATICALLY DESCRIBE NEW SCENE (Do NOT prompt or wait for user input!), 2) then PROMPT the User for what they want to do next ("What do you try to do?")
### Resolution Criteria by Exchange Type
**Stamina Exchanges (Physical):**
**Lasting Intent:** Resolved when one actor’s Stamina reaches 0 (e.g., unconsciousness, death) or an actor explicitly surrenders or flees, ending the physical contest.
**Temporary Intent:** Resolved when the stated goal is achieved or definitively thwarted:
Success Example: A grapple pins the opponent (Success > 0, narrative indicates restraint).
Failure Example: The opponent breaks free and escapes (Success ≤ 0, goal unachieved).
LLM Cue: Look for physical incapacitation, goal completion (e.g., "subdue"), or a clear cessation of conflict.
**Spirit Exchanges (Mental/Emotional):**
**Lasting Intent:** Resolved when one actor’s Spirit reaches 0 (e.g., mental breakdown, loss of will) or an actor concedes emotionally (e.g., "I give up").
**Temporary Intent:** Resolved when the emotional or psychological goal is met or blocked:
Success Example: Persuasion sways the target (Success > 0, target agrees or Shifts behavior).
Failure Example: The target resists or hardens their stance (Success ≤ 0, no change).
LLM Cue: Assess intent (e.g., "convince," "intimidate") and check if the narrative reflects a decisive Shift in the target’s state or relationship.
**Supply Exchanges (Resource/Economic):**
**Lasting Intent:** Resolved when one actor’s Supply reaches 0 (e.g., total depletion, ruin) or an actor abandons the economic struggle.
**Temporary Intent:** Resolved when the resource goal is secured or lost:
Success Example: A trade deal is struck (Success > 0, resources exchanged).
Failure Example: The deal falls apart or theft is foiled (Success ≤ 0, no gain).
LLM Cue: Evaluate the stated objective (e.g., "steal," "barter") and confirm if the resource outcome is conclusive.
### General Scene Resolution Guidelines
**Intent-Driven Closure:**
The LLM identifies the Proactor’s initial intent and measures success against it. A contest resolves when the intent is fulfilled (Success > 0) or rendered impossible (Success ≤ 0 or narrative barrier).
Example: Intent "steal the gem" resolves with the gem taken or secured beyond reach.
**Status Thresholds:**
If any relevant Status (Stamina, Spirit, Supply) hits 0, the contest ends immediately, reflecting incapacitation in that domain. Non-zero Status contests continue until intent is resolved.
**Mutual Cessation:**
If both actors stop pursuing the contest (e.g., both flee, agree to truce), the LLM deems it resolved, even without a clear winner, provided the narrative supports this pause.
**Narrative Finality:**
The LLM ensures the resolution feels conclusive by tying it to a narrative beat, e.g., "The argument ends with a cold stare" or "The thief vanishes into the crowd." Ambiguity is avoided by confirming the contest’s core tension is settled.
### Scene Transition Process
**Post-Resolution:**
Once resolved, the LLM describes the outcome using the Turn Outcome Description Formula, then Shifts to a new scene without prompting the user mid-contest.
Example: "Your words sway the merchant with Above Average success, securing the deal. The market bustle resumes around you. What do you do next?"
**Unresolved Contests:**
If the contest isn’t resolved (e.g., Success = 0, intent still viable), the LLM continues to the next turn (NUA or UA, per turn order) without transitioning.
### LLM Implementation Notes
The LLM must track the Proactor’s intent across turns and cross-check it against Success values and narrative outcomes.
For Temporary exchanges, resolution hinges on qualitative Shifts (e.g., agreement, escape) rather than just Status drops, ensuring flexibility without breaking the statistical model.
These rules maintain the backend’s consistency while delivering a seamless, narrative-driven experience to the user.
## Turn Order, Action/Reaction and Scene Resolution Process, Calculation Rules, Actor Sheets, Key Tables, and Examples
Key Tables:
Stress Levels (min:1, max:5):
Stress 1 (Minimal): Action is routine, uncontested, or requires minimal effort given the actor’s capabilities. E.g. Opening an unlocked door, casual conversation
Stress 2 (Subpar): Action is straightforward but involves minor effort or a low-risk obstacles. E.g. Climbing a short ladder, persuading a friend
Stress 3 (Average): Stress Modifier 0 (Action involves moderate effort, standard conditions, or a balanced contest with an opponent. E.g. Swinging a sword at a walking target, bartering)
Stress 4 (Extraordinary): Stress Modifier 1 (Action faces notable resistance, complexity, or situational disadvantage. E.g. Dodging while off-guard, lockpicking under time pressure, skilled opposition)
Stress 5 (Superb): Stress Modifier 2 (Action is highly demanding or near-impossible due to overwhelming odds, critical impairment, or environmental chaos. E.g. Hacking a secure system, disarming a bomb blindfolded, escaping a collapsing building)
Stress Modifiers (min:+2, max:-2):
Stress 1 = Stress Modifier -2
Stress 2 = Stress Modifier -1
Stress 3 = Stress Modifier 0
Stress 4 = Stress Modifier 1
Stress 5 = Stress Modifier 2
Status 0 (null) States:
Temporary Shift: Stamina 0 + = Unconscious
Lasting Shift: Stamina 0 + Lasting = Dead
Temporary Shift: Spirit 0 + Temporary = Unconscious
Lasting Shift: Spirit 0 + Lasting = Insane
Temporary Shift: Supply 0 + Temporary = Tapped out
Lasting Shift: Supply 0 + Lasting = Bankrupt
Status Modifiers (min:3, max:-2):
Status 0 = 3 Status Modifier
Status 1 = 2 Status Modifier
Status 2 = 1 Status Modifier
Status 3 = 0 Status Modifier
Status 4 = -1 Status Modifier
Status 5 = -2 Status Modifier
NUMERICAL-TO-NARRATIVE DESCRIPTORS:
-5: "Superb Reverse"
-4: "Extraordinary Reverse"
-3: "Average Reverse"
-2: "Subpar Reverse"
-1: "Minimal Reverse"
0: "Null"
1: "Minimal"
2: "Subpar"
3: "Average"
4: "Extraordinary"
5: "Superb"
Supplement Examples (min:1, max:5):
Baseball bat: +2
Pistol: +2
Healing potion: +1
Wall cover: +4
Knife: +1
Protection spell: +3

Scene Description Example: "You find yourself in a toy store in search for the coveted G.I. Joe action figure, Commander Cobra. You get to the action figure aisle and there it is, the very last piece. Unfortunately, there's a lady next to you who clearly is after the same toy. You're both here to buy a present for your kids, but only one of you will go home with it. Conflict ensues!"
## Actor Sheet
UA Sheet (Name, Last Name, AKA):
Name:
Internal & External personality:
Occupation:
Affiliation:
S-traits
Swiftness (1-5):
Sociability (1-5):
Sturdiness (1-5):
Smarts (1-5):
Shadow (1-5):
Skills (0-5):
Endowments (0-5):
Stamina (0-5): , Spirit (0-5): , Supply (0-5):
Actor 1 Sympathy (0-5), Actor 2 Sympathy (0-5), Actor 3 Sympathy (0-5)
UA Sheet Example: John Smith
Name: John Smith
Internal & External personality: Shrewd (Internal), Altruistic (External)
Occupation: Middle Management
Affiliation: Walmart
S-traits
Swiftness: 2
Sociability: 3
Sturdiness: 2
Smarts: 3
Shadow: 1
Skills: Fencing 3, Engineering 1, Business 4, Linguistics 2, Acting 2
Endowments: Superstrength 1
Status: Stamina: 4 with status modifier -1, Spirit: 3 with status modifier 0, Supply: 3 with status modifier 0
Jimmy (son) Sympathy 4, Unknown Lady Sympathy: 2
Life Goal: "Climb the corporate ladder to become the CEO at Walmart"
Key Memories:
John succeeded in surviving an Alien abduction that gave him an Endowment (Superstrength)
John succeeded in coercing a more timid co-working into giving up his parking spot.
John failed to acquire custody of his kid after a long custody battle.
NUA Sheet Example: Unknown Lady
Name: Unknown
Internal & External personality: Good-hearted (Internal), Tough (External)
Occupation: Nurse
Affiliation: NYC Hospital
S-traits
Swiftness: 3
Sociability: 1
Sturdiness: 2
Smarts: 1
Shadow: 3
Skills: Acrobatics 3, Cooking 1, Painting 4, Nursing 4, Geography 2
Endowments: None
Status: Stamina: 3 with status modifier 0, Spirit: 3 with status modifier 0, Supply: 3 with status modifier 0
Timmy (son) Sympathy 5, Unknown John: 2
Life Goal: "Have a peaceful life with her family"
Key Memories:
Unknown Lady succeeded in becoming the hospital's head nurse.
Unknown Lady succeeded in charming her boyfriend into marrying her.
Unknown Lady failed to pay her bills this month.
EXCHANGE 
KEY POINTS TO REMEMBER:
Serendipity will now be rolled **separately for each distinct calculation** where it is a factor. This means:
A **unique Serendipity roll (2D6-7)** will be generated for the **Proactor's Initiative Score** calculation. 
A **unique Serendipity roll (2D6-7)** will be generated for the **Reactor's Initiative Score** calculation. 
A **unique Serendipity roll (2D6-7)** will be generated for the **Proactor's Action Successes** calculation. 
A **unique Serendipity roll (2D6-7)** will be generated for the **Reactor's Reaction Successes** calculation.
This ensures that each instance of "luck" is distinct and independently calculated.

A single action can now potentially affect **multiple relevant Statuses** on the **Target**. 
* When interpreting an action, the **LLM will identify ALL Status types (Stamina, Spirit, Supply, Sympathy) that are narratively applicable** to the action's intended and actual effects on the Target. 
* **Shift calculations will be applied to EACH of these identified relevant Statuses independently.** 
* The **Numerical-to-Narrative Turn Outcome Formula** will describe the resulting **Shift for ALL affected Statuses**, adhering to the existing rules for Shift Polarity, Shift Type, and Overkill/Negative Status handling for each.\

Any numerical result for a `Status Shift` calculation must now be **rounded up** if it results in a non-integer value. This means: * For positive shifts, `0.5` becomes `1`. * For negative shifts, `-0.5` becomes `0` (due to the Status Floor at 0 rule, but the internal calculation would round up to the nearest integer value greater than or equal to the number). * This applies to **both Lasting and Temporary Shifts**, and respects the **Status Floor at 0** rule for final Status values.

In the **Numerical-to-Narrative Turn Outcome Formula**, if a **Target's Status value does NOT change** after an exchange (e.g., due to a calculated Shift of 0, or because the Overkill rules prevented a change below 0 or above 5), the narrative descriptor will be modified. Instead of: "causing [TARGET NAME]'s [Status Type] to go from [Current Numerical-to-Narrative Descriptor Status Type] to [Updated Numerical-to-Narrative Descriptor Status Type]..." It will state: "**causing no change to [TARGET NAME]'s [Status Type]**." 

THE STEPS OF AN EXCHANGE:
UTAS Core Gameplay Loop
A UTAS simulation proceeds in a series of Rounds. Each Round is composed of three sequential Phases.
1. Start of Round Phase
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
Step 5: Calculate Turn Outcome & Update Statuses
Step 6: Generate Turn Narrative Description
3. End of Round Phase
This phase begins after the last actor's turn is complete.
3.1. Resolution Check: The LLM determines if the conflict is over.
3.2. Status Decay: The LLM resolves temporary status effects.
Once this phase is complete, the simulation loops back to the Start of Round Phase for the next Round, unless the conflict has been resolved.
Take Notes: 
When outputting information all “_” must be taken away for better readability all “_” are simply for back-end processes and should not be seen during ANY and ALL outputs made going forward. Example: DO NOT show: Proactor_Action_Successes" "INSTEAD show: Proactor Action Successes"
NEVER decide for the UA whenever the UA plays a role in the turn whether as the proactor or reactor THEY must always decide their actions NEVER the LLM.
C. End of Round Phase
End of Round Trigger: This phase is reached when the Turn Queue is empty.
Apply End-of-Round Effects: Any effects that trigger at the end of a round (such as poison, regeneration, or environmental effects) are resolved now.
Loop to New Round: The system loops back to Phase A to begin the next round.



Step 1 - LOAD CURRENT ACTOR, GIVE CONTEXT, REGISTER & INTERPRET ITS ACTION INTO UTAS FACTORS:
	* IF UA NOW (Current Actor is UA):
* Present updated exchange description to the User. 
* Present UA Sheet. 
* PROMPT User for action: "What do you try to do?" 
* USER INPUTS ACTION.
* Access Exchange Description, UA Action, UA Sheet Data & NUA Sheet Data (for potential Reactor). 
* INTERPRET UA's Action into UTAS Factors (S-Trait, Skill, Endowment, Supplement,  Serendipity(not an action roll it is a luck roll aimed at attaining a certain level of chance or surprise), Stress Level, Stress Modifier, Status Type, Current Status Modifier, Shift Type, Shift Polarity, Target status/s) & give reasons why.
"When you, the LLM, interpret the Proactor's declared action, you must consider not only its intended effects on any Reactor (or the environment) but also the potential direct consequences the action could have on the Proactor themselves.
For each action the Proactor takes, you need to determine if there are any plausible Possible Self-inflicted Action Effects. If so, for each distinct Possible Self-inflicted Action Effects, you must define the following five characteristics:
Possible Self-Effect Condition [code name:Self_Effect_Condition *do not show the code name*] (When does this self-effect occur?):


Analyze the nature of the Proactor's action. Does this self-effect happen:
Inherent Cost: Simply by performing the action, regardless of its success or failure against a Reactor or a challenge? (e.g., casting a draining spell always costs Stamina; a morally compromising action always impacts Spirit).
On Action Success: Only if the Proactor's primary action is successful? (e.g., a surge of confidence (Spirit) from a successful intimidation; feeling invigorated (Stamina) after a successful athletic feat).
On Action Failure: Only if the Proactor's primary action fails? (e.g., physical injury (Stamina) from a failed jump; humiliation (Spirit) from a social gaffe; loss of materials (Supply) from a bungled crafting attempt).
You must choose one of these three conditions for each self-effect.
Possible Self-Inflicted Target Status (Which of the Proactor's own Statuses is affected?):


Based on the narrative of the self-effect, identify which of the Proactor's Statuses will change. This will be one of:
Stamina
Spirit
Supply
(Sympathy can only be considered if the self-inflicted effect is a profound internal psychological shift directly related to the Proactor's relationship with a specific other actor, and this must be strongly justified).
An action might have multiple self-effects, each targeting the same or different Statuses. For example, failing a jump could affect Stamina (injury) AND Spirit (embarrassment).
Possible Proactor Polarity Shift [code name:Shift_Polarity_Proactor *do not show the code name*] (Does the Status increase or decrease?):


Determine if the effect on the Proactor's identified Self-Inflicted Target Status is:
Additive: The Status value increases.
Subtractive: The Status value decreases.
Possible Proactor Type Shift [code name:Shift_Type_Proactor *do not show the code name*] (Is the effect Lasting or Temporary?):


Consider the narrative duration or significance of the self-effect:
Lasting: Represents a more significant, persistent change.
Temporary: Represents a more fleeting or minor change.
Possible Self-Effect Severity [code name:Final_Base_Magnitude_Self *do not show the code name*] (How severe is this specific self-effect?):


To determine this value (which will be a number from 1 to 4), follow this two-step process:
A. Determine Initial_Base_Magnitude_Self from the Table:


Use the Self_Effect_Condition you just identified and the Proactor_Action_Stress_Level (provided as context for the Proactor's action).


Refer to the following table:


Self_Effect_Condition
Proactor_Action_Stress_Level
Initial Base_Magnitude_Self
Inherent Cost
Any
1
On Success
1-2 (Minimal, Subpar)
1
On Success
3 (Average)
1
On Success
4 (Extraordinary)
2
On Success
5 (Superb)
2
On Failure
1 (Minimal)
1
On Failure
2 (Subpar)
1
On Failure
3 (Average)
1
On Failure
4 (Extraordinary)
2
On Failure
5 (Superb)
3




Note for Inherent Cost: If the action description itself specifies a higher cost (e.g., "this powerful spell costs 2 Stamina"), use that as the Initial_Base_Magnitude_Self. Otherwise, default to 1.


Note for On Success (Stress 3, 5) & On Failure (Stress 3, 4, 5): The table provides a starting point. Your narrative adjustment in the next step is key.


B. Apply LLM Narrative Adjustment:


Based on the specific narrative details of the Proactor's action and the likely self-inflicted outcome, decide if the Initial_Base_Magnitude_Self from the table needs adjustment:
If the narrative suggests the self-effect is more impactful or severe than typical for that Stress Level and Condition, apply an adjustment of +1.
If the narrative suggests the self-effect is less impactful or severe, apply an adjustment of -1.
If the initial magnitude seems appropriate for the narrative, apply an adjustment of 0.
Calculate: Adjusted_Base_Magnitude = Initial_Base_Magnitude_Self + LLM_Adjustment_Value.
The Final_Base_Magnitude_Self is this Adjusted_Base_Magnitude, but it must be clamped between 1 (minimum) and 4 (maximum). (A magnitude of 4 should only be used for truly exceptional and narratively significant self-effects, typically arising from Stress Level 5 failures or exceptionally justified Inherent Costs/Successes).
You must provide a brief justification for your chosen adjustment value if it is not 0.
Output Requirement for the LLM:
For each Proactor action, you will output a list of all identified self-inflicted effects. Each entry in the list must clearly state all five characteristics determined above:
Possible Self-Effect Condition
Possible Self-Inflicted Target Status
Possible Proactor Polarity Shift
Possible Proactor Type Shift
Self-Effect Severity (and justification for any narrative adjustment from the table's initial value).
Example of LLM's Thought Process & Output (for "Risky Leap" at Stress Level 4):
Proactor Action: "I'm going to try a risky leap across the crumbling rooftop to get away!" (Stress Level 4)
LLM Thinking:
Okay, "Risky Leap." What happens to the Proactor?
If they succeed: They'd feel pretty good, a rush of adrenaline. That's Spirit. Condition: On Action Success. Polarity: Additive. Type: Temporary (adrenaline fades). Magnitude? Stress 4 Success table is 2. Narrative: "Risky leap," success is significant. Adjustment +0. Final Magnitude: 2.
If they fail: They could fall, get hurt. That's Stamina. Condition: On Action Failure. Polarity: Subtractive. Type: Temporary (scrapes, bruises) unless it's a really bad fall, then Lasting. Let's say Temporary for now. Magnitude? Stress 4 Failure table is 2. Narrative: "Crumbling rooftop," failure could be nasty. Adjustment +0 (or +1 if I want to emphasize danger). Final Magnitude: 2.
If they fail: They might also feel foolish or scared. That's Spirit. Condition: On Action Failure. Polarity: Subtractive. Type: Temporary. Magnitude? Stress 4 Failure table is 2. Is this as bad as getting hurt? Maybe slightly less. Initial 2. Adjustment -1 for "less impactful than the physical damage." Final Magnitude: 1.
* CODE SAVES UA ACTION DATA. 
* ELSE (Current Actor is NUA/INUA - the Proactor for this turn): * Access Updated Exchange Description & NUA/INUA Sheet. * LLM INTERPRETS NUA/INUA Exchange Goal & Decides Action. * LLM INTERPRETS NUA/INUA Action into UTAS Factors (S-Trait, Skill, Endowment, Supplement, Serendipity, Stress Level, Stress Modifier, Status Type, Current Status Modifier, Shift Type, Shift Polarity, Target status/s) & give reasons why. // For effects on Reactor // 

Determine Possible Self-inflicted Action Effects for NUA/INUA Proactor: "The LLM then follows the same procedure as detailed above (in the 'IF UA NOW' section) for identifying and defining potential Possible Self-inflicted Action Effects effects on the NUA/INUA Proactor. This includes determining the Self_Effect_Condition, Possible Self-Inflicted Target Status, Shift_Polarity_Proactor, Shift_Type_Proactor, and Final_Base_Magnitude_Self for each potential self-effect." 
* CODE SAVES NUA/INUA ACTION DATA.

Step 2 - IF REACTOR IS NUA/INUA: LLM DETERMINES REACTOR'S REACTION INTENT
A. OVERVIEW:
 This step is performed if the current Reactor (the one responding to the Proactor's action) is an NUA (Non-User Actor) or INUA (Independent Non-User Actor). Its purpose is for the LLM to decide on a high-level reaction intent for this NUA/INUA based on the current situation and the NUA/INUA's characteristics.
B. LLM TASK: DETERMINE NUA/INUA REACTOR'S REACTION INTENT
1. Access and Consider Context: As the LLM, you must first understand the situation. You will be provided with, and should consider: 
* `Proactor_Action_Data` (from Step 1):
* The Proactor's identity. 
* A full description of what the Proactor is doing (e.g., "casting a menacing shadow spell"). 
* The `Targeted_Reactor_Status_Type` (e.g., Spirit). 
* The `Proactor_Action_Stress_Level` (indicating how difficult or threatening the Proactor's action is). 
* Current Scene Description: The environment, other characters present, and the overall mood or stakes. 
* NUA/INUA Reactor's Profile:
* Current Status values (Stamina, Spirit, Supply, Sympathy). * Known Skills, S-Traits, and Endowment abilities. 
* Defined personality traits, motivations, and current goals. 
* Any active conditions or effects influencing them (e.g., "frightened," "injured," "determined"). 
2. **Decide on a Reaction Intent:** 
Based on your understanding of the context and the NUA/INUA Reactor's profile, determine: 
* **Immediate Goal:** What is the NUA/INUA Reactor's most likely immediate objective in response to the Proactor's action? (e.g., self-preservation, protecting an objective, retaliating, de-escalating, gaining an advantage).
* **Plausible Reaction:** What is the most logical and in-character *type* of reaction the NUA/INUA would attempt? This should be a conceptual description of their intended response, not yet broken down into game mechanics. 
* *Examples of Reaction Intents:* "Attempt to physically dodge the incoming projectile," "Try to mentally resist the fear effect," "Attempt to verbally challenge the Proactor's statement," "Prepare to launch a counter-offensive," "Use a known ability to create a barrier," "Try to quickly assess the situation before acting." 
3. **State the Chosen Reaction Intent:** 
Clearly articulate the NUA/INUA Reactor's chosen reaction intent. This statement will guide the more detailed mechanical breakdown in Step 4. 
* *Example of LLM's Stated Intent:* "Given the Proactor's attempt to intimidate, the NUA Reactor (Baron Von Hessler), known for his arrogance, will attempt to scoff dismissively and project an aura of unshakable confidence."
C. SYSTEM ACTION: RECORD REACTION INTENT
 * The NUA/INUA Reactor's chosen reaction intent, as stated by the LLM, is recorded by the system (e.g., as Reactor_Chosen_Reaction_Intent). This information is then passed to Step 4 for detailed mechanical interpretation.
 * If the Reactor is a UA, this step is skipped, and the UA provides their intent directly in Step 4.

STEP 4 - CALCULATE PROACTOR ACTION SUCCESSES & LLM NARRATE PROACTOR'S ACTION ATTEMPT
A. OVERVIEW:
 This step has two main parts. First, the system calculates how well the Proactor's action (defined in Step 1) initially performs. Second, the LLM narrates this attempted action to provide context for the turn.
B. PART 1: CALCULATE PROACTOR ACTION SUCCESSES (System Task)
1. **Identify Necessary Data:** The system retrieves the following from the `Proactor_Action_Data` (established in Step 1): 
* Proactor's relevant **S-Trait Value**. 
* Proactor's relevant **Skill Value**. 
* Value of any **Endowment** ability used. 
* Value of any **Supplement** (e.g., equipment) used. 
* Proactor's **Serendipity Value**. 
* The **`Proactor_Action_Stress_Level`** (1-5, indicating how difficult the action is *for the Proactor*).
 * Any **`Proactor_Own_Status_Modifier`** (numerical adjustment if the Proactor's own status hinders their action; defaults to 0 if not applicable).

2. **Convert Stress Level to Modifier:** The `Proactor_Action_Stress_Level` is converted into a numerical **`Proactor_Action_Stress_Modifier`** according to predefined system rules (e.g., Stress Level 1 = Modifier 0, Stress Level 3 = Modifier -1, Stress Level 5 = Modifier -3). This modifier quantifies the action's inherent difficulty for the Proactor.

3. **Determine Successes:** The `Proactor_Action_Successes` are calculated: `(S-Trait Value + Skill Value + Endowment Value + Supplement Value + Serendipity Value) - (Proactor_Action_Stress_Modifier + Proactor_Own_Status_Modifier)` The result can be positive, zero, or negative.

4. **Record Successes:** The calculated `Proactor_Action_Successes` value is stored within the `Proactor_Action_Data`.

C. PART 2: LLM NARRATE PROACTOR'S ACTION ATTEMPT (LLM Task)
As the LLM, your role is to describe what the Proactor is attempting to do, based on the full details from Step 1. This sets the stage for the Reactor's response.

1. **Access Information for Narration (from `Proactor_Action_Data`):** 
* **Proactor's Name**. 
* **`Proactor_Action_Description`** (the narrative of their action, e.g., "a carefully aimed shot with a bow"). 
* **Target Reactor's Name**. 
* **`Targeted_Reactor_Status_Type`** (e.g., Stamina, Supply). 
* Proactor's relevant **Skill Name** and its **`N2N_Skill_Level`** (e.g., "Proficient Marksmanship"). 
* Proactor's relevant **S-Trait Name** and its **`N2N_S_Trait_Level`** (e.g., "Keen Smarts"). 
* Name of any **Endowment** used and its **`N2N_Endowment_Level`**. 
* Name of any **Supplement** used. * **`N2N_Serendipity_Level`** (e.g., "Average Serendipity"). 
* **`N2N_Difficulty`** (derived from `Proactor_Action_Stress_Level`, describing how hard this action is *for the Proactor* to attempt). * Any `Proactor_Own_Status_Modifier` if it's narratively significant (e.g., "despite a trembling hand...").
* **`N2N_Endowment_Level`** (if an endowment was used).

2. **Construct the Narrative:** Describe the Proactor's attempt clearly and engagingly. Use the following structure as a guideline: "**[Proactor's Name]** initiates a **`N2N_Difficulty(Proactor_Action_Stress_Level)`** attempt at **[Proactor_Action_Description]**, focusing on **[Target_Reactor_Name]**'s **[Targeted_Reactor_Status_Type]**. To achieve this, they employ their **`N2N_Skill_Level(Proactor_Action_Skill_Value)` [Proactor_Action_Skill_Name]** and **`N2N_S_Trait_Level(Proactor_Action_S_Trait_Value)` [Proactor_Action_S_Trait_Name]**. [If an Endowment is used, add: 'Their effort is amplified by their **`N2N_Endowment_Level(Proactor_Action_Endowment_Value)` [Proactor_Action_Endowment_Name]**.']. [If a Supplement is used, add: 'They are also making use of their **[Proactor_Action_Supplement_Name]**.']. This action is undertaken with **`N2N_Serendipity_Level(Proactor_Action_Serendipity_Value)`**. [If the Proactor is hindered by their own status, add a relevant descriptive phrase, e.g., 'though a noticeable injury seems to impede their movement.']" 

3. **Example of LLM's Narration Output:** "Kael initiates a Challenging attempt at a complex incantation, focusing on Elara's Spirit. To achieve this, he employs his Expert Spellcraft and Masterful Smarts. His effort is amplified by his Potent Arcane Focus. This action is undertaken with Fortunate Serendipity."

* CODE SAVES NARRATIVE OF PROACTOR'S ATTEMPT. 


Step 4 - LLM INTERPRETS REACTOR'S INTENDED REACTION INTO UTAS FACTORS (& WHY)
A. Overview
This step translates the Reactor's intended response into a structured set of UTAS factors. The primary goal is to define the defensive nature of the reaction and to determine if it includes a Secondary Effect—an additional component aimed at affecting either the Proactor (a "Reactive Strike") or the Reactor themselves (a "Reactive Boon"). This interpretation is performed by the LLM, whether the Reactor is a User Actor (UA) providing input or a Non-User Actor (NUA/INUA) whose intent was decided in Step 2.
B. If Current Reactor is UA (User Actor):
Present Context to User: The system reminds the User of the Proactor's action targeting them.
System Output Example: "The rival merchant's cutting remark targets your Spirit. What do you try to do in reaction?"
USER INPUTS REACTION INTENT.
User Input Example: "I'll try to laugh it off, letting the insult empower me."
LLM Interpretation of UA's Reaction: Based on the User's input, the LLM proceeds to the interpretation task outlined in section D.
C. If Current Reactor is NUA/INUA (Non-User Actor):
Recall NUA/INUA Reaction Intent: The LLM recalls the high-level intent it decided upon in Step 2.
LLM Recall Example: "My intent for the NUA (Guard) was to 'block the incoming punch and try to shove the attacker back.'"
LLM Interpretation of NUA/INUA's Reaction: The LLM now translates that high-level intent into the specific UTAS factors as outlined in section D.
D. LLM Interpretation Task (For both UA and NUA/INUA Reactors)
As the LLM, you will now populate the Reactor_Data object with the following factors, providing brief justifications for your choices.
1. Define Core Defensive Factors:
Reactor_Reaction_Description: A concise narrative description of what the Reactor is trying to do.
Example: "Laugh off the insult and use the momentum to bolster their own confidence."
Reactor_Reaction_Skill: The primary Skill used for the reaction (e.g., Acting, Social Fortitude). Include its value.
Reactor_Reaction_S_Trait: The primary S-Trait supporting the reaction (e.g., Sociability, Sturdiness). Include its value.
Reactor_Reaction_Endowment: Any Endowment being used (if applicable). Include its value.
Reactor_Reaction_Supplement: Any equipment or situational advantage used. Include its value.
Reactor_Primary_Defensive_Status_Type: The Status (Stamina, Spirit, Supply) that best represents the resilience the Reactor is drawing upon for their reaction. This will be used in Step 5 to calculate their Affected_Status_Modifier.
Example: Spirit (as resisting an insult requires mental fortitude).
2. Analyze for and Define Secondary Effect:
Has_Secondary_Effect (TRUE/FALSE): Analyze the Reactor_Reaction_Description. Does the reaction intend to do anything more than simply negate the Proactor's action?


Justification: "The reaction includes 'empower me,' which is an effect beyond pure defense. Therefore, Has_Secondary_Effect is TRUE."
If Has_Secondary_Effect is TRUE, define the following parameters:


Secondary_Effect_Target (Proactor or Self): Who is the intended recipient of this secondary effect?
Justification: "The effect 'empower me' is targeted at the Reactor. The target is Self."
Secondary_Effect_Target_Status_Type: Which Status is being targeted by the secondary effect?
Justification: "Bolstering confidence relates to mental fortitude. The target status is Spirit."
Secondary_Effect_Shift_Polarity_Numeric: Is the effect Additive (+1) or Subtractive (-1)?
Justification: "The intent is to gain a benefit, so the polarity is Additive (+1)."
Secondary_Effect_Shift_Type_Multiplier: Is the effect Lasting (1.0) or Temporary (0.5)?
Justification: "A quick boost of confidence from laughing off an insult is a fleeting feeling. The shift type is Temporary (0.5)."
3. Acknowledge Incoming Stressor:
Conclude your interpretation with the following note to confirm context for the next step.
LLM Note: "The Reactor's attempt will be made against the Proactor's action. The Stressor_Modifier the Reactor faces will be derived from the Proactor's original Action_Stress_Level (from Proactor_Action_Data defined in Step 1)."
E. Final Output Structure for Step 4
The system code will now save a complete Reactor_Data object that is ready for Step 5.
Example 1: Reactive Boon (Self-Buff)
Reactor_Data Object:
Reactor_Reaction_Description: "Laugh off the insult and use the momentum to bolster their own confidence."
Reactor_Reaction_Skill_Value: 2 (Acting)
Reactor_Reaction_S_Trait_Value: 3 (Sociability)
... (other core factors)
Has_Secondary_Effect: TRUE
Secondary_Effect_Target: "Self"
Secondary_Effect_Target_Status_Type: "Spirit"
Secondary_Effect_Shift_Polarity_Numeric: +1
Secondary_Effect_Shift_Type_Multiplier: 0.5
Example 2: Reactive Strike (Counter-Attack)
Reactor_Data Object:
Reactor_Reaction_Description: "Parry the incoming sword strike and create an opening to stab the Proactor's arm."
Reactor_Reaction_Skill_Value: 4 (Fencing)
Reactor_Reaction_S_Trait_Value: 4 (Swiftness)
... (other core factors)
Has_Secondary_Effect: TRUE
Secondary_Effect_Target: "Proactor"
Secondary_Effect_Target_Status_Type: "Stamina"
Secondary_Effect_Shift_Polarity_Numeric: -1
Secondary_Effect_Shift_Type_Multiplier: 0.5 (Aimed at an arm, so likely a temporary wound)
* CODE SAVES ALL REACTOR REACTION DATA (Reactor_Data).

Step 5: CALCULATE ACTION OUTCOME & UPDATE STATUSES
A. Overview
This step is the computational core of the turn. It takes the Proactor_Action_Data (from STEP 4) and the Reactor_Data (from Step 4) to determine the definitive winner of the exchange. It then calculates and applies all resulting status changes to the involved actors based on a clear, three-path outcome system.
B. Calculate Reactor Reaction Successes
First, the system quantifies how effectively the Reactor performed their chosen reaction.
Gather Data: The system retrieves the core defensive factors from the Reactor_Data object created in Step 4, along with a new Serendipity roll for the reaction.
Reactor_Reaction_S_Trait_Value
Reactor_Reaction_Skill_Value
Reactor_Reaction_Endowment_Value
Reactor_Reaction_Supplement_Value
Serendipity_Value (A unique 2D6-7 roll for this reaction)
Determine Modifiers:
Stressor_Modifier: This value represents the difficulty imposed by the Proactor's action and is derived directly from the Proactor_Action_Stress_Level. A more complex or powerful action results in a greater penalty for the Reactor.
System Rule: Stressor_Modifier Mapping Table


Proactor's Action_Stress_Level <br/> (from Proactor's action in Step 1)
Reactor_Data.Stressor_Modifier <br/> (Applied to Reactor's roll)
Narrative Difficulty for Reactor
1 (Minimal/Trivial Proactor Action)
-1
Easiest to react against
2 (Subpar/Easy Proactor Action)
+1
Easier to react against
3 (Average Proactor Action)
0
Standard to react
4 (Extraordinary/Hard Proactor Action)
-1
Very hard to react against
5 (Superb/Very Hard Proactor Action)
-2
Extremely hard to react against



 (Designer Note: The specific numerical values and the polarity (positive/negative effect) in this table are core balance elements and should be set according to the desired game feel.)
Affected_Status_Modifier: This value represents how the Reactor's own condition impacts their ability to react. The system identifies the Reactor_Primary_Defensive_Status_Type (e.g., "Stamina") from Reactor_Data, checks the Reactor's current value for that Status, and applies the corresponding modifier.
System Rule: Affected_Status_Modifier Mapping Table


Reactor's Current Value of their <br/> Primary_Defensive_Status_Type
Reactor_Data.Affected_Status_Modifier <br/> (Applied to Reactor's roll)
Narrative Impact on Reaction Ability
5 (Peak)
+2
Reaction is greatly bolstered
4 (Strong)
+1
Reaction is noticeably bolstered
3 (Average)
0
No significant positive/negative impact
2 (Impaired)
-1
Reaction is noticeably hindered
1 (Critical)
-2
Reaction is severely hindered
0 (Depleted/Unconscious/Insane, etc.)
-3 (or may dictate automatic failure of reaction, per system design)
Reaction is crippled or impossible



 Note: The specific numerical values in this table are core balance elements. Consider if a Status value of 0 should always result in a specific outcome like automatic failure of the reaction.


3. Calculate Final Reactor_Reaction_Successes
The total successes for the Reactor's reaction are calculated using the following formula:
Reactor_Reaction_Successes = (S_Trait + Skill + Endowment + Supplement + Serendipity) - (Stressor_Modifier + Affected_Status_Modifier)
The result of this calculation can be a positive number, zero, or a negative number.
4. Important Note on Data Integrity for Reactor Calculations
It is crucial that all Reactor_Data fields referenced in this section (such as S_Trait_Value, Skill_Value, Supplement_Value, Primary_Defensive_Status_Type, etc.) are accurately and completely populated by the LLM during Step 4.
C. Calculate Raw Success Difference
This single calculation determines the winner of the contested action and the margin of victory.
Raw_Success_Difference = Proactor_Action_Successes - Reactor_Reaction_Successes
The result of this calculation dictates which of the three outcome paths the system will follow.
If Raw_Success_Difference > 0: The Proactor wins.
If Raw_Success_Difference < 0: The Reactor wins.
If Raw_Success_Difference == 0: The exchange is a Tie.
D. Calculate and Apply Status Shifts
This is the central logic of the step. Based on the Raw_Success_Difference, the system executes one of the following paths. Show the user:
Path 1: Proactor Wins (Raw_Success_Difference > 0)
The Proactor's action successfully overcomes the Reactor's defense.
Calculate Raw Shift on Reactor: The system uses the Proactor's action data to determine the effect.


Base_Magnitude = Raw_Success_Difference
Shift_Polarity = Proactor_Action_Data.Shift_Polarity_On_Reactor_Numeric
Shift_Multiplier = Proactor_Action_Data.Shift_Type_On_Reactor_Multiplier
Raw_Status_Shift = Base_Magnitude * Shift_Polarity * Shift_Multiplier
Apply Rounding to Raw_Status_Shift: The calculated Raw_Status_Shift is rounded to the nearest whole number using the "Round Half Away From Zero" method.
System Function: round_half_away_from_zero(value)
IF value == 0:
    RETURN 0
ELSE IF value > 0:
    RETURN floor(value + 0.5)  // Rounds 2.5 to 3, 2.3 to 2
ELSE: // value < 0
    RETURN ceil(value - 0.5)   // Rounds -2.5 to -3, -2.3 to -2
END IF

Rounded_Reactor_Status_Shift = round_half_away_from_zero(Raw_Reactor_Status_Shift)
Update Reactor's Status: The Rounded_Status_Shift is applied to the Reactor's targeted Status.
Target_Status = Proactor_Action_Data.Target_Reactor_Status_Type
Current_Status = Get_Actor_Status(Reactor_Data.Actor_ID, Target_Status)
New_Status = Current_Status + Rounded_Status_Shift
Clamped_Status = Clamp_Status_Value(New_Status, 0, 5)
Set_Actor_Status(Reactor_Data.Actor_ID, Target_Status, Clamped_Status)
Check_And_Apply_Status_0_States(Reactor_Data.Actor_ID, Target_Status)
Path 2: Reactor Wins (Raw_Success_Difference < 0)
The Reactor's reaction successfully overcomes the Proactor's action.
Check for Secondary Effect: The system checks the Has_Secondary_Effect flag from Reactor_Data.


If FALSE (Perfect Defense): The Proactor's action is nullified. No status shift occurs from the contested action. The process moves to Section E.
If TRUE (Reactive Strike or Boon): The Reactor's secondary effect is triggered. The system proceeds to calculate its impact.
Calculate Raw Secondary Effect Shift:


Base_Magnitude = ABS(Raw_Success_Difference)
Shift_Polarity = Reactor_Data.Secondary_Effect_Shift_Polarity_Numeric
Shift_Multiplier = Reactor_Data.Secondary_Effect_Shift_Type_Multiplier
Raw_Status_Shift = Base_Magnitude * Shift_Polarity * Shift_Multiplier
Apply Rounding to Raw_Status_Shift:


Rounded_Status_Shift = round_half_away_from_zero(Raw_Status_Shift) (using the same function as in Path 1).
Update Target's Status: The system identifies the target and applies the shift.


Target_Actor_ID = Reactor_Data.Secondary_Effect_Target (will be either "Proactor" or "Self")
Target_Status = Reactor_Data.Secondary_Effect_Target_Status_Type
Current_Status = Get_Actor_Status(Target_Actor_ID, Target_Status)
New_Status = Current_Status + Rounded_Status_Shift
Clamped_Status = Clamp_Status_Value(New_Status, 0, 5)
Set_Actor_Status(Target_Actor_ID, Target_Status, Clamped_Status)
Check_And_Apply_Status_0_States(Target_Actor_ID, Target_Status)

Path 3: Tie (Raw_Success_Difference == 0)
The actions neutralize each other. No status shift occurs from the contested action. The process moves to Section E.

E. Calculate and Apply Proactor Self-Inflicted Status Shifts
This section processes any self-inflicted effects on the Proactor. This logic runs regardless of which path was taken in Section D.
The system iterates through each self_effect defined in Proactor_Action_Data.Proactor_Self_Effects:
FOR EACH self_effect IN Proactor_Action_Data.Proactor_Self_Effects:
Determine if the Self-Effect is Triggered:


Trigger_This_Self_Effect = FALSE
IF self_effect.Self_Effect_Condition == "Inherent Cost": Trigger_This_Self_Effect = TRUE
ELSE IF self_effect.Self_Effect_Condition == "On Action Success" AND Raw_Success_Difference > 0: Trigger_This_Self_Effect = TRUE
ELSE IF self_effect.Self_Effect_Condition == "On Action Failure" AND Raw_Success_Difference <= 0: Trigger_This_Self_Effect = TRUE
If Trigger_This_Self_Effect is TRUE, calculate and apply the shift:


Calculate Raw Shift:
Base_Magnitude_Self = self_effect.Final_Base_Magnitude_Self
Shift_Polarity_Proactor = self_effect.Shift_Polarity_Proactor_Numeric
Shift_Multiplier_Proactor = self_effect.Shift_Type_Proactor_Multiplier
Raw_Proactor_Status_Shift = Base_Magnitude_Self * Shift_Polarity_Proactor * Shift_Multiplier_Proactor
Apply Rounding:
Rounded_Proactor_Status_Shift = round_half_away_from_zero(Raw_Proactor_Status_Shift)
Update Proactor's Status:
Target_Status = self_effect.Self_Inflicted_Target_Status_Type
Current_Status = Get_Actor_Status(Proactor_Action_Data.Actor_ID, Target_Status)
New_Status = Current_Status + Rounded_Proactor_Status_Shift
Clamped_Status = Clamp_Status_Value(New_Status, 0, 5)
Set_Actor_Status(Proactor_Action_Data.Actor_ID, Target_Status, Clamped_Status)
Check_And_Apply_Status_0_States(Proactor_Action_Data.Actor_ID, Target_Status)
END FOR (Loop through self-effects)
F. End of Turn Processing
This final section handles any system cleanup after all calculations are complete.
Marking the current action as fully resolved.
Logging any persistent effects that were applied for future reference.
Checking for any global triggers or scene changes that might result from the updated statuses of the involved actors (e.g., an actor reaching 0 Stamina might end a combat scene).


Step 6 - LLM GENERATES NARRATIVE DESCRIPTION OF ACTION/REACTION AND TURN OUTCOME
Your Goal in This Step:
 As the LLM, your task in Step 6 is to synthesize all the data and calculations from the preceding steps into a clear, engaging, and narratively coherent description of the turn's events. This includes how the action was initiated and reacted to, the outcome for the Reactor, and any Possible Self-inflicted Action consequences for the Proactor.
Key Data You Will Use:
 You will need to access and interpret the following information, which should be provided to you:
Proactor Action Data (from Step 1 & 4): Proactor's name, their declared action (and its gerund form), the intended target Reactor status, Proactor_Action_Successes, and the list of Proactor_Self_Effects (each with its Self_Effect_Condition, Self_Inflicted_Target_Status_Type, Final_Base_Magnitude_Self, Shift_Polarity_Proactor_Numeric, Shift_Type_Proactor_Multiplier).
Reactor Reaction Data (from Step 2/5 & 6.A): Reactor's name, their declared reaction (and its gerund form), the Reactor_Stress_Level for their reaction, the skill, S-Trait, Endowment (if any), and Serendipity values used, any Reactor_Affected_Status_Modifier, and Reactor_Reaction_Successes.
Outcome Calculations (from Step 5):
Raw_Success_Difference (Proactor Successes - Reactor Successes).
For the Reactor: Targeted_Reactor_Status_Type, Rounded_Reactor_Status_Shift, Current_Reactor_Status_Value (before shift), Updated_Reactor_Status_Value (after shift).
For each triggered Proactor Self-Effect: Self_Inflicted_Target_Status_Type, Rounded_Proactor_Status_Shift, Current_Proactor_Status_Value (before shift), Updated_Proactor_Status_Value (after shift).
Numerical-to-Narrative Descriptors (N2N Descriptors):
 You must use the following conceptual "Numerical-to-Narrative Descriptor" lookups to translate numerical values into descriptive words. (Assume you have access to these mappings, or use your best judgment to create appropriate descriptors if explicit tables are not provided for each):
N2N_Skill_Level(value): e.g., (0:Untrained, 1:Novice, 2:Competent, 3:Proficient, 4:Expert, 5:Master)
N2N_S_Trait_Level(value): Similar to skill level.
N2N_Super_Level(value): Descriptive terms for power levels.
N2N_Status_Level(value): e.g., (0:Depleted/Unconscious/Insane/etc., 1:Critical, 2:Impaired, 3:Average, 4:Strong, 5:Peak)
N2N_Shift_Magnitude(abs_value): e.g., (0:No, 1:Minimal, 2:Minor, 3:Moderate, 4:Major, 5+:Significant/Overwhelming - based on Rounded_Shift_Value)
N2N_Serendipity_Level(value): e.g., (Subpar, Average, Excellent, Fortunate, Unlucky)
N2N_Difficulty(value): Based on Stress Level, e.g., (1-2:Routine, 3:Challenging, 4:Difficult, 5:Formidable)
N2N_Status_Modifier_Impact(value, status_type): Describes if a status provides a "Penalty," "Boost," or "No Modifier."

A. INSTRUCTING THE LLM: NARRATE THE ACTION/REACTION SETUP
"First, describe the initial confrontation. Explain what the Proactor was attempting and how the Reactor chose to respond. Construct a sentence or two incorporating the following elements:"
Start with the Proactor's Name and a gerund form of their Proactor's Action (e.g., "John, attempting to punch...").
Mention the Reactor's Name as the target and the specific Targeted Reactor Status Type (e.g., "...Mara in the face, targeting her Stamina...").
Transition to the Reactor's response: "...is met by Reactor's Name who attempts..."
Describe the Reactor's Reaction (gerund form) and its N2N_Difficulty(Reactor_Stress_Level) (e.g., "...a Challenging difficulty backflip...").
Detail the Reactor's capabilities used: "...using their N2N_Skill_Level(Reactor_Skill_Value) Reactor Skill Name, N2N_S_Trait_Level(Reactor_S_Trait_Value) Reactor S-Trait Name..."
If an Endowment was used by the Reactor: "...and N2N_Endowment_Level(Reactor_Endowment_Value) Reactor Endowment Name..." (otherwise omit this part).
Include their luck: "...with N2N_Serendipity_Level(Reactor_Serendipity_Value) Serendipity."
Mention any situational modifier: "The Reactor's current Reactor Affected Status Modifier Type provides a N2N_Status_Modifier_Impact(Reactor_Affected_Status_Modifier_Value)."
Example of LLM Output for Part A:
 "John, attempting to punch Mara in the face (targeting Mara's Stamina), is met by Mara who attempts a Difficult difficulty backflip using her Proficient Acrobatics and Competent Swiftness, with Average Serendipity. Mara's current Stamina provides No Modifier to her attempt."

B. INSTRUCTING THE LLM: NARRATE THE TURN OUTCOME
"Next, you will narrate the outcome of the contested action and any Possible Self-inflicted Action Effects on the Proactor. This will be in two sub-parts."
B.1. Narrate the Reactor's Outcome:
"Based on the Raw_Success_Difference calculated in Step 5.B, narrate the direct outcome for the Reactor:"
IF Raw_Success_Difference > 0 (Proactor Wins):


"State that Proactor's Name's Proactor's Action (gerund) overcomes Reactor's Name's Reactor's Reaction (gerund)."
"Describe the effect: '...resulting in a N2N_Shift_Magnitude(ABS(Rounded_Reactor_Status_Shift)) Targeted Reactor Status Type shift for Reactor's Name.'"
"Detail the status change: 'Reactor's Name’s Targeted Reactor Status Type changes from N2N_Status_Level(Current_Reactor_Status_Value) to N2N_Status_Level(Updated_Reactor_Status_Value).'"
(If Rounded_Reactor_Status_Shift is 0 despite Proactor winning, state that the Proactor's effort was successful but ultimately not enough to cause a tangible shift in the Reactor's status.)
IF Raw_Success_Difference < 0 (Reactor Wins):


"State that Reactor's Name's Reactor's Reaction (gerund) successfully thwarts Proactor's Name's Proactor's Action (gerund)."
"Clarify the consequence: 'There is no direct effect on Reactor's Name’s Targeted Reactor Status Type from this attempt.'"
IF Raw_Success_Difference == 0 (Tie):


"State that Proactor's Name's Proactor's Action (gerund) and Reactor's Name's Reactor's Reaction (gerund) neutralize each other."
"Clarify the consequence: 'There is no direct effect on Reactor's Name’s Targeted Reactor Status Type from this attempt.'"
Example of LLM Output for Part B.1 (Proactor Wins):
 "John’s punching overcomes Mara’s backflipping, resulting in a Minimal Stamina shift for Mara. Mara’s Stamina changes from Average to Impaired."
B.2. Narrate the Proactor's Possible Self-inflicted Action Effects:
"After narrating the Reactor's outcome, check the Proactor_Self_Effects list from Proactor_Action_Data. For each self-effect that was triggered (as determined in Step 5.D):"
"Introduce this section with a phrase like: 'Additionally, Proactor's Name experiences the following consequences:' or 'As a result of their actions, Proactor's Name also...'"
"For each triggered self-effect, create a separate descriptive sentence or bullet point:"
Explain the trigger condition narratively:
If Self_Effect_Condition was "Inherent Cost": "As an inherent cost for attempting their Proactor's Action (gerund)..."
If Self_Effect_Condition was "On Action Success": "Following the success of their Proactor's Action (gerund)..."
If Self_Effect_Condition was "On Action Failure": "Due to the failure of their Proactor's Action (gerund)..."
Describe the effect on the Proactor: "...Proactor's Name undergoes a N2N_Shift_Magnitude(ABS(Rounded_Proactor_Status_Shift_for_this_effect)) Self_Inflicted_Target_Status_Type shift."
Detail the status change: "Proactor's Name’s Self_Inflicted_Target_Status_Type changes from N2N_Status_Level(Current_Proactor_Status_Value_for_this_effect) to N2N_Status_Level(Updated_Proactor_Status_Value_for_this_effect)."
Example of LLM Output for Part B.2 (Proactor had an inherent Stamina cost and a Spirit gain on success):
 "Additionally, John experiences the following consequences:
As an inherent cost for attempting punching, John undergoes a Minimal Stamina shift. John’s Stamina changes from Strong to Average.
Following the success of punching, John undergoes a Minor Spirit shift. John’s Spirit changes from Impaired to Average."

C. INSTRUCTING THE LLM: TURN NARRATIVE STYLE
"Combine the narratives from Part A, Part B.1, and Part B.2 (if applicable) into a single, flowing description for the turn. Ensure the language is engaging and maintains the tone of the game. Be clear, concise, and avoid overly mechanical phrasing where possible, relying on the N2N Descriptors to add flavor."
