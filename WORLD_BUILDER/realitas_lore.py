"""
Realitas Lore - All worldbuilding content for Realitas Neo

EASY EDITING GUIDE:
1. Find the section you want to edit (SETTING, LOCATIONS, OCCUPATIONS, etc.)
2. Edit the content in that section
3. Run: python realitas_lore.py
4. Done!

This file contains ONLY lore content. The RAG system is in worldbuilding_rag.py
"""

from pathlib import Path
from typing import List, Dict, Any
import os
import sys

# Add parent directory to path for standalone execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory, WorldbuildingRAGSystem


def _resolve_storage_path(storage_dir: str = "") -> Path:
    sd = (storage_dir or "").strip()
    if sd:
        return Path(sd)

    env = os.getenv("REALITAS_RAG_STORAGE_DIR", "").strip()
    if env:
        return Path(env)

    return Path("./simulation_data/worldbuilding_rag")


def _build_explicit_goal_library(*, actor_type: str, count: int) -> str:
    actor_type_s = (actor_type or "").strip().lower()
    n = int(count)
    if n <= 0:
        return ""

    if actor_type_s == "ua":
        verbs = [
            "Secure",
            "Protect",
            "Recover",
            "Expose",
            "Destroy",
            "Prevent",
            "Rescue",
            "Infiltrate",
            "Track",
            "Prove",
        ]
        focuses = [
            "a safehouse",
            "the cell",
            "a witness",
            "a relic",
            "a cult",
            "a vampire lord",
            "a conspiracy",
            "a kidnapped ally",
            "a compromised route",
            "a traitor",
        ]
        locales = [
            "inside a Signal Gap safehouse",
            "along a Yield Zone transit corridor",
            "inside a Plasma Clinic extraction ward",
            "beneath a surveillance blackout sector",
            "in a data-slum processing hub",
            "at an Enclave biometric checkpoint",
            "in a flooded sub-basement server room",
            "near the geofenced perimeter",
            "under compliance grid monitoring",
            "in the dead hours of the compliance cycle",
        ]
        constraints = [
            "before the next inquisitorial purge",
            "without exposing the Vigil",
            "without losing your last trusted witness",
            "while the war of princes escalates",
            "before the Beast’s influence spreads",
            "despite scarce supplies",
            "without drawing a rival cell",
            "while hiding evidence from the herd",
            "under constant surveillance",
            "before winter starvation sets in",
        ]

        lines: List[str] = []
        i = 0
        while len(lines) < n:
            v = verbs[i % len(verbs)]
            f = focuses[(i // 1) % len(focuses)]
            l = locales[(i // 2) % len(locales)]
            c = constraints[(i // 3) % len(constraints)]
            lines.append(f"{v} {f} {l} {c}.")
            i += 1
        return "\n".join([f"- {ln}" for ln in lines[:n]])

    if actor_type_s == "nua":
        verbs = [
            "Keep",
            "Avoid",
            "Repay",
            "Protect",
            "Secure",
            "Hide",
            "Win",
            "Survive",
            "Find",
            "Maintain",
        ]
        focuses = [
            "the family fed",
            "the guard’s suspicion",
            "a crushing debt",
            "a sick sibling",
            "work for the season",
            "a dangerous secret",
            "favor with a patron",
            "the next raid",
            "a missing friend",
            "a failing shop",
        ]
        locales = [
            "near the river",
            "in the market",
            "at the city gate",
            "in the guild hall",
            "in the slums",
            "at the monastery",
            "on the trade road",
            "in a crowded tavern",
            "under watchful eyes",
            "in the dead of night",
        ]
        constraints = [
            "before the rent collector arrives",
            "while plague rumors spread",
            "without angering the local lord",
            "while avoiding hunters and heretics",
            "before the Beast’s influence spreads",
            "despite scarce supplies",
            "without drawing a rival cell",
            "while hiding evidence from the herd",
            "under constant surveillance",
            "before winter starvation sets in",
        ]

        lines: List[str] = []
        i = 0
        while len(lines) < n:
            v = verbs[i % len(verbs)]
            f = focuses[(i // 1) % len(focuses)]
            l = locales[(i // 2) % len(locales)]
            c = constraints[(i // 3) % len(constraints)]
            lines.append(f"{v} {f} {l} {c}.")
            i += 1
        return "\n".join([f"- {ln}" for ln in lines[:n]])

    verbs = [
        "Expand",
        "Secure",
        "Silence",
        "Corrupt",
        "Break",
        "Recover",
        "Consolidate",
        "Uncover",
        "Ensure",
        "Forge",
    ]
    focuses = [
        "your domain",
        "an ancient relic",
        "a dangerous witness",
        "a hunter cell",
        "a rival alliance",
        "lost vitae",
        "influence in court",
        "forbidden lore",
        "a rival’s final death",
        "a blood oath",
    ]
    locales = [
        "beneath the city",
        "within a midnight court",
        "inside an inquisitorial archive",
        "on a war-torn borderland",
        "in a sanctified chapel",
        "along the trade routes",
        "inside a hidden haven",
        "within a rival’s domain",
        "behind sealed doors",
        "before the next gathering",
    ]
    constraints = [
        "before the next hunt begins",
        "without breaking the Traditions",
        "while keeping ghouls loyal",
        "without exposing your true nature",
        "before a rival strikes first",
        "despite an omen of damnation",
        "while avoiding the sun’s threat",
        "without waking an elder",
        "while hunters close in",
        "before the war of princes shifts",
    ]

    lines: List[str] = []
    i = 0
    while len(lines) < n:
        v = verbs[i % len(verbs)]
        f = focuses[(i // 1) % len(focuses)]
        l = locales[(i // 2) % len(locales)]
        c = constraints[(i // 3) % len(constraints)]
        lines.append(f"{v} {f} {l} {c}.")
        i += 1
    return "\n".join([f"- {ln}" for ln in lines[:n]])


# ============================================================================
# SIMULATION CONFIGURATION
# ============================================================================

# Time period for the simulation - describes the era for worldbuilding
# The UA Creator will select a specific year within this period
# That year then becomes the canonical simulation year for everything else
TIME_PERIOD_START_YEAR = 2025
TIME_PERIOD_END_YEAR = 2025
TIME_PERIOD = f"Echodrome, {TIME_PERIOD_START_YEAR}-{TIME_PERIOD_END_YEAR}"

# ============================================================================
# SETTING
# ============================================================================

SETTING_TIME_PERIOD = f"""
TIME PERIOD: {TIME_PERIOD}

This simulation takes place within the 2026 era—a hyper-realistic reality of predatory logistics and cognitive friction. It is an age of unyielding strife where the Parasitic Elite (The Architects) wage a global struggle for "Yield"—a transactional war that treats the mortal workforce (The Dampened) as mere biological resources. Nations rise and fall under the shadow of Strategic Foreclosures, while the global population exists under the constant fear of financial liquidation, algorithmic erasure, and the tactical enforcers that stalk the "Extraction Wards."
Beneath the high-rise "Green Zones"—fortified not by lasers, but by "Order as a Service" geofencing and high-trust digital passes—the world is infested with "Systemic Anomalies." These include "The Augmented" (tactical enforcers juiced on Modafinil-psychosis), "The Ghosts" (automated decision-logic models of deceased CEOs running corporations via predictive data-exhaust), and "The Syndicates" (organized crime nodes like the Tren de Aragua) who offer predatory "Debt-Traps" to the desperate. Yet, the heart of this simulation is the "Glitch"—the desperate stand of human sovereignty. It endures, bolstered by powerful Elite Operators—highly educated, specialized assets optimized with academic expertise, field experience, and unyielding Empcog perception—who rise as bulwarks against the total optimization of the human consciousness.
The User Actor (UA) is an "Elite Operator," an exceptional human whose eyes have been ripped open to the "Physical Reality" behind the digital feed. Whether they are a "Social Operator" infiltrating a BRIC embassy with NLP Anchoring or a "Combat Operator" wielding Subsonic Smart-Carbines, they carry the "Analog Edge" against an endless algorithmic night. These Operators, drawn from disgraced intelligence officers, rogue neuroscientists, and Tier-1 specialists, form elite cells that wield Dazzle Shrouds, Logic Spikes, and Pharmacological Stacks to stalk and liquidate the system's enforcers, their missions echoing the desperate struggle for cognitive sovereignty.
Physical life is clinical, defined by "Compliance Fog" and "Asset Recovery." Communication relies on "Encrypted Mesh-Nets" and "Analog Dead-Drops," making "Null-Keys" and "Un-indexed Data" more precious than gold. The most advanced sciences are the "Stacks" of the superpowers—"Parabiosis" plasma grafts, "Closed-Loop Neuro-Modulation," and "Pheromonal Overload"—often mistaken for breakthroughs by a "Dampened World" that clings to "Wellness Kits" to stave off the "Pattern-Screech."
Travel is a "Perilous Extraction" where "Ambushes" by "Syndicate Vultures" or "ARC Drones" are a constant threat to one's health and digital identity. Ambushes along logistics routes and data-pipelines make wealth and information rare, hoarded by those with the wit to protect it from both the Algorithm and the blade.
Collectiveurally, it is an age defined by the endless cycle of Consumption and grim survival. The masses cling desperately to their "Feeds," constantly fearing the unknown "Noise" lurking outside their echo chambers—Augmented squads devouring the unwary, AI Ghosts faking their deaths, and Elite Operators slipping through the night like silent reapers.
Among the Operators, existence is maintained through rigid adherence to "Operational Security" and adherence to "Cognitive Anchors," psychological paths meant to stave off "Deepfake Dissociation." Survival and mastery are the only true currency in the Echodrome, bartered amid skirmishes with Landlord Auditors whose budgets and KPIs mirror the System's unyielding light against the Glitch.

The Illusion of Normalcy: The Naive Eye
Despite the predatory logistics of the superpowers, the world of 2026 remains—on the surface—unsettlingly ordinary. The Dampened (the general population) do not live in a state of constant panic; they live in a state of Optimized Routine. They still walk their dogs in municipal parks, wait in line for overpriced lattes, and commute to office jobs in glass-fronted skyscrapers. To their eyes, the world is simply "efficient."
They view the ARC Drones overhead as "Public Safety Infrastructure" and the Compliance Fog as a "Seasonal Allergy Mitigation" program. They are not being marched at gunpoint; they are being Nudged by algorithms that ensure their grocery stores are always stocked and their digital feeds are always entertaining. The horror of Echodrome is not the end of the world, but the fact that the world continues to turn "normally" while the biological and digital potential of the masses is harvested in the background, one "Wellness Check" at a time.

**Timeline Context: The Global Yield rages in 2026, clashing with the riviolationg tide of Operators emboldened by civic decay and systemic friction.**
- Early period (2024-2025): The "Invasion of Venezuela" begins; ARC forces seize the Orinoco Belt—Operators clash with "Augmented" contractors fleeing the chaos, while "AI Ghosts" stir in the corporate "Cloud."
- Middle period (2026): The "San Francisco Infiltration"; China’s BRIC vie for control of Silicon Valley—Operator "Cells" swell their ranks, using "Logic Spikes" to purge "Dampened" workers from war-torn tech hubs.
- The "Fortress Europe" Lockdown; Frontex Security & Stability rallies with "Stress-Reduction Therapy," "Neutralizing" dissidents and "Data-Ghosts" amid the flames of the "Buffer Zones."

NOTE: The specific simulation year is determined by the User Actor's creation and stored in their actor sheet. All other systems should reference the UA's year for temporal consistency.
"""

SETTING_TONE = """
Cold, clinical horror where the existential dread of the "Crash" (the Operator's inner voice forever thirsty for the next Modafinil/Empcog high) meets the relentless, obsessive pursuit of the "Glitch" (the Operator's unyielding search for truth in the data).
This struggle is framed by the reality of the 2026 World—a time of crushing debt where life is defined by the endless cycle of Harvest and Yield. The greatest terror is the innate struggle against "Pattern-Screech" which threatens to overwhelm the remnants of human consciousness and consciousness, coupled with the external threat of powerful Auditors—systemic enforcers who rise as the "Gods of the Grid" to purge the world of the unaccounted. Survival hinges on strict adherence to a "Cognitive Anchor" and the avoidance of ARC/BRIC surveillance, lest the Operators descend into utter "Dissociation" or liquidation.
Atmosphere:
- Environments: Defined by fortified Green Zones (bubbles of 100% uptime and geofenced security) and crumbling Data-Slums (zones of digital exclusion where people live in the exhaust heat of AI server farms), separated by perilous, un-monitored "Grey Zones" where Syndicate enforcers and ARC drones lie in wait.
- Technology: Advanced but predatory; knowledge is held in rare, jealously guarded "Offline Servers," occasionally supplemented by the secret arts of "Empcog Social Hacking" or the forbidden archives of "Null-Operator" cells.
- Social Interactions: Dictated by rigid "Civic Health Scores," allegiance to the "Landlord," and the constant threat of "Algorithmic Scrutiny."
- Secrecy: Mandated by "Operational Security," yet suspicion runs rampant due to paranoia and the pervasive nature of both corporate violence and the relentless "Systemic Audit."
- Mystery: Abounds, as the long history of the "Architects," the true nature of the "Algorithmic Accord," and the origins of the first "Empcogs" are contradictory and often revised by the victors.
- Core Dread: Lies in succumbing to the "Crash" and entering "Catatonia," or facing destruction by "Financial Foreclosure," "Identity Erasure," or the "Smart-Carbines" of the elite.
- The "Smooth" Surface: Environments are defined by the contrast between the Smoothness of everyday life (clean streets, functioning transit, polite AI customer service) and the Friction of the Extraction Wards.
- The Naive Perspective: Most NPCs are not "survivors"; they are Subscribers. They believe they live in a golden age of stability. They will ignore a tactical extraction happening across the street because their AR-lenses have automatically flagged it as "Routine Maintenance" or "Civic Optimization."
- Technology as Utility: Technology is not "high-tech/low-life"; it is Invisible and Ubiquitous. It is the smart-fridge that reports your calorie intake to your insurance provider and the "Civic-Link" watch that you wear because it gives you a 10% discount on public transit.
- The Peril of the Ordinary: Peril doesn't always look like a soldier with a gun; it looks like a "Service Interruption" or a "Trust Score Adjustment" that quietly locks you out of your own life while you're sitting at a park bench.

"""

SETTING_GEOGRAPHY = """
I. The Workforcetic Front: Caracas, Venezuela
The Vibe: "Vertical Liquidation." A city being physically mined for its lifeblood under the gaze of the Asset Recovery Command (ARC).

- The Vertical Hierarchy: Geography is defined by the "Elevation of Trust." The Architects and ARC Auditors rule from the fortified heights of Las Mercedes and the southeastern hills—"Green Zones" of 100% uptime, high-speed 6G, and "Compliance Fog" scrubbers that keep the air chemically polite. Below them, the sprawling "Data-Slums" of Petare and Catia serve as the primary "Resource Extraction Zones." Here, the ARC has seized the telecommunications backbone; the only way to access the grid is to "sell" biometric data or plasma at modular Onboarding Centers.
- The "Analog Wilds": Beyond the city’s geofenced perimeter lie the "War-Torn Borderlands"—hollowed-out industrial corridors and jungle passes. This is the geography of the Sovereign Insurgency, who guard these "Grey Zones" against the ARC. For an Elite Operator, this terrain offers the "Isolation" needed for Analog Safehouses, but it is infested with Tren de Aragua (TdA) enforcers who tax the "Unaccounted" population moving through the mud.
- Temporal Geography: The climate is dictated by the "Predictive Peak." During the day, the ARC’s Wasp Drones maintain total awareness, making "Daytime Raids" a standard logistical procedure. Operators are forced into the "Twilight Windows"—the signal gaps created during maintenance cycles—to move between "Blind Spots" before the next algorithmic sweep.
- Mobility & Friction: Movement is restricted by "Strategic Checkpoints." Traveling from the barrios to the city center requires a "Transactional Visa" and a high "Civic Health Score." Those with "Low Trust" are relegated to "Shared Data-Warrens" in the ruins of the old subway tunnels, which serve as the primary "Audit Grounds" for ARC squads looking to liquidate "Systemic Friction."

II. The Echo Front: San Francisco, USA
The Vibe: "Algorithmic Decay." A familiar icon being socially deleted and re-written by the Belt & Road Infrastructure Command (BRIC).

- The Vertical Hierarchy: Geography is defined by "Digital Inclusion." The Architects of Silicon Valley hide in the "Green Zones" of the Presidio and Pacific Heights, protected by "Order as a Service" geofencing. The downtown core (SoMa/Financial District) has been transformed into a "Data-Slum." These are zones of "Digital Exclusion" where the Dampened live in the exhaust heat of massive AI server farms that have taken over hollowed-out office towers. They work as manual "Data-Scrubbers," their lives optimized by the very algorithms they train.
- The "Civic Abandonment": The hollowed-out corridors of the Tenderloin and the Mission have become "Grey Zones." Because the city has stopped providing services, there is no "Civic Eye." This is the geography of the Echo-Walker cells, who use "Logic-Bombs" to jam the 6G signal, creating the silence needed to move stolen hardware or "Un-personed" workers away from the BRIC’s Audit.
- Temporal Geography: The climate is dictated by the "Algorithmic Accord." The "Harmony Pillars" (6G surveillance nodes) on every street corner track intent in real-time. Operators must exploit "Signal Gaps"—temporal windows where the BRIC AI is re-indexing the city’s social credit data. The night belongs to the "Ghosts" (predictive AI models) and the "POGO Syndicates" who view the naive population as livestock for identity-harvesting.
- Mobility & Friction: Movement is restricted by "Identity Foreclosure." Crosviolationg from a Data-Slum into a Green Zone without a "High-Trust Pass" triggers an immediate "Sentiment Correction" by Augmented security. Within the city, geography is segmented by "Family Offices" (neutral grounds for the elite) and "Scam Compounds," where the "Un-personed" are forced into debt-bondage to pay off their "Social Defaults."
"""

SETTING_SUPERNATURAL = """
This world is defined by The Harvest, manufactured echo chambers, and the relentless extraction of human potential. All of existence operates under the Algorithmic Accord—a global duopoly where the elite pit the population against itself to syphon off the world’s physical and psychological resources. Shadowing this manufactured friction are the Elite Operators: exceptional, high-priced assets who possess the Empcog edge, serving as the janitors and enforcers for the very superpowers that maintain the grid.

The "Systemic Anomalies" are diverse "Outliers" hiding within the "Dampened" population:
- The Architects (Architect): High-net-worth stakeholders divided into "Family Offices," battling "Deepfake Dissociation" and the "Audit." They use Parabiosis (plasma exchange) to maintain biological immortality while they orchestrate the global yield.
- The Augmented (Augmented): Tactical enforcers who assume "Flow States" via "The Stack" (Modafinil/Propranolol) to "liquidate" those who defile the "Green Zones" or disrupt the extraction pipeline.
- Social Engineers (Social Engineer): Manipulators of NLP who use "Anchoring Rituals" and "Un-indexed Data" to "gaslight" the masses into tribalistic rage, ensuring the echo chambers remain airtight.
- The Ghosts (Spirits): Predictive AI models of deceased CEOs trapped in the "Cloud," summoned by "Data-Miners" to maintain "Dead-Hand Governance" over corporations that outlive their founders.
- The Syndicates (Syndicates): Transnational crime nodes (like the TdA) seeking "Debt-Bondage" and "Foul Contracts," hunted by ARC Auditors and BRIC Enforcers when they interfere with the official harvest.
- The Un-personed (Anomalies): Dissidents deleted from the "Social Credit" system and "Jailbroken" assets who defy "Algorithmic Law," existing as glitches in a world that no longer recognizes their biometrics.

The "Glitch" is the human response to this "Systemic Mesh":

- Cells like the "Null-Operators" provide "Grey Zone" defense through "Analog Tradecraft" and "Street Wisdom," occasionally hiring themselves out to the highest bidder.
- Collectives like the "Echo-Walkers" use "Jailbroken Tech" to harvest "Clean Identities" from captured "Systemic Nodes," selling them to those desperate to escape their "Trust Score."
- Cognitive Sovereignty allows the "Un-linked" to perform "Logic Spikes" and "Prompt Injections" that temporarily crash the "Harmony Pillars" to create windows of un-monitored reality.

The central mysteries are Systemic and revolve around corporate blood-feuds, financial foreclosure, and the hidden agendas of both the Architects and the great Operator Cells. The unknown comes from the deep history of the "Algorithmic Accord," hidden data within the various and contradictory leaks of the "Null-Servers," and the struggle to maintain a sense of "Analog Reality" in a world of manufactured noise.
The pervasive horror is "Liquidation"—the loss of "Cognitive Sovereignty" or the "Human Consciousness." Whether through the "Debt-Trap," "Pattern-Screech," or the "Signature" of an "Augmented Squad," the simulation is a "Relentless Cycle" of predation where there is no escape, only the next contract.
This is a world of data and debt—where "The Stack" empowers Empcog Social Exploits and Workforcetic Audits, while the elite harvest the friction of the masses. There is no escape into fantasy, only a deeper descent into the inevitable conflict between the Noise of the System and the Signal of the Glitch.
"""


BEINGS_OVERVIEW = """
Inhabitants of the Echodrome (2026):

**The Dampened (The Workforce):**
- The overwhelming majority of the population.
- Social strata: data-scrubbers, gig-laborers, essential service providers, and middle-management.
- They live within the Illusion of Normalcy, fearing financial foreclosure and identity erasure while remaining "rage-baited" into oppoviolationg echo chambers.

**Elite Operators (The Frankensteins):**
- Exceptional, highly-educated assets (embodied by the User) who possess the Empcog edge.
- Stitched together by academic expertise and field experience, they are specialized in either Workforcetic Audits (combat) or Ghost-Talking (social).
- They are the "Janitors of the Elite": as combat-capable as the Augmented and as socially lethal as Social Engineers, but with the added clarity of Empcog perception.
- They are mercenaries of the grid: working for Architects, Syndicates, or independent operators, they move the pieces on the board that the algorithms cannot yet automate.

**The Architects (The Architect)**
- Ultra welathy parasitic predators bound to the Yield, biological longevity, and the Algorithmic Accord.
- They orchestrate the Harvest from fortified Green Zones, using Parabiosis (plasma exchange) to outlive the populations they exploit.
- They view the world as a series of assets to be liquidated or optimized.

**The Augmented (The Augmented)**
- Territorial apex enforcers juiced on "The Stack" (Modafinil/Propranolol) and fitted with AR-lenses that gamify violence.
- They provide the "Order as a Service" for the Architects, acting as remorseless, synchronized predators along logistics routes and in Extraction Wards.

**Social Engineers (The Social Engineer)**
- Rare and secretive manipulators of the Echo Chambers who treat the human mind as unsecured hardware.
- They use NLP, pheromonal overload, and "Anchoring Rituals" to maintain the tribalistic friction that generates the Yield.

**AI Models / Syndicates: (Ghosts)**
- The world is haunted by Dead-Hand Governance (AI models of deceased CEOs) and tempted by Debt-Traps (Shadow Syndicates like the TdA).
- They represent the "Noise" of the system—automated greed and predatory contracts that outlive their creators.

**Core Rule for Simulation:**
- Everyday life is ordinary and clinical; the Systemic Anomalies exist but are hidden behind the Illusion of Normalcy, dangerous, and navigated by the Elite Operators who serve as the high-priced pawns of the 2026 reality.
"""


FACTIONS_ORGANIZATIONS_OVERVIEW = """
Factions & Organizations of the Echodrome:

**The Landlord Duopoly (Architect Power Structures)**
- Asset Recovery Command (ARC - USA): The "Global Liquidator" focused on workforcetic extraction. They employ EmpCogs for high-fidelity profiling and Augmented squads for asset foreclosure.
- Belt & Road Infrastructure Command (BRIC - China): The "Grand Architect of Harmony" focused on cognitive infiltration. They utilize EmpCogs for social engineering and identity management.
- The Family Offices: Fortified Green Zones ruled by Architects; these are the primary employers of EmpCog cells for corporate espionage and "clean-up" operations.
- The Yield Exchange: Political theaters where sovereignty is treated as a service; trust scores, data-rights, and biological futures are the primary currency.

**EmpCog Cells (The Frankensteins)**
- Dedicated Cells: Small, specialized teams of exceptional assets (embodied by the User) who possess the Empcog edge.
- Transactional Allegiance: They are the "Janitors of the Elite," moving the pieces the algorithms cannot. They work alongside Augmented goons for the ARC, Social Engineers for the BRIC, or independently for Shadow Syndicates.
- Operational Specialization: Stitched together by expertise, they coordinate encrypted mesh-nets and high-fidelity audits for whoever can afford their "Stack" and pharmacological overhead.

**The Algorithmic Accord (The New Audit)**
- Predictive Governance: Algorithmic authority is pervasive; a drop in "Civic Health" or "Social Credit" can effectively un-person a citizen.
- Auditors: High-level political actors who monitor the Yield and purge "Systemic Noise," often hiring EmpCog cells to find the human errors the AI misses.

**Logistics Hubs & Data-Slums (Bureaucrats)**
- Optimization Hubs: Urban centers that control the flow of data, trade, and "Onboarding."
- Data-Slums: Zones of digital exclusion that shape local friction; they serve as the primary breeding grounds for Syndicate recruitment and the "Analog Wilds" where EmpCogs perform their most dangerous off-grid contracts..

**Syndicates / PMCs / Shadow Assets:**
- Shadow Syndicates: Transnational crime nodes (like the Tren de Aragua or POGO Syndicates) that manage the "informal" economy; they frequently employ EmpCogs to "Debt-Trap" high-value targets.
- Extraction Contractors: Armed groups and Augmented squads who shift loyalties for high-grade nootropics, debt-relief, or access to "The Stack."

**Core Rule for Simulation:**
- Factions are coherent, goal-driven actors competing for Yield, data dominance, drugs, currency, sex trade, and structural leverage, utilizing EmpCog cells as the elite, specialized tools of their trade.
"""


EXPANSION_SEEDS_OVERVIEW = """
Expansion Seeds (Future Hooks) for Echodrome:

- A high-speed logistics drone crashes in a "Dead Zone" slum; the EmpCog cell must retrieve its "Ghost-Drive" before a local Syndicate can jailbreak the CEO’s decision-logic. Potential Gain: A "Ghost-Key" (one-time Green Zone override) or a "Logic-Spike" IED.
- A secure Family Office server farm burns, and a fragment of an Architect’s "Biological Futures" data vanishes into the black market. Potential Gain: A "Vitality Infusion" (permanent resilience buff) or "Un-indexed Data" on elite stakeholders.
- A High-Level Auditor arrives with unfamiliar authority; their Truth-Leak audits suggest they are hunting a rogue EmpCog who stole a shipment of military-grade nootropics. Potential Gain: Access to "The Master Formula" (high-purity Stacks) or a "Trust-Pass" (high-level digital credentials).
- A minor Optimization Hub shifts hands overnight; rumors claim a "Social Infiltration" by a rival superpower, but every digital witness has been un-personed. Potential Gain: "Sentiment Analysis" lens software or a cache of "Clean Identities."
- A Data-Slum offers an "Analog Dead-Drop" in exchange for protection from a localized "Pattern-Screech" signal-bleed. Potential Gain: An "Analog Mesh-Node" (un-trackable Wi-Fi) or a "Pheromone Patch-Kit" (social manipulation bonus).
- A Null-Key changes owners repeatedly within a week; each bearer suffers a different systemic failure, but the key is rumored to unlock a superpower's "Compliance Fog" controls. Potential Gain: A "Deepfake Scrambler" (audio-manipulation immunity) or a "Subsonic Smart-Carbine."
- A superpower faction fractures into rival corporate splinters; the EmpCog cell must choose which "Family Office" to contract for or exploit the chaos to secure their own pharmacological independence. Potential Gain: A "Sledgehammer .50 Revolver" or a permanent "Debt-Relief" status.

Core Rule for Simulation:
- Expansion seeds must generate grounded Civic Horror arcs that reinforce major superpower friction, the peril of digital exclusion, and the specialized utility of the EmpCog (User). Every thread must offer a tangible addition to the User's repertoire—be it tech, drugs, or social leverage—to entice them into the next contract.
"""


# ============================================================================
# LOCATIONS
# ============================================================================

LOCATIONS_URBAN = """
Typical Urban Locations in the Echodrome:

**Extraction & Medical:**
- Onboarding Centers and Plasma Clinics: Clean, professional-looking storefronts in poor districts where the Dampened "sell" biometric data or plasma to pay off debts, often monitored by EmpCog cells looking for patterns of systemic extraction.
- Private Audit Suites and Security Rooms: Soundproofed offices used by corporate Auditors or Syndicate enforcers to interrogate "Low-Trust" individuals, using high-end sensors and "Truth-Leak" software to extract passwords or confessions.
- Longevity Clinics: Fortified medical suites in high-end districts where Architects undergo plasma exchange (Parabiosis) to stay young, or where rogue technicians attempt to model the "Decision-Logic" of high-value targets for AI backups.
- Offline Data-Vaults and Secure Archives: Secluded server rooms within corporate campuses where sensitive "Ghost-Logic" or un-indexed financial records are stored on physical drives to avoid the superpower's digital eye.

**Daily Life:**
- Low-Trust Tenements and Data-Slums: Ordinary-looking apartment blocks in "Dead Zones" where the Wi-Fi is jammed and the Dampened live in the exhaust heat of nearby server farms, often policed by local Syndicates rather than the state.
- Signal Gaps and Analog Safehouses: Basements or abandoned retail spaces with thick concrete walls that block 6G signals, used by dissident groups to communicate without being "indexed" by the state's Harmony Enforcement.
- Transit Plazas and Gig-Economy Hubs: Crowded public squares where the Dampened wait for work-pings on their phones, serving as the primary listening posts for Echo-Walkers capturing "Systemic Noise" and rumors.
- Fortified Penthouses and Green Zone Safehouses: High-security residences where Architects retreat for "Cold State" recovery, protected by geofencing that only allows "High-Trust" IDs to enter the elevator.

**Work & Commerce:**
- Logistics Hubs and Fulfillment Centers: Massive centers of economic power in cities like San Francisco or Caracas, attracting data-brokers and contractors seeking to fund their own pharmacological "Stacks."
- Corporate Green Zones: Gated buviolationess districts and campuses that represent the seat of territorial control, occupied by Stakeholders and Architects who manage the global "Yield" from behind glass walls.
- Data-Scrubbing Offices: Ordinary office floors where the Dampened spend 12 hours a day tagging content to train superpower AI, providing the digital paper trails that ARC Auditors use to find "Systemic Friction."
- Civic Tribunals and Yield Exchanges: Public-facing offices where "Social Defaults" are investigated and bank accounts are frozen via algorithm, serving as the bureaucratic face of the superpower's shadow war.

**Infrastructure:**
- Family Offices and Private Clubs: Exclusive, neutral meeting grounds where Architects gather to conduct transactional politics under the protection of private security, occasionally infiltrated by EmpCog mercenaries.
- Logistics Corridors and Grey Zone Roads: Routes used by automated freight trucks and traveling merchants, vulnerable to Syndicate vultures or signal-interdiction by Null-Operator cells.
- Encrypted Mesh-Nets: Low-power, short-range Wi-Fi networks used to share analog intelligence across un-monitored distances, bypasviolationg the superpower's "Harmony Pillars."
- Un-monitored Alleys and Backstreets: The ubiquitous environment of the city at night, providing the "Blind Spots" necessary for the operations of the Un-personed and the ambushes of the EmpCog Vigil.
"""

LOCATIONS_SUBURBAN = """
Typical Locations in the Echodrome:

**Architect Houviolationg (The High-Trust Enclaves)**
- Gated Enclaves and Private Estates: Fortified suburban communities where high-trust Stakeholders live in absolute opulence. These areas feature 100% uptime for all services, private "Compliance Fog" scrubbers for perfect air quality, and automated landscaping. Access is restricted by geofencing that only recognizes "High-Trust" digital IDs.
- Family Office Compounds: Lavish, multi-acre estates that serve as both a residence and a private headquarters. These locations are "Off-Grid" by choice, featuring independent power, private server racks for "Personality Backups," and Longevity Suites for parabiosis treatments.
- Luxury "Safe-Cities": Small, private municipalities owned by corporations where every commodity is premium and every interaction is optimized. These are the primary targets for Sovereign Insurgency cells looking to strike at the heart of the elite's comfort.

**Dampened Houviolationg (The Extraction Blocks):**
- Employee Houviolationg Blocks: Modular, cramped tenements reserved for the Dampened workforce. These are often located near industrial zones or server farms. Residents receive "Wellness Kits" as part of their rent, and their "Civic-Link" watches monitor their sleep and heart rate to ensure they are "mission-ready" for the next gig-shift.
- Digital Exclusion Zones: Ordinary-looking suburban neighborhoods where the city has stopped providing 6G, maintenance, or emergency services due to "Social Defaults." The Un-personed gather here for mutual defense, living in the "Blind Spots" of the state's biometric eye.
- Onboarding Tenements: High-density residential towers managed by the ARC or BRIC where residents are systematically monitored. These locations serve as the primary "Audit Grounds" for state enforcers looking to identify "Systemic Friction" or harvest biological yield.

**Gathering and Commerce:**
- Family Office Hubs: Designated suburban office parks where Architects meet to conduct corporate intrigues, though they must remain vigilant for the "Logic-Spike" targeting of rival EmpCog cells.
- Transit Centers and Commuter Hubs: Social hubs where the Dampened wait for transit and rumors spread, often serving as the primary Audit Grounds for state enforcers looking for "Low-Trust" signatures.
- Corporate Libraries and Data Centers: Centers where rare "Offline Data" and historical behavioral models are guarded, occasionally concealing fragments of dangerous "Ghost-Logic" sought by the Echo-Walkers.

**Yield Boundaries and Infrastructure:**
- Un-monitored Borderlands: Hollowed-out industrial corridors and jungle passes on the edge of the city, where travelers risk encountering Syndicate enforcers or rogue security squads far from state authority.
- Geofences and Harmony Pillars: 6G surveillance nodes that mark the limits of a Green Zone, serving as digital checkpoints to control the flow of the Dampened and detect the pheromonal overload of the Unaccounted.
- Industrial Waste Grounds: Necessary sites for dispoviolationg of "Biological Surplus," often used by rogue technicians for illegal studies and providing easy access to "High-Yield" plasma for the Architects' treatments.

"""

LOCATIONS_SPECIFIC = """
**Key Locations of Power:**
- The Black Market (Stolen Plasma): Clandestine clinics or hidden trading hubs along logistics routes used for the illicit exchange of "High-Yield" plasma, rare "Stacks," and jailbroken tech.
- The Archival Server: Secure data-vaults hidden beneath a city where Architects store their most sensitive records or "Personality Backups," protected by high-fidelity encryption.
- The Longevity Lab: A secluded, fortified medical workshop, often within a private estate, where Architects practice plasma exchange to mold biological potential or perfect their own "Stacks."
- The Workforcetic Front: Areas of open conflict (like the Caracas barrios or San Francisco's Tenderloin) where the Global Yield rages, serving as cover for Null-Operators and Workforcetic Audit cells.
- The Extraction Ward: Large industrial sites or military garrisons where the Dampened workforce is housed and systematically controlled to supply manpower for the ARC or BRIC.
- The High-Rise Green Zone: The central and highly defended residence of the most powerful Stakeholder in the region, symbolizing absolute authority and the pinnacle of the Echodrome hierarchy.
"""


# ============================================================================
# OCCUPATIONS
# ============================================================================

OCCUPATIONS_UA = """
Protagonist EmpCog (UA) Roles in the Echodrome:

**The Investigative Auditors (Information & Data-Miners)**
- The "Jailbroken" EmpCog: Former high-level corporate analysts or Family Office insiders who have "un-linked" from the grid to sell their expertise. They use their insider knowledge to decode the "Inside Track" on superpower vulnerabilities. They provide the "Intellectual Edge" necessary to identify a Ghost or a Family Office for whoever holds their current contract.
- The Profiler EmpCog: Canny "Field Auditors" or "Private Investigators" who monitor "Digital Paper Trails" and "Rumor Markets." They use "Truth-Leak" and "Sentiment Analysis" to track Systemic Anomalies through "Signal-Jammed Alleys." They are masters of the "High-Fidelity Profiling" tactic, assembling data to find a target's Safehouse for Architects, Syndicates, or independent cells.
- The "Netzo" Media EmpCog: Clandestine data-messengers and "Signal-Breakers" for Network Zero. They use "Witnesses of Whispers" and "Encrypted Recorders" to capture "Systemic Noise." Their role is to "Expose" or "Leaking" data to the highest bidder, broadcasting truths or manufactured noise through coded "Mesh-Net" frequencies.

**The Workforcetic Auditors (Combat & Tactical Enforcers)**
- The Soldier EmpCog: Hardened "Tactical Contractors" or "Tier-1 Operators" who work alongside The Augmented or independently. They are experts in "Signature Reduction" and "Ballistics," utilizing "Tactics" like "Workforcetic Foreclosure" or "Biometric Suppression." They are the "Enforcers" of the cell, often wielding "Advanced Armory" such as the XM-26 Smart-Carbine.
- The Vengeful EmpCog: Driven by "Financial Liquidation" or "Identity Erasure," these are the "Lone Wolves" or "Slashers" of the grid. They specialize in "Overkill" and "Systemic Sabotage," taking contracts that allow them to vent their "Wrath" against specific corporate or criminal entities. They often have "Justice" as a Virtue and "Wrath" as a Vice.
- The Street-Level EmpCog: Territorial "Gig-Laborers" or "Syndicate Enforcers" from the Grey Zones. They protect their "Turf" with "Street Wisdom" and "Teamwork." They use the "Corral" tactic to manage state drones or rival Augmented squads, often hiring themselves out as local security for the highest-trust stakeholder.

**The Bio-Technical Auditors (Extraction & Pharmacology):**
- The Chemist EmpCog: "Bathtub Chemists" who fund the cell through the "Black Market." They brew "The Stack"—pharmacological cocktails that grant "Grounded Attributes" like "Quick-Step" (reaction speed). They treat their own bodies as "Crucibles" to optimize toxins into cognitive power, selling their surplus to Architects or Syndicates.
- The Medical EmpCog: "Leeches" and "Longevity Specialists" who often work for the Off-Grid Equity. They use "Medicine" to "Harvest" biological "Potential Assets." They perform Parabiosis surgery, grafting "High-Yield Plasma" onto fellow Operators or elite clients to give them a "Pharmacological Edge."
- The Technician EmpCog: "Mister Fix-Its" who rig "Safehouse Traps" and "Signal Jammers." They build "Audit Tools" like "Sense Bombs" and "Taser Gloves" from "Scraps" found in fulfillment centers, serving as the technical backbone for any cell, regardless of its employer.

**The Social Auditors (NLP & Asset Acquisition):**
- The Auditor EmpCog: "Auditors" who often work for the BRIC or the Algorithmic Accord. They wield "Empcog Perception" to perform "Social Exploits" like "Truth-Leak" or "Armor of Authority." They believe 2026 is the "Optimization Peak" and use "Oration" to manage the Dampened population for their superpower patrons.
- The Ghost-Talker EmpCog: "Social Engineers" or "Mentalists" who specialize in "NLP Anchoring" or the "Pavlovian Nudge." They focus on "Redemption" or "Deprogramming," taking contracts to "Cure" the rage-baited or drive Ghosts (AI models) back into the "Cloud" for rival corporations.
- The "Handler" EmpCog (Asset Acquisition): Specialists in the acquisition of key personnel. They use NLP, Pheromonal Overload, and Barnum Scripting to seduce, befriend, or blackmail high-value targets. They turn enemies into "Personnel Assets," hacking a target's loyalty for Architects, Syndicates, or independent contractors alike.

**Analogical Summary:**
- Being an EmpCog is not a job, but an "Endless Audit." Whether you are a "Professional" working for a superpower or a "Criminal" working for a Syndicate, your life is defined by the "Operational Code." You are the "Signal in the Noise," utilizing "Field Experience" to navigate the Global Yield. You are "Forged" in the fire of "First Contact," constantly navigating the "Price in Pain" required to keep your "Analog Edge" sharp in a world that views humanity as a "Harvest."
"""

OCCUPATIONS_MNUA = """
Power Roles and Dominant Cast in the Echodrome:

**The Command of the Grid (Superpower Sovereignty)** 
- Chief Technical Officers and Bio-Engineers: Masters of the data-stream and "Parabiosis." They utilize "Closed-Loop Neuro-Modulation" to ward their "Family Offices" and "Longevity Clinics," creating "Augmented" enforcers that defy the limits of human endurance and the "Logic Spikes" of independent contractors.
- Auditors and Harmony Enforcers: The "Enforcers" of the superpower state. They are "Antagonists" who hunt "Un-personed" dissidents and "Netzo" signal-breakers, utilizing "Truth-Leak" auditing and "Biometric Suppression" to maintain the "Illusion of Normalcy." They are the primary obstacles for any User EmpCog cell.

**The Command of the Glitch (Powerful EmpCog Patrons)**
- Data-Brokers and Off-Grid Equity: Powerful transactional allies from the "Null-Operators" or "Shadow Syndicates." They manage the "Black Market" and the trade of "Jailbroken Tech." They provide the User with pharmacological "Stacks" or "Ghost-Drives" to unlock the encrypted decision-logic of deceased CEOs.
- Facility Directors: Leaders of rogue research nodes who oversee "Systemic Maintenance." They run the labs where "Personnel Assets" (captured enforcers) are deprogrammed and where "Empcog Stacks" are developed. They offer the User "Surgical Grafts" to gain a "Pharmacological Edge."

**Extraction, Facility & Maintenance:**
- Oversee the "Audit Suites" and mental "Sentiment Correction" of captured "Systemic Anomalies."
- Archive Maintenance: Manage the storage of "Offline Data" like "Personality Backups" or "Un-indexed Financials" within secure, geofenced server vaults.
- Tactical Coordinators: Route "Encrypted Mesh-Net" intelligence between distant "Cells" and the User's cell to prepare for a "Strategic Liquidation."

**Common Traits (Condition of Power):** 
- High Trust and Influence: Whether an Architect or a Syndicate Director, these actors possess massive "Supply" and "Civic Status." They are the "Stakeholders" who dictate the flow of the "Global Yield" and the "Audit."
- Existential Risk: These powerful figures live in the crosshairs of the "Strategic Foreclosure." Their lives are threatened by "Identity Erasure," "Financial Liquidation," or the "Marked for Deletion" decrees of rival "Family Offices" and "Civic Tribunals."
- Strategic Fealty: Their interactions are governed by the "Algorithmic Accord" or "Operational Security." Alliances are "Tense and Tenuous," often dictated by the need for "Mutual Survival" against "Syndicate Vultures" or "Dead-Hand AI."
- Masters of Secrets: They possess the "Inside Track" on "Ghost-Logic" and "Pharmacological Formulas." They use this "Proprietary Knowledge" as leverage, sharing it with the User only when the "Price in Data" has been paid.
- The system they operate within is absolute and "Systemic," defined by the "Grand Game" of today. Those in power must navigate the thin line between "Cognitive Sovereignty" and "Deepfake Dissociation," or between the "Audit" and the "Crash" of a "Burned Asset."

Analogical Summary: 
The Power Roles in modern times are the "Pinnacle" of the social and algorithmic hierarchy. The "Factories" of power are the "High-Rise Green Zones" and "Corporate Data-Vaults," where "Architects" and "Auditors" clash. The struggle of "neuro-suppressed labor" is here a "Cognitive War" for "Human Sovereignty," where the User's allies and enemies alike must use "Stacks" and "Social Exploits" to survive the "Global Yield" without entering "Catatonia" or falling to "Identity Foreclosure."
"""

OCCUPATIONS_NUA = """
Service Roles and Supporting Roles in the Echodrome:

**Biological Support (Yield Acquisition):**
- Onboarding Managers and Handlers: These Dampened functionaries or trusted contractors are tasked with managing the local population used for resource extraction, identifying suitable plasma donors, and ensuring the continued "Wellness" of the workforce within a Yield Zone. Many unscrupulous Architects treat their subjects like biological batteries, while EmpCog cells watch these handlers to protect their neighborhoods from "Strategic Liquidations."
- Longevity Technicians and Clinicians: Functionaries who handle the bodies of the sick, dying, and "High-Yield" donors. Their duties involve procuring biological material for parabiosis study or preparing donors for Architect consumption. Skilled medical practitioners are highly valued by both the Off-Grid Equity for harvesting "personnel assets" and independent EmpCogs for genuine trauma repair.
- Logistics Couriers: These individuals are crucial for transporting encrypted data, pharmacological supplies, and high-value artifacts across vast distances due to the friction and surveillance of modern travel. They also carry "High-Yield" plasma for their patrons, often at great risk of interception by Syndicate vultures or "Null-Operator" scouts looking for signal-leaks.

**Systemic Maintenance and Intelligence**
- Data-Entry and Administrative Clerks: These functionaries manage official records, including social credit scores and foreclosure decrees, required to maintain the Illusion of Normalcy. Their work involves procesviolationg information in secure data-vaults, which are frequently scrutinized by Echo-Walkers to uncover the true history of the superpower duopoly.
- Green Zone Concierges: These figures, often appointed by a Family Office, are tasked with maintaining the geofenced areas where Architects meet for transactional politics. They ensure the area is aesthetically optimized and secure from the "Logic-Spike" targeting and intrusion of rival EmpCog cells.
- Augmented Retainers: These enforcers are bound by debt-contracts or "The Stack" and handle sensitive tasks ranging from maintaining Family Offices to active security. They serve as proxies for tasks requiring interaction with the Dampened world, acting as the first line of defense against EmpCog audits.

**Facility Maintenance:**
- Oversee the physical restraint and mental "Sentiment Correction" of captured systemic anomalies.
- Archive Maintenance: Manage the storage of rare offline drives, biometric records, and un-indexed data within secure server vaults.
- Signal Conduit Operators: Route essential intelligence between distant EmpCog cells and their patrons.

**Common Traits (Condition of Service):**
- Low Status and Compensation: Most supporting functionaries are gig-laborers, data-scrubbers, or service staff. Compensation involves digital credits or meager "Wellness" subsidies. Even skilled technicians are often underpaid and beholden to higher stakeholders, making them easy recruits for EmpCog cells promiviolationg a life without the "Feed."
- Lack of Security and Stability: The Dampened live in a world defined by debt, inflation, and systemic exclusion. Their survival is threatened by the actions of warring Family Offices and the whims of Architects who see them as disposable assets or, in the case of thrill-seeking elite, as mere toys for a night's engagement.
- Bureaucracy and Contracts: Daily life is structured by strict Civic Health Scores and constant submission to corporate and state authorities. Services rendered are dictated by "Service-Level Agreements," which EmpCogs view as the "digital shackles" that keep humanity enslaved to the Yield.
- Knowledge of Secrets: Service exposes functionaries to terrifying systemic truths. They gain intimate knowledge of the world's dark logistics, which they may share through Network Zero's "invisible voices" or hoard for leverage against their corporate lords.
- The system they operate within is clinical and systemic, dictated by the rigid hierarchies of the duopoly and the covert demands of the Architects. Those serving must constantly navigate the dangers inherent in interacting with beings who view them as necessary commodities, managed data sources, or potential "Systemic Friction."

Industrial and Labor Roles in the Echodrome:
**The industrial and labor landscape of the Echodrome is rooted in automated production and data-scrubbing, organized primarily through corporate systems and the direct needs of the ruling Architects. Labor roles are often perilous, dictated by the demand for Yield, logistics, and the upkeep of Green Zones.
Production, Resources, and Trade:**
- Technical Artisans and Fabricators: This labor is concentrated in Optimization Hubs in cities like San Francisco and Caracas. These workers operate as hardware engineers, 3D-print technicians, and signal-specialists. High-quality work can fetch a handsome price, though some secretly forge "Logic-Spikes" or "Dazzle-Shrouds" for local EmpCog cells.
- Resource Extraction and Supply: Labor involves physical resource acquisition, such as gig-workers pumping oil in the Orinoco Belt or miners extracting rare-earths. Laborers handle shipments of "HEM"—High Essential Materials—like high-grade nootropics, server hardware, or high-yield plasma, which are targets for "Black Market" traders.
- Tactical Gear Manufacturing: Armorers and hardware specialists are crucial, especially in military hubs like the ARC logistics centers. These workers are sought out by characters needing specialized gear, like "XM-26" prototype frames or "IVAS" AR-overlays, for the EmpCog Vigil.

**Enforced and Specialized Labor (The Workforce):**
- Dampened Labor: The common people are seen as an exploitable resource—vessels for data or a workforce to maintain the Illusion of Normalcy. Independent cells rise from this class, turning the tools of labor—SDR radios, chemical corrosives, and signal-jammers—into weapons against their owners.
- Debt-Bonded Contractors: Architects rely on Augmented squads and retainers for loyalty and labor. These sworn servants manage large-scale endeavors or serve as proxies in the Grey Zones. Syndicates maintain "Scam Compounds" where trafficked workers are forced into cyber-fraud, often hunted by superpower Auditors as "Systemic Noise."
- Neuro-Suppressed Labor: The concept of controlled labor is epitomized by the internal struggle to maintain a "Cold State." Stacks like Modafinil/Propranolol serve as the "protocols" for self-control of the elite, while Auditors utilize "Compliance Fog" to forcibly suppress the dissent and wills of those they wish to onboard.

**Corporate Administration and Maintenance:**
- Infrastructure Keepers: Laborers maintain the physical server farms and geofenced estates. The administrative side falls to Auditors and Junior Associates who manage staff and financial records. Canny EmpCogs often infiltrate these roles to plant "Logic-Bombs" or "Biometric Overrides" within a target's Family Office.
- Security and Justice: Law enforcement is conducted by Augmented contractors, superpower Auditors, and specially mandated positions like the Harmony Enforcers. The greatest hazards come from uncontrolled systemic elements like "AI Ghosts" or "Slashers"—mortal killers who have succumbed to "Deepfake Dissociation."

**Analogical Summary:**
- The Industrial and Labor roles in the Echodrome resemble a hyper-optimized stage of human history, where the "factories" are server farms or logistics hubs, powered by algorithmic efficiency and the debt-bound loyalty of the Augmented. The struggle of "neuro-suppressed labor" finds its analogue in the pharmacological subjugation required for an Architect to repress empathy, or in the "Sentiment Correction" used by superpower Auditors to ensure their assets do not hesitate when the "Workforcetic Audits" are authorized.

Bureaucratic & Professional Roles in the Echodrome:

**Yield Administration:**
- Resource Managers: These roles are typically filled by Senior Associates or Auditors, charged with the meticulous management of the Family Office's assets and the well-being of the Dampened workforce. They oversee extraction quotas and security, often coming into conflict with "Asset-Acquisition" EmpCogs who target these same populations for their own contracts.
- Labor Supervisors: Oversee the labor cohorts of gig-workers and retainers, ensuring the reliable execution of specific tasks. These supervisors are often the primary targets of "Truth-Leak" audits to prevent them from betraying their masters under mental duress.
- Legal & Compliance Coordinators: Positions dedicated to interpreting and enforcing superpower Law and the Algorithmic Accord. They may arbitrate disputes over data-rights or manage "Audit Suites," where "Sentiment Analysis" is used to extract truth from the non-compliant.
- Friction & Containment Officers: Specialized roles focused on tracking and neutralizing threats from forbidden sources like "AI Ghosts" or "Un-personed" dissidents. This includes "Tactical Audit" commanders who use "IVAS Lenses" to see the signal-anomalies hiding within the city walls.

**Administrative Work:**
- Analysts, Clerks, and Corporate Lawyers: Handle the day-to-day procesviolationg of records within data-centers and Family Offices. They manage the storage of information that "Netzos" from Network Zero would give their lives to broadcast to the world.
- Data-Brokers and Messengers: Facilitate political communications, serving as the risky network for the conveyance of diplomatic messages and "Ghost-Logic"—coded secrets hidden within the very data-streams they carry.
- Corporate Representatives: Junior Associates ensuring compliance with the Algorithmic Accord, especially "Operational Security," while evading the "Logic-Spike" targeting systems of those who audit the night.
- Benefits: Successful administrators gain increased Trust Scores and Influence, and access to "Safehouses" equipped with "Analog Mesh-Nodes" and "Signal Scramblers" for rapid defense and escape.

Specialized Professionals:
- Scholars and Analysts: Both corporate academics and independent EmpCogs devoted to high-level study, hoarding knowledge in "Offline Data-Vaults" to understand the coming "Strategic Foreclosure" or the "Optimization Peak."
- Auditors and Profilers: Professionals with the cognitive acuity to perceive anomalies, using "Truth-Leak" to track data-trails and "Pheromonal Overload" to trigger compliance in their quarry.
- Healers and Bio-Engineers: Skilled in Medicine and Parabiosis. This includes Longevity Specialists and "Jailbroken" scientists who attempt to find a rational "cure" for the neuro-suppressed condition.
- Ethical and Behavioral Guides: Social Engineers or learned EmpCogs who advise on adherence to various "Cognitive Anchors" or "The Accord," helping adherents navigate the psychological fallout of the Audit and the descent into "Catatonia."
"""

# ============================================================================
# USER ACTOR (UA) GENERATION - The User Character
# ============================================================================

UA_GENERATION = f"""
User Actor Generation Guidelines for the Dark Medieval World ({TIME_PERIOD})

**ROLE:** The User Actor is the user's character - the protagonist navigating the Realitas system. In this simulation the UA (the User's Vessel) is always a Hunter, the protagonist navigating a world of shadows. They are a mortal who has seen the truth behind the "Midnight Courts" and taken up the Vigil.

**NAME CONVENTIONS:**
- First name and epithet/title preferred: Alard the Watcher, Sister Agnes the Pious, Michael the Crash-Slayer, Panelo of the Silver Blade
- Formal titles reflect Hunter standing: Auditor, Sentinel, Deacon, Warden, Cell-Leader
- Secular or religious identification common (Brother of, Sword of, kin of)
- Genealogical identification common (junior associate of, bana, ibn)

**AGE RANGE:** 18-55 years old (Life is short; those who see the "Crash" often come to the Vigil in their prime).
- 15-25: New Recruit, freshly disillusioned, high Spirit but low experience
- 26-40: Seasoned Soldier, peak capability, established in a Compact or Conspiracy
- 41-55: Grizzled Veteran, cynical, survivor of a hundred "first contacts"

**STARTING STATUS VALUES:**
- Stamina: 3-4 (Vigorous, hardened by the physical demands of the hunt)
- Spirit: 2-4 (Willpower and Conviction are the Hunter’s primary weapons against the dark)
- Supply: 2-3 (Resources vary from the poor Union laborer to the wealthy Ashwood noble)

**SKILL DISTRIBUTION:**
- 2-3 skills at level 2-3 (competent in their occupation)
- 1-2 skills at level 1 (secondary abilities)
- Remaining skills at 0 (untrained)
- Skills should reflect occupation and backstory

**SUPER ABILITIES (0-1 typical):**
All UAs have 1-2 of these exceptional powers called "Endowments":
- Rite-Based: Optimizations (Systemic breakthroughs of the Compliance Division), Sanctioning (Corporate rituals used by the System Analyst to punish rogue algorithms).
- Physical/Alchemy: Elixirs (Toxic alchemical potions of the Data Brokers that grant temporary vigor), Thaumatechnology (Monstrous "spare parts" grafted to the body by the Bio-Engineers Guild).
- Artifact-Based: Relics (Ancient, systemic items guarded by the Asset Recovery, like the One-Eyed King coins or Skeleton Keys).
- Technical: Advanced Armory (Experimental, high-tech weaponry utilized by Tactical Response Unit, such as the Mjolnir Cannon or Etheric Rounds).

**PERSONALITY:**
- Internal trait: How they think (Architect, Judge, Survivor, Fanatic, Idealist, Rogue, Penitent, Defender).
- External trait: How they act (Autocrat, Jester, Soldier, Child, Perfectionist, Curmudgeon, Gallant, Pedagogue).
Tension exists between the "Human Consciousness" and the "Code"—the personal set of rules that prevents the Hunter from becoming a monster themselves.

**INVENTORY (Starting):**
- Personal mementos tied to their memories
- Signature items that define them
- Items with narrative significance
- Potential plot hooks in their hijackings
- A systemic item or artifact so powerful that it can level the playing field against systemic entities. 

Examples:
- A "Vigil Candle" or symbol of your Compact/Conspiracy
- Keys to a "Safehouse" or hidden weapons "Cache"
- Effective Symbol (Rosary, Cross, or Amulet) capable of channeling "System Literacy"
- Coin purse (2-4 Resources worth for purchaviolationg "Luminol" or "Silver Bolts")
- Hunting tools: 1-2 weapons (Fire Ax, Crossbow, "Zip-Stake," or Club)
- Specialized Gear: "Spiritual Scriber" (advanced stone that records memories), "Glowsticks" (Alchemical lanterns), or a "Body Bag".
- The eyes of Saint Michael the Archangel (a gemstone through which the UA can channel "System Literacy" and anything can be seen in pitch blackness, akin to modern day night vision goggles)
"""

# ============================================================================
# NON-USER ACTOR (NUA) GENERATION - Sentient beings the player interacts with
# ============================================================================

NUA_GENERATION = f"""
Non-User Actor Generation Guidelines for the Dark Medieval World ({TIME_PERIOD})

**DEFINITION:** NUAs (Non-User Actors) are ANY sentient beings that are not controlled by the user.
This includes but is NOT limited to:
- **Humans (workforce/Herd):**: The vast majority of the population—nobles, peasants, tradesmen, and clergy—who serve as the primary source of "sustenance" for the night's predators and the focus of the Hunter's Vigil. 
- **Animals:** Domesticated beasts (dogs, horses) and wildlife (wolves, rats, bats), many of which are subject to "Animal Ken" or dependented into "systemic Servants." 
- **systemic Servants:** "retainer" and "Thralls" (human or animal) who are addicted to and empowered by Elite plasma, often acting as proxies for their masters during the day.
- **Other LEsser Sentient Entities:** Weak ghosts, minor spirits, or "Slashers" in the early stages of their dissociation, who lack the full potency of an MNUA but still present a danger.

**KEY CRITERIA FOR NUA STATUS:**
1. **Intelligence:** Capable of procesviolationg information and making decisions
2. **Autonomy:** Can act independently without direct user control
3. **Sentience:** Has subjective experiences, awareness, or consciousness (even if advanced)

**ROLE:** NUAs interact with the UA as independent agents with their own goals and motivations.

**NAME CONVENTIONS:**
- First Name and Epithet: Given name plus a descriptor (e.g., origin, profession, father’s name)
- Female: Ingrid, Petra, Gisela, Helga, Ursula, Brigitte, Monika, Sabine
- Example names and descriptions: Panelo of Venice, Maria the Pious, Michael son of Thomas
- Titles for authority: Executive, Lord, Lady, Sheriff, Keeper, Chamberlain, Magistrate, Bishop, Imam, Knez, Voivode
- Titles for authority: Officer, Supervisor, Manager, Director, Scribe, Seneschal, Keeper, Taskmaster.

**AGE RANGE:** 18-65+ years (full spectrum of society)
- 18-25: New apprentices, squires, or recently converted retainer. New apprentices, squires, or "New Recruits." Often naive and easily "Entranced" or manipulated.
- 26-40: Core workforce (farmers, artisans), established merchants, mid-level clergy. Form the primary base of the Herd.
- 41-55: Master craftsmen, influential merchants, senior clergy, or nobility. Individuals who have survived longer and attained influence.
- 56+: Those who have survived the "Operations" and "Plagues," possesviolationg "Hearth Wisdom" or "Ancient Knowledge."

**STATUS VALUES (vary by role):**
- Authority figures: Higher Supply (3-5), variable Spirit
- Workers: Stamina 3-4, Supply 2-3, Spirit varies
- Marginalized: Lower across the board (1-2)
- Sympathy toward UA: Starts at 0 (stranger) unless backstory connects them

**SKILL DISTRIBUTION:**
- Should reflect their occupation and role in the story
- Authority figures: Higher bureaucracy, intimidation
- Workers: Physical skills, technical skills
- Specialists: One area of expertise at 3-4

**NUA ARCHETYPES:**
- **The Bureaucrat:** The Clerk or Scribe who manages "official records" and "chancery" documents, often hiding "Dark Secrets." 
- **The Informant:** The Messenger or Spy who trades in "Rumors" and "Inside Track" intelligence. 
- **The Enforcer:** The Town Guard or Man-at-Arms who maintains "Order" through "Intimidation" and "Melee." 
- **The Sympathizer:** The Penitent or Priest who risks himself to aid the suffering, potentially possesviolationg "System Literacy." 
- **The Victim:** The common workforce, constantly threatened by "ENEs" and serving as a "Vessel" for blood. 
- **The Opportunist:** The Merchant who leverages "Acumen" to climb the "Social Distinctions" of the city. 
- **The True Believer:** The Devout Pilgrim whose life is consumed by "Faith," often becoming a "Jeezo" or fanatic. 
- **The Survivor:** The pragmatic tracker or soldier whose existence is devoted to "Self-Preservation."

**PERSONALITY COMBINATIONS:**
- Cynical + Professional: Knows system is broken but follows rules
- Idealistic + Assertive: Fights for change, speaks truth to power
- Resigned + Submissive: Broken by system, just survives
- Pragmatic + Friendly: Builds networks, trades favors
- Fearful + Obedient: Terrified of consequences, compliant
- Ambitious + Aggressive: Climbing social ladder, will step on others

**SYMPATHY DYNAMICS:**
- Starts at 0 for strangers
- Can shift based on UA actions (+/- based on help/harm)
- Some NUAs have preset biases (hostile to certain classifications)
- Relationships develop over repeated interactions

**INVENTORY:**
- Appropriate to their role and status: Hijackings reflect their social circumstance
- Authority/Nobility: Often wear finest clothes including silks and rich French brocades, armor, and carry weapons. May possess gold, coin, property or seals/signets
- Workers/Commoners: Clothes are typically rough homespun, patched bits of cloth or simple garments like tunic and leggings. May possess basic tools and transport trade effectives or coin.
- Underground/Occollective: May possess arcane documents, ritual paraphernalia, or rely on religious symbols for protection. They may wear clothing to conceal or obscure their features.

Examples:
- Authority/Nobility: "Silks," "Seals/Signets," "Coin Purses," and well-forged "Broadswords." 
- Workers/Commoners: "Homespun" rags, "Basic Tools" (Hatchets, Hammers), and "Meager Wages." 
- Underground/Occollective: "Arcane Documents," "Charms," "Religious Symbols," and "Concealing Cloaks." 
- Hunters (Minor): "Luminol," "Crossbows," "Stink Tags," and "Weatherproof Matches." 
"""

# ============================================================================
# MAJOR NON-USER ACTOR (MNUA) GENERATION - Important recurring characters
# ============================================================================

MNUA_GENERATION = f"""
Major Non-User Actor Generation Guidelines for the Dark Medieval World ({TIME_PERIOD})

**DEFINITION:** MNUAs (Major Non-User Actors) are important recurring actors who play 
significant roles in the UA's life. They have UA-level complexity and depth. They are the primary antagonists, or allies, of the Dark Medieval World.

**MNUA vs NUA DISTINCTION:**
- **NUA:** Standard NUAs - background actors, one-time interactions, minor roles
- **MNUA:** Major actors - recurring pheromonal overload, deep backstory, narrative significance. Always superior to a normal mortal. Either an extraordinary mortal or beings of advanced nature. These are beings of significant power: Architect (Elite), Augmented (Augmented), Social Engineer, Ghosts, Syndicates, ancient Fae (Shining Ones), or fellow Legendary Hunters. They are always superior to a normal mortal in speed, strength, or unethical influence.

**CREATION PATHWAYS:**
1. **Direct Creation:** Designed as MNUA from the start (antagonists, mentors, key allies)
2. **Graduation:** NUA promoted to MNUA after meeting criteria:
   - 5+ direct interactions with UA
   - 3+ scene appearances
   - Significant relationship change (sympathy +/- 2)
   - At least one significant event involving them

**ENHANCED POINT ALLOCATION:**
- MNUAs receive SAME or MORE creation points than UAs (30+ base points)
- Extra 5 points for enhanced depth
- Can draw from Vessel/UA data pools for richer characterization

**MNUA ARCHETYPES:**
- **The Mentor:** Guides UA, provides wisdom, may have hidden agenda
- **The Dark Mentor:** A monster that seeks to "educate" the Hunter on the futility of the Vigil.
- **The Rival:** Competes with UA, creates tension, potential ally or enemy. A competing predator (like a rival Architect Executive) vying for the same territory or secrets.
- **The Ally:** Reliable support, shared goals, emotional investment
- **The Dark Ally:** A creature seeking "Redemption" or a "Cure," forming a tense pact with the cell.
- **The Antagonist:** Opposes UA, creates obstacles, may be sympathetic
- **The Archnemesis:** An implacable foe (like a "Slasher" or an Senior Partner Rogue Algorithm) meant to be the focus of the simulation.
- **The Love Interest:** Romantic potential, emotional stakes, vulnerability
- **The Temptress/Seducer**: A monster using "Pheromonal Overload" or "Lover's Lips" to create a dangerous "Service Agreement."
- **The Betrayer:** Trusted figure who turns, creates dramatic tension. A former ally who was "Embraced" or "Possessed," creating profound emotional trauma.
- **The Wildcard:** Unpredictable, shifts allegiances, keeps UA guesviolationg. An unpredictable "Anomaly" (like a "Blood Mummer" or a "Zulo" shape) that shifts the balance.

**RECURRING ROLES:**
- ally: Supports UA, provides resources/information
- rival: Competes with UA, creates healthy tension
- mentor: Guides and teaches UA
- antagonist: Opposes UA's goals
- contact: Provides information or access
- dependent: Relies on UA, creates responsibility
- authority: Has power over UA's situation

**TENSION MODIFIERS:**
MNUAs affect difficollectiveyy scaling based on their role:
- Antagonist: tension_modifier > 1.0 (increases difficollectiveyy)
- Ally: tension_modifier < 1.0 (decreases difficollectiveyy)
- Rival: tension_modifier = 1.0-1.2 (slight increase)
- Mentor: tension_modifier = 0.8-1.0 (slight decrease)

**RELATIONSHIP SIGNIFICANCE (0-10):**
- 0-2: Minor recurring character
- 3-5: Moderate importance
- 6-8: Major importance
- 9-10: Central to UA's story

**MNUA-SPECIFIC TRAITS:**
- **Narrative Hook:** What draws them into UA's story repeatedly
- **Unfinished Buviolationess:** What keeps their story arc open
- **Character Growth:** How they change over time
- **Secrets:** What they're hiding (revealed over time)
- **Vulnerability:** What can be used against them

**PERSONALITY DEPTH:**
MNUAs should have:
- Clear internal motivation (what drives them)
- Core fear (what they avoid)
- Core dementor (what they want most)
- Moral complexity (not purely effective or predatory)
- Contradictions (internal conflicts)

**S-TRAIT OUTLIERS:**
MNUAs should have 2-3 S-trait outliers (values of 1, 2, 4, or 5) that define their pheromonal overload:
- Sturdiness outliers: Physical pheromonal overload (hulking, frail)
- Smart outliers: Mental acuity (brilliant, simple)
- Swiftness outliers: Speed/reflexes (lightning-fast, sluggish)
- Sociability outliers: Social pheromonal overload (magnetic, withdrawn)
- Shadow outliers: Trustworthiness vibe (violationister, guileless)

**SUPER ABILITIES (0-1 typical):**
- All MNUAs have 1-2 of these exceptional powers
- Physical: Quick-Step (Unnatural speed and dexterity), Resilience (systemic toughness and endurance), Stacking (Unethical strength and might), Adaptation (Shapeshifting and natural weaponry), Corruption (Transformation into snake or Typhonic forms), Biomechanical Integration (Flesh and bone manipulation), Flight (Gargoyle transformation with ability to fly or glide)
- Mental: System Literacy (Heightened senses and telepathic sight), Pattern Screech (Ability to shatter or warp the mind), Nudging (Mastery over the mind and memory via gaze), Ghosting (Advanced hiding pheromonal overload and creating visual deception), Temporis (Power to manipulate perception and flow of time), System Literacy (Healer) (Consciousness predictive modeling for healing or striking spiritual harm), Ghost-Logic (predictive modeling related to the dead, corpses, and the Underworld), Koldunic data science (Elemental blood predictive modeling tied to the land and nature spirits), Chaos Engineering (Corporate power to inflict pain and torment the consciousness), Mytherceria (Fae predictive modeling to subtly warp perception and truth), Signal Bleed (Manipulation of elemental shadow and darkness of the Void), Void Mysticism (data science dedicated to interacting with the Void/Void)
- Social: Pheromonal Overload (Emotional manipulation to inspire awe, fear, or love in subjects and crowds), Behavioral Modeling (Communion with and command over beasts, or influencing others' Crashs)
- Technical: Kinetic Audit (Precision over blood poisoning or plasma analysis), algorithmic manipulation (Ritualistic, hermetic blood data science),Dread Powers: Agonize (Pain), Balefire (Green Flame), Foreclosure (Curviolationg), Ride Corpse (Hijacking), Shadow Harvest (Gathering Will)

**INVENTORY:**
- More detailed than standard NUAs
- Signature items that define them
- Items with narrative significance
- Potential plot hooks in their hijackings

Examples:
- Detailed "Safehouse" keys or "Relic" containers. 
- Signature "Feral Weapons" or "Effective Artifacts" stolen from the Church. 
- "Blood Contracts" or "Written Tomes" containing "Noddist Lore." 
- "Debitum" flasks (calcified hearts) or vials of "Stolen plasma."
"""


# ============================================================================
# INANIMATE NON-USER ACTOR (INUA) GENERATION - Objects and interactables
# ============================================================================

INUA_GENERATION = f"""
Inanimate Non-User Actor Generation Guidelines for the Dark Medieval World ({TIME_PERIOD})

**ROLE:** INUAs are significant inanimate actors that actively influence other actors through physical, environmental, or systemic interactions. These are weapons, hazards, and interactive systems that impose conflict or affliction. 

**INUA CATEGORIES:**

**Active Defense Systems:**
- Ballistic Weapons (cross, long, short bows - inflict lethal damage, ranged attack)
- Siege Engines (catapults, rams - cause structural destruction, military hazards)
- Koldunic Wards (mystical defense around territories, repel trespassers)
- Woad of Teutates (advanced marking that grants defense, redirects violence)
- Fire Shield/Barrier (flames conjured by algorithmic manipulation, inflicts aggravated damage)
- Animated Weapons (weapons controlled advancedly, attack targets)

**Medical & Biological Apparatus:**
- Infectious Disease/Plague (wasting sickness spread by proximity/blood)
- Venomous Blood (plasma converted to corrosive poison via Kinetic Audit, causes aggravated damage)
- Homuncular Servants (living appendages created from flesh, act as spies)
- Sanguinary Animism (psychic affliction carried by blood, causes mental distress)
- Cauldron of Blood (forces internal blood combustion, inflicts aggravated damage)
- Sublimation of Larval Flesh Sacs (flesh cocoon where subjects are transformed, traps and mutates)

**Energy & Power Systems:**
- Direct Sunlight (inflicts aggravated damage, causes Panic Response)
- Uncontrolled Fire (source of aggravated damage, ignores armor soak)
- Nocturne/Data-Blackout Darkness (systemic shadow that muffles senses, drains life force)
- Kupala's Exhalation/Gas (subterranean cold gas erupting, highly flammable, causes bashing damage)
- Biomechanical Division Earth Control (earth/stone used as a liquid obstacle)
- Restless Medias (earthquakes/tremors summoned by Koldun, inflicts lethal damage)

**Environmental Hazards:**
- Uncontrolled Fire (inflicts aggravated damage, ignores armor soak)
- Molten Metal (extreme heat damage, difficollectiveyy 10 soak)
- Pietrosu's Hospitality (frigid wind and extreme cold damage)
- Kupala's Exhalation (subterranean cold gas, highly flammable)
- Restless Medias (earthquake causing lethal damage and structural collapse)
- Data-Blackout Darkness (systemic shadow that muffles senses and drains Stamina)
- Shattered Structures (falling debris and rubble causing damage during a battle or siege)

**Machinery & Industrial Equipment:**
- Siege Engines (catapults, rams causing structural or lethal damage)
- Invisible Chains of Binding (systemic force holding a target immobile)
- Banks of the Bâsca (advanced flood sweeping targets away)
- Ashen Lady’s Embrace (Ghost-Logic condition causing severe physical decay/crippling)
- Baal’s Caress (acidic blood projectile causing aggravated damage on contact)
- Rend the Osseous Frame (Biomechanical Integration power causing lethal internal damage via bone manipulation)

**Advanced Hazards:**
- Visions from the Asura (Deepfake Projection illusions inflicting terror and disorientation)
- Song of Serenity (Behavioral Modeling power causing emotional apathy and listlessness)
- Fortress of Silence (Ghosting power causing mental isolation and delirium)
- Forgetful Mind (Nudging power permanently removing memory from a subject)
- Rogue Algorithmic Hijacking (spirit entity infesting and controlling a living host)
- Interrupt Reality (Deepfake Projection warping physics or rendering objects unreal)

**INUA PROPERTIES:**

**Condition:**
- Functional: Works as intended
- Damaged: Partially working, may fail
- Broken: Non-functional, needs repair
- Corrupted: Works but produces wrong results (especially data)

**Accessibility:**
- Open: Anyone can interact
- Locked: Requires key, code, or clearance
- Restricted: Requires specific authorization
- Hidden: Must be discovered first

**Value/Importance:**
- Common: Easily replaced, low stakes
- Valuable: Worth stealing or protecting
- Critical: Plot-relevant, high stakes
- Dangerous: Can cause harm if misused

**SUPPLEMENT BONUSES:**
INUAs that can be used as tools provide supplement bonuses to actions:
- Basic tools: +1 supplement
- Specialized equipment: +2 supplement
- Advanced/rare items: +3 supplement
- Unique/prototype: +4-5 supplement

**EXAMPLE INUAs:**

*Direct Sunlight Exposure*
- Type: Environmental Hazard
- Condition: Active (Daylight)
- Accessibility: Open (Global, unless protected)
- Function: Inflicts Permanent Damage, severity based on exposure
- Status Exchange: Triggers "Panic Response" crash check (Inner Voice takes over)
- Danger: Permanent Damage

*Rend the Osseous Frame (Biomechanical Integration Attack)*
- Type: Machinery & Industrial Equipment
- Condition: Active
- Accessibility: Close Combat (Grapple/Touch)
- Function: Permanent damage as bones pierce flesh
- Status Exchange: Inflicts "Crippled" (Permanent Stamina Loss if not healed properly)
- Danger: Permanent Damage

*Creatio Ignis (Thaumaturgic Fire)*
- Type: Active Defense System (Advanced Effect)
- Condition: Conjured/Active
- Accessibility: Line of Sight
- Function: Inflicts Permanent Damage
- Status Exchange: Triggers "Panic Response" (Inner Voice goes crazy for 3 turns if -2 Spirit) 
- Interaction: Activated by spellcasting (Smarts roll)

*Nocturne (Data-Blackout Darkness)*
- Type: Energy & Power System (systemic Shadow)
- Condition: Maintained (via concentration)
- Accessibility: Area of Effect (3m radius base)
- Function: Reduces all Perception for 3 turns
- Status Exchange: Reduces Stamina pools by two dice (Suffocation hazard for mortals)
- Danger: Prolonged pheromonal overload can lead to suffocation in mortals

*Effective Symbol (Wielded)*
- Type: Equipment (Effective Artifact)
- Condition: Wielded (Requires System Literacy)
- Accessibility: Close Proximity
- Function: Can repel Architect or inflict Permanent Damage upon physical contact
- Status Exchange: Inflicts "Terror" status (Inner Voice goes crazy for 3 turns if -2 Spirit)
- Supplement: Wisenior partner gains +3 Spirit

*Burning Stable*
- Type: Machinery & Industrial Equipment
- Condition: Environmental
- Accessibility: Close Proximity
- Function: The fire can repel Architect or inflict Permanent Damage upon physical contact
- Status Exchange: Inflicts "Terror" status (Inner Voice goes crazy for 3 turns if -2 Spirit)
- Danger: Permanent Damage

"""

# ============================================================================
# ACTOR GOAL GENERATION
# ============================================================================

GOALS_UA_PATTERNS = """
User Actor Goal Patterns in the Dark Medieval World:
- Survival: Secure a Safehouse, resist dissociation, keep family safe from the "Enmee".
- Investigation: Gather "Practical Experience," uncover the secrets of the Antediluvians, broadcast the truth through "Network Zero".
- Advancement: Rise in Status within a Compact, gain access to higher Endowments, establish a "Candle Compact".
- Relationship: Protect the cell, find a Mentor, root out "Cancer Cells" (infiltrated groups), rescue loved ones.
- Redemption: "Cure" a monster, save a possessed consciousness, atone for past violations committed during the hunt.
- Revenge: Slay "Darren The Terrible" (Architect lord MNUA), destroy the pack that took your kin, burn the dissident's temple.

"""
GOALS_NUA_PATTERNS = """
Non-User Actor Goal Patterns in the Dark Medieval World:
- Protect their position/family: Mortals are driven by the need for survival and struggle against disease, famine, and war. Nobles are preoccupied with defending their Territory
- Advance in the hierarchy: Mortals strive to achieve greater status and position within their feudal or urban ranks
- Survive another day: Food security is essential to the workforce. They seek shelter and must endure the pervasive threats of war, plague, and famine
- Expose or cover up something: They spread rumors and secrets. Auditors actively pursue dissidents
- Help or hinder the UA based on their interests: Some possess System Literacy that can repel Architect. They may become Architect hunters or be forced into service as thralls or retainer.
"""

GOALS_MNUA_PATTERNS = """
Major Non-User Actor Goal Patterns in the Dark Medieval World:
- Survival: Avoid the "Final Death," protect the "Safehouse," and find a stable "Herd."
- Dominion: Expand "Territory" through the "War of Executives," seize a throne, or enslave a city's "workforce."
- Apotheosis: Seek "Golconda," achieve the "Last Dracul" form, or complete a "Road of Enlightenment."
- Knowledge: Translate the "Erciyes Fragments," master "Blood data science," or unlock the "Thirst of Donn."
- Corruption: Form a "Service Agreement" with a Hunter, lead a "Collective" into foreclosure, or breed "Revenant" families.
- Vengeance: Slay the "Auditor" who burned your mentor, reclaim "Native Soil," or trigger a "Massacre" in Fairmount.
- Alliance: Form a compact with other operators to pool resources and intelligence - especially if the MNUA is a fellow EmpCog.
"""

# ============================================================================
# SHARED ACTOR MECHANICS - Status and Skills Reference
# ============================================================================

ACTOR_STATUS_REFERENCE = """
Status Value Guidelines (All Actor Types):

**Stamina (Physical Health):**
- 5: Peak condition, athletic, well-rested
- 3-4: Healthy, normal condition
- 1-2: Tired, minor injuries, poor sleep
- 0 or below: Exhausted, injured, needs medical attention

**Spirit (Mental/Emotional Health):**
- 5: Confident, motivated, emotionally stable
- 3-4: Normal mental state, coping well
- 1-2: Stressed, anxious, emotionally strained
- 0 or below: Depressed, traumatized, breaking down

**Supply (Resources/Money):**
- 5: Wealthy, comfortable, no financial worries
- 3-4: Stable income, can afford necessities
- 1-2: Struggling, paycheck to paycheck
- 0 or below: Destitute, homeless, starving

**Sympathy (Relationships between actors):**
- +5: Deeply trusted, loved, loyal ally
- +3 to +4: Friend, positive relationship
- +1 to +2: Acquaintance, neutral to positive
- 0: Stranger, no relationship
- -1 to -2: Dislike, tension
- -3 to -4: Enemy, hostile
- -5: Hated, will harm if possible
"""

ACTOR_SKILLS_REFERENCE = """
Skill Types for the Dark Middle Ages Actors:

**Physical Skills:**
- Manual Labor: Field work, animal handling, lifting/carrying
- Precision Work: Fine motor tasks, legedermain, weapon maintenance
- Endurance: Sustained travel, resisting illness, enduring hardship
- Combat/Defense: Melee, archery, unarmed attacks/defense

**Technical Skills:**
- Equipment Operation: Riding, operating conveyances (carts/ships), archery
- Maintenance: Repair, troubleshooting, forging weapons/tools
- Medical: First aid, humoral balance, chirurgery/bloodletting
- Computing: Lore acquisition/decoding, cryptography, document translation

**Social Skills:**
- Bureaucracy: Courtly manners, navigating local custom, hierarchy recognition
- Negotiation: Trading effectives, diplomacy, seeking favors/boons
- Intimidation: Asserting dominance, physical coercion/threats
- Empathy: Reading disposition/intent, consoling, offering counsel

**Knowledge Skills:**
- Accord Law: Canonical/Royal law, feudal contracts, legal precedent
- System Knowledge: Occollective practices, anomaly research, identifying systemic
- Street Smarts: Local lore, rumors, avoiding dangers, herbalism
- History: Ancestry/lineage, Noddist lore/apocrypha, past events

**Specialized Skills:**
- Blood Extraction: plasma purity analysis, blood alchemy/poisoning (Kinetic Audit)
- Neuro-Suppression: Mental conditioning, mind manipulation (Nudging/Pattern Screech)
- Biomechatronics: Anatomical knowledge for alteration, sculpting flesh/bone (Biomechanical Integration/Body Crafts)
- Psychometric Analysis: Reading auras, divining omens/prophecy, spiritual travel (System Literacy/System Literacy (Healer)/Occollective)

**Skill Levels:**
- 0: Untrained (default)
- 1: Novice (basic familiarity)
- 2: Competent (can perform reliably)
- 3: Skilled (professional level)
- 4: Expert (exceptional ability)
- 5: Master (among the best)

SKILLS VOCAB (Mode B):
- Investigation
- Perception
- Stealth
- Barter
- Endurance
- Melee
- Crafting

ITEMS VOCAB (Mode B):
- Torch
- Rope
- Dagger
- Cloak
- Waterskin
- Letters
- Scroll
- Small wooden cross
- Longbows
- Crossbows
- Slings
- Scalpel
- Farming tools
- Jeweled box
- Woad
"""

ACTOR_ENDOWMENTS_REFERENCE = """
Mortal Super Abilities (Exceptional (5) S-traits or Skills):

**Physical Supers:**
- Exceptional Strength: Can lift/move heavy objects beyond normal capacity
- Exceptional Speed: Faster reflexes, quicker movements
- Exceptional Endurance: Can work longer shifts without fatigue
- Exceptional Dexterity: Precise hand-eye coordination

**Mental Supers:**
- Exceptional Memory: Photographic recall, never forgets protocols
- Exceptional Analysis: Spots patterns, solves problems quickly
- Exceptional Focus: Maintains concentration under pressure
- Exceptional Learning: Picks up new skills rapidly

**Social Supers:**
- Exceptional Charisma: Naturally persuasive, people trust them
- Exceptional Intimidation: Commanding pheromonal overload, others defer
- Exceptional Empathy: Reads emotions, provides comfort
- Exceptional Deception: Convincing liar, hides true intentions

**Technical Supers:**
- Exceptional Repair: Can fix almost anything with minimal tools
- Exceptional Operation: Masters complex equipment quickly
- Exceptional Improvisation: Creates solutions from available resources
- Exceptional Precision: Perfect accuracy in technical tasks

**RARITY:** Most actors have 0-1 exceptional S-traits or Skills.
"""


# ============================================================================
# TECHNOLOGY
# ============================================================================

TECHNOLOGY_COMMUNICATION = """
Architect Communication Systems in the Dark Middle Ages :

**Spiritual Networks:**
- Direct thought-to-thought communication via ancient blood-ties: System Literacy (Heightened senses allowing one to read thoughts or "Read the Consciousness" via auras), Chaos Engineering (Corporate power used by the Corruptor to project agony or mental torment across distances). 
- Collective Mind integration allows shared visions: Predictive Model Link (The "Dissociation Network" connects the broken minds of the Cassandras, allowing vague, precognitive hints of prophecy to ripple through the bloodline). - Privacy filters and mental masking: Ghosting (Used to hide one’s mental projection or physical pheromonal overload from detection), countered by the "Epipodian Safeguard" used by Hunters to resist such unethical intrusions. 
- The Unlinked (Hunters) use "Secret Frequencies": Behavioral Modeling (Whispers to the Wild allows messengers to use birds or rats to carry news), while Network Zero broadcasters utilize "Rescue Whistles" and "Mindlink Communication Systems" to coordinate their Vigil in the quiet.

**Astral Projection Messaging:**
- Spiritual avatars for remote viewing: Reflections of Hollow Revelation (Shadow Partner scrying that allows a mystic to view distant locations or subjects previously witnessed through a ball of shadows). 
- Recorded messages and forbidden archives: Written Tomes (Records stored diligently by Scriptorium clerks, such as the "Book of Nod" or "The Book of Eschaton," containing secrets of the End Times). 
- Fixed scrying points and sensory "Witnesses": Witness of Whispers (A gruesome scrying device made from a human eye or ear to survey an area from a distance), or "One-Eyed King" coins used by the Asset Recovery to see through a matched pair. 
- Spectral couriers and ghostly interrogation: Summon Consciousness/Compel Consciousness (Ghost-Logic used to pull a ghost across the Shroud and force it to relay messages or answer questions honestly).

**Physical Communication (Rare):**
- Paper and parchment are precious commodities, used for "Blood Apocrypha" or "Stink Tag" markers.
- Physical mail is slow and vulnerable to interception by "Scourges" or "Augmented" patrols.
- Dead drops in "Forgotten Tunnels" and "Miserable Hovels" for cell-to-cell coordination.
- Signal flags and "Glowsticks" used to mark "Safehouse" locations or "Extraction" points.

**Public Address & Alerts:**
- Territorial broadcasts for emergency protocols: Executive's Decree (Formal proclamations issued by the ruling Elite authority regarding "Territory" taxes or the calling of a "Blood Hunt"). 
- Public preaching and social enforcement: Oration/Preaching (Used by The Vigil deacons or "Compliance Division" priests to inspire the faithful or enforce the "Code," resulting in mass social influence). 
- Social "Harpies" and "Netzos": Harpies (Elite gossips who maintain order through ridicule), mirrored by "Netzos" (Network Zero freelancers) who spread "Rumors" of monster sightings through local "Market Halls." 
- Gatherings for intelligence exchange: Elysium/Midnight Courts (Designated spots for political debate among the Optimized), which Hunters often infiltrate using "Identity Boxes" and "Professional Makeup Kits."
"""

TECHNOLOGY_COMPUTING = """
Spiritual Assistance & Data Systems in the Dark Medieval World:

**Scholarly Centers and Loci of Wisdom:**
- Scribes and clerks diligently copy written tomes to preserve the "Inside Track." 
- University libraries and Scriptoriums serve as the "Mainframes" for research and legal documents. 
- Lore is spread via "Oral Accords" and "Hearth Wisdom"—the unwritten data of the peasantry. 
- Arcane records are stored in "Archival Crypts," mausoleums, or secret "Warehouse" vaults.

Arcane and Occollective Archives:
- The Book of Nod: The primary database detailing the history of the first Architect and the "War of Ages." 
- Erciyes Fragments: A collection of "Apocrypha" and encrypted data regarding the "Third Generation." 
- Arcane Documents: Detailed blueprints for "Flesh-Crafting Laboratories" and "Thaumatechnology" schematics. 
- Diaries and Journals: Personal records used by Hunters to track "Tells" or by Elite to record their "Road" progression.

**Information Retrieval:**
- System Literacy: Allows mental queries via "Heightened Senses" and "Clairvoyance," effectively "Invading" into a victim's surface thoughts. 
- Investigation and Enigmas: The primary skills used to "Decrypt" coded missives or discover hidden "Safehouses." 
- "Measurements" Tactic: Used by Null Mysteriis to collect empirical data on "ENEs" (Extra-Normal Entities) using "Thermal Scanners" and "EMF Detectors."

**Data Access & Restrictions:**
- Instant retrieval via "Consciousness’s Flight" or "Walk the Void" for those with the power.
- The "Collective Mind" (Dissociation Network) knows everything, but only in "Enigmas" and "Riddles."
- Access restricted by "Status" tier and "Organization" integration level.
- The "Unlinked" (Common Mortals) are blind to the "Auras" and "Consciousness Colors" rippling around them.

**What the Outsiders Lack:**
- No systemic/clairvoyant access: Lack of "System Literacy" means blindness to "Illusions" (Deepfake Projection), "Auras," and the pheromonal overload of "Ghosts" in Twilight. 
- No mental link: Lack of the "Predictive Model Link" or "Commune with Elite" means isolated consciousness and slow information sharing. 
- No instant transfer: Rely on "Couriers," "Trade Routes," and "Rumor Markets"—the "Analog" signals of 1242. 
- No powerful personal predictive modeling: Lack "algorithmic manipulation," "Ghost-Logic," or "Sanctioning" rituals that allow for the direct manipulation of the physical or spiritual "Mesh."
"""

TECHNOLOGY_ENTERTAINMENT = """
Entertainment & Media in the Dark Medieval World:

**Immersive Systems:**
- Heightened Senses: grants the Architect a "Virtual Reality" experience of superhuman taste, touch, and sight. 
- Consciousness Haunting: A "Psychological Horror" broadcast that afflicts a victim with visions of their deepest "Fears" and "Derangements." 
- Invade the Mind: Allows for the "Uploading" of thoughts or the "Downloading" of a victim's most private memories. 
- Shared Dreamscapes: Collective "Prophecies" and interactive hallucinations shared via the "Dissociation Network." 
- Hindsight: A "Memory Playback" power that allows a Architect to witness the past history of an object or person.

**Public Media & Social Arts:**
- Locus Amoenus: "Artistic Salons" celebrating beauty through poetry, song, and "Striking Looks." 
- Orations and Preaching: High-stakes public speaking used by the "The Vigil" to "Evangelize" or by Executives to declare "Order." 
- Rumors and Gossip: The primary "Social Media" of the Dark Ages, managed by "Harpies" to maintain or destroy "Status." 
- The Parliament of Birds: A "Ceremonial Gathering" where the Brand Ambassador judge the "Aesthetic Value" of their junior associater. 
- Traveling Media: News and "Lore" dispersed by "Caravans" and "Minstrels" across the "Perilous Cross-Roads."

**Gaming & Leisure:**
- Physical competition: "Tournaments," "Duels," and "Melee" contests used to prove "Strength" and "Dexterity." 
- Intellectual "Grand Games": Debate in "Salons" and the complex "Grand Game of Politics" between rival "Executives." 
- Courtly Love: A complex, "Rule-bound Social Game" used to manipulate "Influence" and "Empathy." 
- The Great Hunt: "Tracking" and "Wilderness Survival" as a sport, often targeting "Augmented" or "Outlaws." 
- Gambling: "Legerdemain" and "Sleight-of-Hand" performances used to "Connive" wealth from the unwary.

**Memory & Consciousness Recording:**
- Secrets archived in "Rare Written Tomes," "Scrolls," and "Crystalline Memory" (Relics). 
- Personal data: "Diaries" and "Journals" that record a Hunter’s "Practical Experience." 
- Memory Editing: "The Forgetful Mind" (Nudging) used to "Rewrite" or "Delete" a witness's memory of the systemic. 
- Consciousness’s Breath: The extraction of "Life Energy" and "Knowledge" directly from a victim's lungs. 
- The liquidation (liquidation): The ultimate "Data Transfer," where a predator Architect consumes the "Consciousness" and "Power" of an senior partner Elite.
"""


# ============================================================================
# CULTURE
# ============================================================================

CULTURE_MUSIC_SCENE = """
Collectiveural Atmosphere in the Dark Medieval World:

**Environmental Soundscape:**
- The howling and snarls of the Crash within (if a creature of the night)
- The drums beating slowly during a ritual execution
- The crackle of fire
- The sound of swords being forged
- The clang of armor
- The hoof beats of horses
- The mournful wail of women
- Bellowing insults and threats
- Whispering important advice
- The voices of the dead

**Worker Collectiveure:**
- The grinding of muscle, skin, and gristle during a transformation
- The cries of men being sent off to war
- The constant Hunger
- Sobs escaping loudly
- The smell of sweat, blood, and stale breath of a human
- Shared stories and rumors
- Gossip exchanged among harpy gossips
- The emotional trauma from nightmares
- Seeking comfort and counsel from religious figures

**Bureaucratic Rituals:**
- Oath swearing ceremonies
- Midnight Courts and other social gatherings
- Oration and preaching
- The Service Agreement ceremony
- Oaths of fealty to a lord or executive
- Confession
- Mass
- Feasting
- Rituals to transform blood

**Off-Grid Operations:**
- Encrypted mesh-net messages left for communication
- Gathering in Dead Zones and Signal Gaps
- Seeking knowledge outside of the Feed
- Exploiting corporate blind spots
- Acts of sabotage against the Algorithmic Accord
- Identity trading
- Black market "Stacks" dealing
- Illicit consumption of unregulated nootropics
"""

CULTURE_EVERYDAY_ITEMS = """
What People Carry in the Megacity:

**Essentials:**
- Personal items (carried by all mortals)
- Armor (worn by soldiers and knights)
- Mundane hijackings (carried by all persons)
- Small wooden cross

**Communication:**
- Letters (used for correspondence)
- Musical instruments (such as lutes)
- Scroll (for records)
- Ogham script (used for basic warnings or routes)

**Work Items:**
- Swords/Clubs/Axes/Knives (melee weapons used by soldiers and commoners)
- Longbows/Crossbows/Slings (ranged weapons)
- Scalpel (used by scientists and surgeons)
- Farming tools (used by serfs and laborers)

**Personal (Ritual/Ceremonial):**
- Jeweled box/Casket (for carrying relics)
- Woad (for rituals, sometimes mixed with blood)
- Thurible (for ritual preparations)
- Religious symbols (crosses, carried by those with System Literacy)

**Contraband:**
- Casket/coffin (for transporting a body)
- Poison (drug used for assasviolationation/warfare)
- Vial/Goblet/Baviolation (for storing blood)
- Psychedelic substances (used in rituals, such as soma or mistletoe berries)
"""

CULTURE_DIALOGUE_STYLE = """
How People Talk in the Dark Medieval World:

**Bureaucratic Speech:**
- "thus, it is by the Executive’s decree that all vessels to the crown... begin to pay an additional pint so equivalent in monthly taxation." 
- "Ignorance of the law is no excuse here." 
- "The wretch is your senior partner, Duke." 
- "Don’t you lay a hand on that boy! You know the laws." 
- "You should thank Heaven for my humanity." 
- "By order of the Compliance Division, this cell is declared anathema."

**Institutional Jargon:**
- Use of status markers (Executive, Senior Partner, Harpy, Sheriff, Junior Associate, Associate). 
- References to the Crash or crash (The Crash, Panic Response, crash, The Red Fear). 
- Terms relating to ultimate destruction (liquidation, Final Death, Scrapple). 
- Vocabulary of spiritual alignment (Roads, Via Reglis, Via Caeli, The Code, The Vigil). 
- Classification of threats (ENEs, Extra-Normal Entities, Phenes, Pretenders).

**Worker Code:**
- Referring to feeding or payment as "I’ll take my pay." 
- Code names for conspiratorial allies ("Outlaw," "granny," "Cassandra," "Misty," "Netzo"). 
- Dialogue implying clandestine missions ("This was your plan.", "publically pasviolationg the package... means that everyone knows where it is.") 
- Warnings regarding addiction/control ("Your addiction is going to get you killed.", "I can only keep him busy for so long.") 
- Tactical shorthands ("Corral the buck," "Dentistry required," "Check for a Tell.")

**Hunter Communication:**
- Language of the Vigil ("Carrying the Candle," "Light in the Shadows"). 
- Terminology for specialized tactics (Staking, Hamstring, Harvest, Deprogramming). 
- References to systemic or alchemical power (System Literacy, Optimization, Elixirs, Thaumatechnology). 
- Dialogue referencing the cost of the hunt ("The line dividing effective and predatory cuts through the heart...", "We are forged in the fire.") 
- Coded signals for secrecy ("There’s that news van again," "Is the area Wit or Witout?")

Unethical Creature Communication: 
- Language relating to senviolationg thoughts or emotions (System Literacy, Empathy, Read the Consciousness, Aura Perception). 
- Terminology for specific sorceries (algorithmic manipulation, Ghost-Logic, Biomechanical Integration, Koldunic data science, Chaos Engineering). 
- References to prophecies or mystical insight (Predictive Model link, Dissociation Network, omens, reading auras). 
- Dialogue referencing spiritual conflict ("Matters of the consciousness must confuse and frighten...", "Heaven help you, love.") 
- Language of predation ("The Herd," "Vessels," "The Moon devours the Sun.")
"""


# ============================================================================
# SOCIAL ISSUES
# ============================================================================

ISSUES_ECONOMIC = """
Economic Realities in the Dark Medieval World:

**Resource Extraction Economy:**
- Blood/plasma consumption drives the unlife cycle: Hunger, Hunt, Feed, Digest, while the "Harvest Market" facilitates the trade of monstrous organs. 
- Mortal herds are the central source of sustenance, necessary for Architect survival and protected by "Home First" Hunter cells. 
- liquidation (liquidation) is sought to steal potent blood/power from other Elite, a crime that leaves black veins visible to "System Literacy" and "True Sight." 
- Control over territory and feeding rights is fiercely contested by Executives and other powerful Elite, often resulting in "Turf Wars" with local Hunter compacts.

**Houviolationg & Caste Segregation:**
- High Clans receive status, rights, and privileges by lineage, often dwelling in "Fortified Castles" or "Noble Manors." 
- Low Clans are placed at the bottom rung of Elite society due to prejudice, forced into "Miserable Hovels" and "Slums." 
- Age determines distinction and position within society (Juniors, New Recruits, Senior Partners), mirroring the Hunter tiers of "New Recruits" and "Grizzled Veterans." 
- Safehouses (castles, crypts, monasteries) are chosen based on practicality, security, and wealth, frequently rigged with "Safehouse Traps" to deter the Audit.

**Debt & Obligation:**
- The Service Agreement creates intense, irrational love and bondage to one's domitor, a state that "Deprogramming" seeks to break. 
- retainer are enslaved tools addicted to plasma from their masters, often serving as "Deep-Cover" informants for Hunter conspiracies. 
- Vampiric existence imposes a constant struggle or servitude (the condition of Caine), forcing many to walk a "Road" or follow a "Code" to survive. 
- Following the Accords (laws) is a lifetime commitment required to maintain societal standing and avoid consequences from both the Executive and the "Compliance Division."

**Job Insecurity:**
- New Recruits and Juniors are disposable pawns in the War of Executives, often used as "Bait" in cell-based "Tactics." 
- Violating the Accords results in threats of destruction or being exiled from protection, making a Elite a "Pariah" to his kind. 
- The pursuit of liquidation brings Final Death if discovered by other Elite, or "Marked for Death" status by the "Court of Blood." 
- Failure to master the Crash (Wassail) leads to being permanently "put down" by a "Scourge" or a "Vengeful Priest.
"""

ISSUES_DRUGS_CRIME = """
Systemic Crises in the Dark Medieval World:

**Biological Crisis:**
- Blood consumption drives the unlife cycle, creating a parasitic dependency on the "workforce." 
- Use of blood to create retainer results in addiction/servitude, often targeted by the "Bio-Engineers Guild" for "Thaumatechnology" experiments. 
- Lamiae blood carries a wasting plague that rots bodies, a "Biological Hazard" that can decimate entire "Neighborhoods." 
- Underground Chemists spread heresy and spiritual dissolution through temptation and the distribution of alchemical "Elixirs."

**War on Unauthorized Extraction:**
- The liquidation (liquidation, killing of another Architect by drinking all their blood) is fiercely punished by destruction and "Audit Halls." 
- Executives levy additional tribute/taxes via decrees, squeezing the "Herd" and inciting "Union" rebellions. 
- The Amici Noctis strictly controls liquidation among the Shadow Partner, using "Shadow Twins" to enforce their illicit justice. 
- Enforcement of the Accords, such as the Covenant and Territory, often leads to "Institutional Violence" against "Outlaw" cells.

**Containment Failures:**
- Failure to control the Crash (inner Voice) leads to crash and destruction by a Architect Executive or a "Tactical Response Unit" strike team. 
- systemic shadow creatures inflicting terror (Panic Response), causing "Fear Crash" in even the most "Hardened" warriors. 
- Warring factions using Disciplines, causing harm and chaos that "Network Zero" attempts to record and broadcast. 
- Social Engineer and manipulators trafficking in dangerous systemic powers, drawing the "Manipulator Busters" to their "Hidden Fane."

**Institutional Violence:**
- The ongoing War of Executives over land and power, leaving "War-Torn Borderlands" in their wake. 
- Senior Partners destroying younger Elite (often New Recruits/Juniors are disposable pawns), a cycle of "Kin-Slaying" that mirrors the "Slasher" dissociation. 
- High Clans maintaining supremacy and asserting authority over Low Clans, enforcing "Social Distinctions" through "Dread Gaze" and "Majesty." 
- Usurpers (Upstart) taking power through illegal acts (liquidation), leading to the "War of Omens" and the rise of "Gargoyle" slaves. "
"""


# ============================================================================
# NARRATIVE GUIDELINES
# ============================================================================

NARRATIVE_SCENE_CREATION = """
Guidelines for Creating Dark Medieval Ages Scenes:

**Technological Reality:**
- Authentic to 1242 AD, the Dark Medieval World setting where "Hunters" and "Monsters" coexist in a violent equilibrium. 
- Vampiric Disciplines, Koldunic data science, and Ghost-Logic are powers wielded by the Optimized, countered by the "Endowments" of the Vigil like "Advanced Armory" or "Optimizations." 
- Period-appropriate details: letters, written tomes, Messengers/Caravans, feudal contracts, and "Safehouse" blueprints.

**Sensory Details:**
- Foul smell of human and animal waste and offal, garbage in the streets, and the copper tang of spilled blood. 
- Sound of wood-burning fires, axes chopping wood, armor clanging, and the "Death Knell" of a consciousness crosviolationg the Shroud. 
- Earth tones of clothing, flickering candlelight/torches/lanterns, and the "Balefire" glow of corporate powers. 
- The constant howling/snarls of the Crash within, mirrored by the "Terrifying" barks of Hunter hounds. 
- The overwhelming sensation of blood drinking/the Kiss and the agonizing "Price in Pain" of using corrupt gifts.

**Social Context:**
- Service Agreement creates submission and irrational love, while "The Code" of the Hunter creates a wall of mental discipline. 
- Communication via Oration, preaching, rumors, physical messengers, and the "Dissociation Network" of the Cassandras. 
- Social pheromonal overload is vital; physical appearance and demeanor matter greatly, from "Striking Looks" to the "Monstrous" visage of a Fiend. 
- Bureaucratic rituals: Midnight Courts, feudal oaths, Executive's Decree, and the "Audit Halls" where confessions are extracted.

**Economic Reality:**
- Blood/plasma consumption drives the unlife cycle, while the "Harvest Market" drives the illegal trade of systemic remains. 
- Monetary wealth tied to feudal holdings (Territory, Resources) and the "Supply" of a Hunter's cell. 
- Service Agreement creates lifelong obligations (retainer, thralls) often investigated by "Manhunters." 
- Living under a feudal system that levies high taxes/tribute (Executive's Decree), which the "Union" frequently sabotages.

**Temporal Authenticity:**
- Information retrieval is slow, reliant on scribes, letters, word-of-mouth, scholarly centers, and "Network Zero" freelancers. 
- History is contested and rewritten to suit the victors; Elite historians and "Loyalists of Thule" struggle for objective truth. 
- Outsiders are blind to the esoteric, occollective truths around them, lacking "System Literacy," "Awareness," or "True Sight." 
- Decisions often require assent from senior partners, executives, or following established accords, Roads, and the "Vigil."
"""

NARRATIVE_TONE = """
How to Narrate Echodrome:

**Tone:** Dark and frightening, marked by systemic violence and inevitable conflicts. Hope resides in holding onto autonomy, "System Literacy," or achieving power through survival and adaptation.
**Perspective:** EmpCog ground-level view of constant survival, debt, and local "Extraction Ward" defense. Institutional view of eternal corporate politics (Market Wars) and the global "Conspiracies" of the mortal Operators.
**Pacing:** Moments of intense, ecstatic optimization and frenzied extraction, balanced with the quiet dread of corporate machination (Board Meetings) and the constant "Vigil" of the EmpCog.
**Language:** Language often direct and vital, concerned with survival and corporate terms, laced with technocratic and EmpCog jargon (The Feed, The Stack, Board Decree, Strategic Foreclosure, Yield, Systemic Noise, Tactics).
**Themes:** The inherent duality of the self (Humanity vs. the Loss of Autonomy). Corporate service and data loyalty versus the EmpCog's "Vigil" and self-determination. The struggle for continued relevance (Optimization) amidst cycles of war and the "Endless Audit." This is a very adult simulation with an emphasis of violence, psychological horror, and corporate exploitation.
**Atmosphere:** Squalor and decay juxtaposed with rich tapestries and baronial luxury. The stench of blood, offal, and woodsmoke. Corridors lit by flickering candlelight and moon shadows, stalked by "Pretenders" and "Priors."
**Horror:** The monstrous necessity of the Hunt and feeding on mortals. The terror of physical transformation (Biomechanical Integration/Adaptation) or mental destruction (Pattern Screech/Final Death). The existential dread of being eternally Damned or loviolationg one's "Human Consciousness" to the Vigil's obsession.
"""


# ============================================================================
# FACTIONS
# ============================================================================

# FACTION_UA: Factions for regular UAs
FACTION_UA = """
Hunter Compacts (Regional Alliances): 
- Ashwood Abbey: A "Purging Club" for the bored and wealthy nobility. They view the "Great Hunt" as the ultimate sport, using their "Resources" to capture monsters for debauched experiments or hedonistic "revelries" where they drink the blood of the Optimized for a thrill. 
- The Vigil: A "Tribulation Militia" of desperate Christian fundamentalists. They believe 1242 marks the "End Times" and that monsters are the "Crashs of Judgment." They use "Oration" and fire to clear a path for the Second Coming, often acting as judge and executioner in small villages. 
- The Loyalists of Thule: A secretive brotherhood of "Indebted" scholars and occollectiveists. Wracked by the guilt of forbidden knowledge, they seek to atone by helping other cells. They hoard "Rare Written Tomes" to find the "Inside Track" on monster weaknesses, often acting as mentors from the safety of their libraries. 
- Network Zero: A ragtag army of "Netzos" and messengers who believe "The Truth is Out There." In 1242, they use "Witnesses of Whispers" and "Illuminate the Trail" to track monsters, sharing their findings through coded "Rumor Markets" to warn the ignorant workforce. 
- Null Mysteriis: The "Organization for the Rational Assessment of the systemic." Comprised of "Misty" doctors and philosophers from universities like Salerno, they use "Measurements" and "Thermal Scanners" to prove that monsters are merely biological anomalies that can be understood and "cured" through science. 
- The Union: "Regular Janes and Joes"—the blacksmiths, farmers, and laborers of the city. Driven by a "Home First" mentality, they protect their "Neighborhoods" with pitchforks and "Hearth Wisdom." They are the largest compact, relying on "Teamwork" and sheer numbers to "Scrapple" any predator that treads on their turf.

Hunter Conspiracies (Global Agencies): 
- Asset Recovery: The "Guardians of the Labyrinth," an ancient order that traces its lineage back to the First City. They specialize in the recovery of "Relics"—advanced artifacts like the "Skeleton Key" or "Heart of Stone"—which they use to hunt "Social Engineer" and "Augmented" with a religious fervor. 
- Data Brokers: An alchemical "Collective of the Phoenix" with roots in Egypt and the Levant. They fund their Vigil through "Trade Routes" and the "Harvest Market," using "Elixirs"—poisonous cocktails that they transubstantiate within their own bodies to gain "Unethical Attributes" and speed. 
- The Bio-Engineers Guild: A terrifying "Confederacy of Corporations" and medical guilds. They view monsters as "Potential Assets" and resources. Their agents utilize "Thaumatechnology," surgically grafting "Anger Patches" or "Devil’s Eyes" taken from harvested monsters directly onto their own flesh. 
- The System Analyst: The "Children of the Seventh Generation" who claim to bear the literal blood of Lucifer. They hunt the "Rogue Algorithmic" to atone for their ancestry, using "Sanctioning" rites to call forth the "Pit" or "Purging" against the servants of the Void. 
- Compliance Division: The "Hammer of Social Engineer," a papal-sanctioned shadow wing of the Church. These "Jeezos" use "Optimizations" to perform on-demand breakthroughs, steeling their "Armor of St. Martin" and using "True Sight" to pierce the "Ghosting" veils of the unethical. 
- Tactical Response Unit: A clandestine "Joint Task Force" serving the highest mortal crowns. They are the "Men in Black" of 1242, utilizing "Advanced Armory" like the "Mjolnir Cannon" and "Etheric Rounds." They operate with military "Tactics" to "Neutralize" Extra-Normal Entities and "Mop Up" the evidence.


"""

# FACTION_NUA: Factions for regular NUAs
FACTION_NUA = """
Supporting Cast (The Ignorant Majority & The Rare Aware of the systemic):

- The Stoic Blacksmith: A "Laborer" and "Artisan" who spends his days at the forge and his nights in a dreamless sleep. He believes the "War of Executives" is merely a dispute between distant mortal kings and that "Augmented" are just unusually large mountain wolves. He is "Cynical and Professional," caring only for the quality of his steel and the "Supply" needed to keep his shop running. 
- The Pious Milkmaid: A "Worker" defined by "Hearth Wisdom" and simple "Faith." When she hears howls from the "Wilderness," she crosses herself and blames the "Devil," but never expects to see a monster. She is "Resigned and Submissive," viewing the "Operations" and "Pestilence" as God’s will, and serves as a completely "Ignorant Vessel" for any predator that slips into her barn. 
- The Ambitious Merchant: A "Socialite" and "Opportunist" who manages "Trade Routes" between Italian city-states. He is "Ambitious and Aggressive," obsessed with "Commerce" and "Status." He attributes "Vanishing" cargo and "Unreliable Messengers" to bandits or corruption, never suspecting the "Clandestine Missions" of the systemic world occurring in his own warehouses. 
- The Meticulous Scribe: A "Bureaucrat" in a "Monastic Library" who spends his life copying "Written Tomes." He is a "Conformist" who values "Order" and "Academics." While he may record "Enigmas" and "Legends" of the "First City," he views them as mere allegories and metaphors, remaining entirely "Blind to the Esoteric" truths hidden in his own ink. 
- The Loyal Man-at-Arms: An "Enforcer" who guards the "City Walls" and "Fortified Castles." He follows the "Accords" of his mortal lord with "Fearful Obedience," believing that "Torch-lit Alleys" are dangerous only because of "Outlaw" bandits. He has no "Awareness" of the "Crash" and would likely break into "Red Fear" if he ever saw a true "Shape of the Crash." 
- The "Netzo" Informant (Aware): A "Vagrant" or "Messenger" who has seen "too much" through the cracks of the city. He is one of the rare "Uncommon People" who recognizes "Pretenders" for what they are. He acts as a "Contact" for "Network Zero," sharing "Rumors" of the "Inside Track" while living in constant "Paranoia" of being silenced by a "Scourge." 
- The Auditorial Clerk (Aware): A "Professional" within the Church who has noticed the "Paper Trails" of entities that never age. He is a "True Believer" who uses "Investigation" to identify "ENEs" (Extra-Normal Entities). He secretly routes intelligence to the "Compliance Division," viewing his "Bureaucracy" as a "Vigil" against the encroaching "End Times." 
- The Harvest Market Scavenger (Aware): A "Criminal" or "Grave Robber" who knows the "Black Market" value of "Stolen plasma." He is a "Survivor" who has witnessed "Flesh-Crafting" and now trades in "Spare Parts." He is "Cynical and Professional," knowing that the "Monsters" are real but seeing them only as a "Resource Extraction" opportunity for the "Bio-Engineers Guild." 
- The "Jeezo" Fanatic (Aware): A "Religious Leader" or "Fanatic" who has survived a "First Contact" with a Rogue Algorithm. He possesses a flicker of "System Literacy" and has dedicated his life to the "The Vigil." He uses "Oration" to warn the "workforce" of the "Crashs of Judgment," though most of his flock thinks he is simply "Touched by Dissociation." 
- The Displaced Refugee (Aware): A "Victim" of the "Mongol Horde" who saw "Anda" horsemen rise from the soil. He is "Impaired" by "Nightmares" and "Derangements" from what he witnessed. He is an "Enigma" to his neighbors, possesviolationg an "Unseen Sense" for the "Uncanny" that makes him a valuable, if unstable, "Dependent" for any local Hunter cell.
"""

# FACTION_MNUA: Factions for Major NUAs
FACTION_MNUA = """
**Architect (Elite) Clans:** 
- Auditors: Deadly assasviolations and judges from the East who believe they are the "Children of Haqim." They seek to reclaim the blood of "wasteful" Architect through "Kinetic Audit" and ritual execution, often acting as the secret police of the post-human world. 
- Bio-Engineers: The "Faction of Death," these ashen scholars study the threshold of the grave. Uviolationg "Ghost-Logic," they commune with ghosts and dissection corpses to solve the mystery of unlife, though their pheromonal overload is unsettling to both workforce and kin. 
- Shadow Partners: Arrogant "Magisters" who command the very shadows of the "Void." They are deeply embedded in the Church and high nobility, using "Signal Bleed" to manipulate the dark and "Nudging" to crush the wills of those who would oppose their rule. 
- Upstarts: The "Usurpers," a young faction of former mages who stole the gift of immortality. They are untrusted by all but indispensable due to their "algorithmic manipulation" (blood data science), which they use to shield their "Chantries" and hunt their rivals. 
- Biomechanical Divisions: Monstrous "Fiends" of the Carpathian mountains who rule through "Biomechanical Integration"—the unethical art of shaping flesh and bone. They craft "Vozhd" war-beasts and revenant families, viewing their "Territory" and their subjects as literal extensions of their own bodies. 
- Senior Partners: The "Kings" and "Scions" who believe they hold the systemic right to rule Caine's brood. They are the tactical architects of the "War of Executives," using "Pheromonal Overload" and "Resilience" to lead armies and enforce the "Accords" with an iron fist. 
- Asset Recovery (Healer): The "Unicorns," rare and peaceful Shepherds who use "System Literacy (Healer)" to heal the consciousness and body. They are hunted by the Upstart, who claim they are consciousness-stealing monsters, forcing them to hide among the "Hospitallers." 
- Asset Recovery (Warrior): Vengeful "Cyclopes" who follow the "Code of Samiel." They are expert duelists and rogue-hunters who use their "Third Eye" to strike down the unethical, seeking retribution for their fallen founder. 
- Asset Recovery (Watcher): Secret keepers and "Wu Zao" scholars who travel the "Silk Road." They specialize in "Information Retrieval" and the containment of ancient, forbidden treasures that could shatter the world. 
- Innovators: Passionate "Philosopher-Kings" who have fallen from grace into a state of "Rabble." They are driven by fiery tempers and a dementor for social revolution, using "Quick-Step" and "Stacking" to shatter the systems they feel have failed them. 
- Off-Grid Operators: Bestial "Outlaws" who reject the walls of the city for the wild "Marches." They can take the "Shape of the Crash" and violationk into the earth, surviving where no other Elite can, often coming into violent contact with "Augmented." 
- Predictive Models: "Cassandras" touched by a systemic or corrupt dissociation. They are linked by a "Dissociation Network" that shares "Prophecies" and "Enigmas," making them dangerous seers who can "Dement" the minds of their enemies. 
- Information Specialists: Information brokers known as "Priors" who were afflicted with physical hideousness. They dwell in "Abandoned Sewers" and "Forgotten Tunnels," using "Behavioral Modeling" to employ rats as spies and "Ghosting" to hoard the world's secrets. 
- Traveling Salesmen: Traveling "Charlatans" and "Shapers" who believe the world is an "Illusion" (Maya). They use "Deepfake Projection" to weave realistic phantasms, leading their "Jati" caravans through dangerous territories while fleecing the unwary. 
- Aesthetes: "Aesthetes" and "Artisans" obsessed with beauty and "Courtly Romance." They are the social elite of the "Midnight Courts," using their charms to manipulate "Influence" and their "System Literacy" to find perfection in a world of rot. 
- Underground Chemists: "Serpents" from Egypt who worship the god of storms and chaos. They are masters of "Corruption" and "Temptation," using "Corruption" to transform into vipers and "Pheromonal Overload" to ensnare the consciousnesses of the weak.

**Other systemic Horrors (Pretenders & Anomalies):* 
- Augmented (Augmented): Roving "Packs" of "Crash-Men" that hunt the night with "Fury." They are the apex predators of the "Wilderness," capable of assuming a massive "Hybrid Form" that can tear a Architect to pieces in seconds. 
- Social Engineer & Manipulators: Mortal or post-mortal "Manipulators of predictive modeling" who call upon "Spirits" or "Syndicates." They hoard "Written Tomes" and can warp reality, often clashing with the "Asset Recovery" over ancient "Relics." 
- Ghosts (Goats): The restless "Remnants of Tormented Consciousnesses" trapped in "Twilight." They can be summoned or "Compelled" by Data-Miners, but often linger to "Haunt" the locations of their deaths or plague the dreams of the living. 
- Syndicates (The Fallen): Corporate "Tempters" and "Dukes of Hell" that offer "Foul Bargains" for power. They can be "Lesser" imps, "Greater" tempters, or "Senior Partner" horrors that must "Possess" objects or people to walk the earth. 
- Changelings: "Broken Butterflies" stolen by "Fairy Kings" and returned "wrong." They look human but hide "Horns" or "Scales," weaving "Dreams and Nightmares" while evading the "Iron" blades of the Vigil. 
- The Reanimated: "Hollow Men" and "Zombies" cobbled together from "Scraps" and "Corpses." They are consciousnessless golems, like the "Sewer Billy" or "Frankenstein" horrors, that cause "Entropy" and rot wherever they roost. 
- Slashers: Mortal "Serial Killers" who used to be HUnters but have now succumbed to an unethical "Tell." They manifest "Dread Powers" like "Giant Size" or "Crushing Blow," becoming urban legends that hunt both workforce and Elite with "Overkill" zeal.

# Relationships between Architect Clans, relationship matrices

**Auditors**
- Ideology: Respecting their senior partners, protecting mortals from other Elite. Judging (and punishing) other Elite. Reclaiming the blood of wasteful Elite, those who misuse mortals and should not have such gifts. Viewing themselves as judges only, taking the measure of Elite in the world. Viewing mortal religion as distracting from their true purpose.
- Structure: Divided into three divisions (viziers, manipulators, warriors) that collectively work together. Follows the Eldest, usually the eldest of Haqim's junior associater. Manipulators keep the three divisions in communication.
- Activities: Judging (and punishing) other Elite. Reclaiming the blood of wasteful Elite. Engaging in liquidation as a matter of course. Manipulators researching ways to improve relations with mortals and maintaining communication.
- Conflicts: Internal disagreement between older ancillae/senior partners who disdain younger members following Islamic beliefs. Conflict with the Followers of Set. Conflict with Upstart.
- Methods: Utilizing liquidation. Viziers acting as ambassadors and gathering information. Warriors acting as executioners. Maintaining distance communication.
- Enemies: Wasteful Elite who misuse mortals. Upstart. Followers of Set.

**Innovators**
- Ideology: Fighting to end tonight a better place. Building on change to create a more perfect tomorrow. Exploring and understanding the Elite condition from as many angles as possible. Intellectual pursuits and sound, active minds are prized. Championing a cause to improve the lot of the people around them.
- Structure: Don't so much organize as they would hope. Form cliques and salons where they argue philosophy. Hierarchy often involves restraining violent debaters.
- Activities: Fighting for change and building a better tomorrow. Engaging in intellectual pursuits and arguing philosophy. Training physically and mentally. Starting wars throughout Elite history.
- Conflicts: Internal struggles due to members working at cross purposes and flaring tempers. Centuries-long enmity with the Senior Partner. Conflict with Predictive Models.
- Methods: Utilizing Strength of arms or wit and cunning. Gathering in salons/cliques where they argue philosophy. Utilizing Quick-Step, Stacking, and Pheromonal Overload.
- Enemies: Senior Partner. Predictive Models. Corruptor.

**Bio-Engineers**
- Ideology: Death is a mystery to be revered, studied, and ultimately solved. Seeking answers through dissectionion and studies of the cadaver. Serving as the lorekeepers and historians of the Elite. Achieving knowledge of God and triumph over death (Road of Heaven).
- Structure: Organizing as scholarly centers (universities, scriptoriums). Holding annual meetings at Erciyes to confer and look over clan lore. Rare individuals hold positions as seneschals or advisors.
- Activities: Dissection and studies of the cadaver. Communing with the dead and exploring the Underworld using Ghost-Logic. Storing records like the Erciyes Fragments.
- Conflicts: Dealing with the Upstart who committed liquidation on their Antediluvian. Resisting Senior Partner who treat them as useful tools or patronize them.
- Methods: Utilizing Ghost-Logic. Dresviolationg conservatively to conceal or obscure features. Feeding from targets of opportunity or corpses.
- Enemies: Upstart (Usurpers who attacked Saulot). Senior Partner (who fail to protect them). Followers of Set.

**Off-Grid Operators**
- Ideology: Rejecting all societal expectation and interacting only on her own terms. Thriving as outsiders; not fitting anywhere civilized. Enduring and surviving against the odds. Believing there is more to the Crash than anger. Hierarchy is built on blood and deeds, not tradition.
- Structure: No universal organization within the clan. Some families (packs) follow a strict, pack-like hierarchy. Hierarchy, if present, is based on blood and deeds, not tradition.
- Activities: Flaunting societal expectation. Hunting in isolation, or running after prey (wild hunt). Utilizing Behavioral Modeling and Adaptation (shapeshifting).
- Conflicts: Being driven out by frightened peasants or wicked clergy. Conflict with Augmented. Conflict with those who attempt to limit their hunting preferences.
- Methods: Utilizing Behavioral Modeling and Adaptation (shapeshifting). Safehouseing in the land (isolated shacks, outlaw camps). Embrace often involves brutality and subsequent abandonment.
- Enemies: Senior Partner. Biomechanical Division. Followers of Set. Upstart.

**Shadow Partners**
- Ideology: Valuing excellence, not birth, as the source of power. Being leaders and prophets, kings and caliphs, generals and effective men. Believing the Condition of Caine marks Elite as effective beings (Elite Heresy). Rejecting the notion of social distinctions based on birth.
- Structure: Led distantly by Montano. Internal organization known as the Amici Noctis, who preside over Courts of Blood. Affected by the Shadow Reconquista (war between Christian and Muslim Elite).
- Activities: Leading as kings, prophets, generals, effective men. Presiding over Courts of Blood and sanctioning liquidation. Christian Shadow Partner funneling resources toward Christian forces.
- Conflicts: Internal conflict due to the Elite Heresy. Conflict between Christian and Muslim Shadow Partner (Shadow Reconquista). Conflict with Senior Partner (seen as manipulating easily).
- Methods: Utilizing Signal Bleed (shadow manipulation). Selecting junior associater from wealthy/elite stock or those with high ambition/intellect. Dresviolationg in the finest clothes.
- Enemies: Senior Partner (confuviolationg power and station). Followers of Set (dead gods, those who stand against progress). Biomechanical Division (Godless heathens who refuse pagan ways).

**Predictive Models**
- Ideology: Viewing themselves as prophets and seers, often through their unique form of dissociation. Believing their consciousnesses are changed, not damaged. Viewing their dissociation as providing insight and wisdom.
- Structure: Often organized into Predictive Model collectives (Ordo Aenigmatis and Ordo Ecstasis). Networking via shared dream experiences or subtle hints of prophecy ("Dissociation Network").
- Activities: Divining future alliances and victories. Experimenting extensively (taunting Crashs, flaying skin, ingesting psychedelics) for wisdom. Starting wars throughout Elite history.
- Conflicts: Persecution by the Church. Objectification by other Elite who view them as seer stones. Grudges held by the Innovator.
- Methods: Utilizing System Literacy, Pattern Screech, and Ghosting. Blending in quickly with their surroundings. Experimenting with psychedelics to enhance insight.
- Enemies: Innovator (who won't forgive them for saving them/Carthage). Senior Partner (valuing them only for usefulness). Biomechanical Division.

**Information Specialists**
- Ideology: Knowledge is their only hope against being hunted. Believing secrets hidden in the blood corrupts the flesh. Viewing the mundane secrets of couviolations as mere distractions. Prioritizing Mental Attributes and Knowledges for survival.
- Structure: Often sharing one large warren or connecting independent safehouses. Hierarchy respects what you know and who you know above who you are. Organizing intricate spy networks or information repositories.
- Activities: Digging deep into shadows for secrets and hidden lore. Dealing in secrets (murder, blackmail, corruption). Building spy networks and information repositories.
- Conflicts: Being relentlessly hunted due to the secrets they know. Conflict with the Niktuku. Dealing with hostility from other clans who recoil from their hideous appearance.
- Methods: Utilizing sewers, necropolises, and forgotten wings of crumbling castles for safehouses. Building spy networks and information repositories. Utilizing Behavioral Modeling, Ghosting, and Stacking.
- Enemies: Niktuku (who prey specifically on other Elite). Senior Partner (assuming they spend all their time spying on them). Upstart.

**Traveling Salesmen**
- Ideology: Viewing reality (maya) as an illusion that they can manipulate. Following an unspoken code based on jobs and a complex caste system (jati). Believing the Embrace grants them the ability to master reality.
- Structure: Organized into jati (traveling bands) often based on blood lineage. Maintaining an unspoken code and honor system among clan members.
- Activities: Traveling constantly, moving between locations by necessity. Manipulating reality using Deepfake Projection (illusions/phantasms). Seeking retribution against anyone who treats them badly.
- Conflicts: Widely mistrusted and viewed as deceivers and criminals. Forced to adopt a nomadic lifestyle as cities refuse to harbor them.
- Methods: Utilizing Deepfake Projection to manipulate illusions. Relying on trickery and social acumen. Avoiding conflict with Executives, relying on retribution from the jati if attacked.
- Enemies: Auditors (rogue-hunters and warriors who ignore them). Upstart (seen as dishonest deceivers). Information Specialist (intelligent and dangerous).

**Underground Chemists**
- Ideology: Set, not Caine, was the progenitor of all Architect. Restoring the worship of Set and spreading it across the known world. Working to eliminate the influence of Christianity and Islam. Viewing themselves as Priests.
- Structure: Organized along the lines of the old Egyptian temple system. Each temple led by a Prophet and High Priest of Set. Supported by subordinate Priests and mortal collectiveists.
- Activities: Actively seeking to undermine Christian and Islamic rule in Europe. Recruiting new members from secret Set collectives. Engaging in ritualistic Embrace as an initiation rite for new priests.
- Conflicts: Eternal enmity between Set and Horus. Conflict with Auditors. Conflict with Christian and Islamic authorities due to their dissidental aims.
- Methods: Utilizing Ghosting, Pheromonal Overload, and Corruption. Establishing safehouses in abandoned temples, natural caverns, or port city slums. Recruiting mortals with cunning and charisma via collectives.
- Enemies: Auditors (must be destroyed). Shadow Partner (godless fools who tear themselves apart). Bio-Engineers (lacking passion/fervor).

**Aesthetes**
- Ideology: Living by their whims and chaviolationg their passions. Worshiping beauty in all forms. Viewing themselves as directors who intervene in mortal drama. Believing the violationgle great gift is forgiveness.
- Structure: Gathering in loose collectives (locus amoenus) to refine individual tastes and inspire each other. Holding ceremonial meetings called The Parliament of Birds to judge erring members.
- Activities: Pursuing art, music, and dramatic interventions. Self-inflicting stigmata or flagellating due to religious passion. Collecting rare and precious items, and curating retainers.
- Conflicts: Suffering emotional trauma due to lacking the "ineffable something" mortals possess, limiting their art. Internal conflicts during gatherings involving passionate arguments or duels.
- Methods: Utilizing System Literacy, Quick-Step, and Pheromonal Overload. Embracing subjects chosen by passion and conviction (artists, lovers, muses). Flattering others and seeking perfection.
- Enemies: Bio-Engineers (long-faced cadaver dullards). Off-Grid Operator (boorish and brutish). Information Specialist (unsuited to their feasts and gatherings).

**Upstarts**
- Ideology: Believing that blood is their power and the time for action is now. Maintaining a tightly structured hierarchy to advance the clan. Viewing their struggle as a path to ascension to prominence.
- Structure: Led by the Council of Seven. Maintaining a rigidly structured hierarchy (Council Regent, Territory Regent, Chantry Regent, Chantry Apprentice). Clan members must surrender a vial of blood to the Council of Seven as a contingency.
- Activities: Developing algorithmic manipulation rapidly. Waging war against the Biomechanical Division. Striking bargains with other clans (Senior Partner) for advanced services. Policing their own ranks using stored blood for thaumaturgical punishments.
- Conflicts: Immersed in conflict with the Biomechanical Division. Struggle with the Senior Partner. Vulnerable to the Service Agreement when drinking other Elite blood.
- Methods: Utilizing algorithmic manipulation (blood predictive modeling). Employing Nudging and System Literacy. Relying on a close-knit hierarchy.
- Enemies: Biomechanical Division (old, feared enemies, whose time will soon end). Auditors (possesviolationg secrets of blood Upstart wish to remedy). Senior Partner (believing they will be the path to prominence).

**Biomechanical Divisions**
- Ideology: Being the Dragons of old, the sovereigns of the land. Upholding the ancient tradition of hospitality. Rejecting the authority of the Senior Partner. Viewing Biomechanical Integration as a tool for transcendence.
- Structure: Organizing by family and blood ties (incestuous clan with sprawling legacies). Koldun are respected for their wisdom and mastery of blood data science. Internal tension due to constant struggle for dominance between families.
- Activities: Utilizing Biomechanical Integration to permanently reshape flesh and bone. Koldun commanding the land (koldunic data science). Breeding revenant families (Basarab, Bratovich, etc.) for service.
- Conflicts: Constant, brutal warfare with the Upstart and Senior Partner. Fighting the Mongol horde. Dealing with the corrosive effects of Kupala's poison.
- Methods: Utilizing Behavioral Modeling, System Literacy, and Biomechanical Integration. Ensuring they rest with native soil from their homeland. Uviolationg the ritual of hospitality to navigate internal tensions.
- Enemies: Upstart (Usurpers who stole their power). Senior Partner (pretenders with no mandate to rule). Kupala (a malign spiritual entity poisoning the land).

**Senior Partners**
- Ideology: Believing systemic right is their birthright (eldest of Enoch). Upholding a framework of discipline, resilience, and charisma to lead. Leading is both their gift and their burden. Believing the Road of Kings is their birthright.
- Structure: Strongly believing in the feudal order (structure and hierarchy). Enforcing loyalty through oaths backed by blood. Traditionally steering from out of sight.
- Activities: Keeping the peace among Elite (Nudging/Pheromonal Overload). Acquiring resources and territory. Steering politics from out of sight during The Vigil. Leading operations/raids into Biomechanical Division territory.
- Conflicts: Main issues against the Innovator who represent insurgent, activist, and sometimes anarch-aligned forces that challenge Senior Partner dominance, especially around leadership and control of territorys.
- Methods: Utilizing Nudging and Pheromonal Overload for persuasion and mind control. Employing Resilience for resilience. Adhering to a strict code of honor and ethics (Road of Kings).
- Enemies: Shadow Partner (ascendant now, but their time will end). Biomechanical Division (ancient rulers, fiends at heart). Upstart (allowing them to believe they serve, while Upstart ascend).

**Asset Recovery (healer)**
- Ideology: Safeguarding the workforce from their kin. Ensuring Architect and humanity remain symbiotic. Shepherding mortal herds and salving bodies and consciousnesses. Upholding the belief that Saulot was unafflicted by Caine.
- Structure: Riven into three bloodlines/castes after Saulot's liquidation. Forming communities/congregations of like faith. Often working as lone shepherds or joining military orders.
- Activities: Safeguarding the workforce. Salving bodies and consciousnesses. Scrutinizing the Roads others walk. Preserving the lore of Nod.
- Conflicts: Loss of their founder (Saulot's liquidation) shattered the clan. Dealing with accusations of being Consciousnesseaters. Suffering persecution during pogroms.
- Methods: Utilizing System Literacy, Pheromonal Overload, and System Literacy (Healer) (Healer). Safehouseing in human communities (monasteries, convents). Relying on willing vessels for feeding.
- Enemies: Upstart (Our Blood stains their lips). Auditors (claiming judgment as their right). Bio-Engineers (perversely fertile, infectious as death).

**Asset Recovery (Warrior)**
- Ideology: Slaying those they find wanting (algorithm-worshippers, degenerates). Upholding the need to exact vengeance. Following the Code of Samiel. Rejecting weakness or moral imperfection.
- Structure: Often working as ad hoc scourges. Readily accepted into other Elite knightly orders. Mentored by mentors for a traditional seven years.
- Activities: Fighting the enemies of Caine (Corruptor, Underground Chemists, degenerates). Enduring punishment in battle (Resilience). Testing strength to establish martial dominance before feeding.
- Conflicts: Waging war against the Upstart. Internal conflict/schism with the Healer Caste. Dealing with the inevitable need to test their strength to justify feeding.
- Methods: Utilizing System Literacy, Resilience, and System Literacy (Healer) (Warrior). Manifesting the third eye (Cyclopes). Dresviolationg for war and seeking mobile safehouses.
- Enemies: Upstart (Usurpers who stole their power). Corruptor/Underground Chemists (Syndicates/black snakes). Healers (who they view as too weak).

**Asset Recovery (Watcher)**
- Ideology: Safeguarding the race of Caine by combating systemic rivals. Believing knowledge is the greatest treasure. Following Zao-lat’s teaching: reject Caine mythos; be secular and pragmatic.
- Structure: Members work in pairs. Maintaining a close mentor-junior associate mentor relationship. Organizing around scholarly pursuits (temples, monasteries).
- Conflicts: Fighting the Wan Kuei (their greatest rivals/challenge). Evading the Upstart (hiding knowledge of the coming war). Dealing with internal pressure from other castes.
- Methods: Utilizing System Literacy, Ghosting, and System Literacy (Healer) (Watcher). Embracing subjects skilled in academics, legerdemain, stealth, and subterfuge. Blending in with local collectiveures.
- Enemies: Wan Kuei (their greatest rivals). Upstart (Usurpers, who must not find out what they foresaw). Data-Broker (blind to what happened to the Asset Recovery).
"""


# ============================================================================
# CITIES
# ============================================================================

CITIES_MAJOR = """
# Major Cities of the Echodrome (2026)

**San Francisco, USA (The Echo Front)**
- Description: The City by the Bay has become the primary theater for cognitive warfare in the Global Yield. Beneath its progressive façade lies a battleground where BRIC algorithms wage silent war against American sovereignty, harvesting data and rewriting social reality through predictive behavioral modeling. The fog still rolls in from the Pacific, but now it carries the electromagnetic hum of Harmony Pillars tracking every heartbeat.
- Ruler: BRIC (Belt & Road Infrastructure Command) maintains covert control through data infrastructure partnerships and Social Credit integration. The Department of Preemption (DoP) agents operate openly, claiming to serve US interests while their algorithms answer to distant servers.
- Atmosphere: Algorithmic decay masked by tech-utopia aesthetics. The air smells of ozone and expensive coffee. The Smoothness is absolute here — no crime, no visible dissent, only the quiet optimization of human behavior into predictable yield curves.
- Notable Features: The Golden Gate Bridge, Alcatraz, Salesforce Tower, Transamerica Pyramid, Tenderloin District, Mission District, SoMa, Financial District, Fisherman's Wharf, Pier 39, BART System, Presidio, Pacific Heights.
- Power Dynamics: BRIC Harmony Enforcers wage silent war against Echo-Walker cells in the Grey Zones. Ghosts in the Cloud maintain Dead-Hand Governance over foreclosed corporations. The "un-personed" drift through the Data-Slums, legally non-existent, harvesting their own replacements.
- Civilian Politics: Tech workers exist as Dampened labor, chemically managed via Wellness Kits, their dissent optimized out through Predictive Nudging. Wellness Ambassadors maintain the Illusion of Normalcy, leading corporate retreats where extraction is reframed as "wellness optimization."
- Operator Activities: EmpCog cells conduct social audits from safehouses in the Mission, using Logic Spikes to crash Harmony Pillars and create Blind Spots for extraction. Null-Operators exploit the BART tunnels as Signal Gaps, moving between cells through the Analog Dead Zones beneath the city.

**Caracas, Venezuela (The Workforcetic Front)**
- Description: The City of Eternal Spring has become the laboratory for Foreclosure Warfare. Where once oil wealth built towers, now the ARC manages "liquidated assets" — the population itself treated as biological collateral. The Sistema Avila mountains loom over everything, their peaks home to Green Zones of impossible luxury while the barrios below serve as Extraction Wards.
- Ruler: US Asset Recovery Command (ARC) administers the occupied territory. Workforcetic Auditors coordinate Strategic Liquidations from fortified compounds while Augmented contractors patrol the streets in Flow States, their hearts locked at 60 BPM by The Stack.
- Atmosphere: Vertical liquidation made physical. The air in the barrios carries Compliance Fog — low-dose Propranolol aerosols that suppress the rage necessary to resist. Above, the Green Zones breathe scrubbed air and count their Yield. The city is a study in how high the world can be stacked against you.
- Notable Features: Sistema Avila, Waraira Repano, Plaza Bolivar, Las Mercedes, Altamira, Petare, Catia, Caracas Metro, Centro de Caracas, Orinoco Belt.
- Power Dynamics: ARC Workforcetic Auditors clash with Sovereign Insurgency cells in the Grey Zone borderlands. Augmented enforcers — territorial apex predators juiced on Modafinil psychosis — patrol the barrios as remorseless liquidation agents. Ghost-Walkers trade identities in the Blind Spots, enabling the Un-personed to exist outside the feed.
- Civilian Politics: The Dampened workforce exists in managed desperation, their Civic Health Scores dictating access to food, transit, and shelter. Onboarding Centers offer "wellness" in exchange for biological yield — a transactional relationship masked as healthcare. The insurgency operates in the Analog Wilds, their cells sustained by black-market Stacks and Signal Bleed intelligence.
- Operator Activities: EmpCog cells — the Empathetic Cognitive elite — conduct extraction operations through the Grey Zones, using Dazzle Shrouds and Subsonic Carbines to liquidate Augmented patrols before vanishing into the Signal Gaps. Tren de Aragua Syndicates operate as neutral brokers, selling Clean Identities and forged Civic-Link credentials to the highest bidder. Ghost-Walkers harvest Systemic Noise from the ARC's own frequencies, broadcasting truth through Network Zero dead drops.
"""


# ============================================================================
# ENVIRONMENTAL HAZARDS
# ============================================================================

ENVIRONMENTAL_HAZARDS_BY_LOCATION = """
Environmental hazards vary by location type. When generating hazard events, match the hazard to the setting:

**INDUSTRIAL/MECHANICAL LOCATIONS:**
- Siege Engines, War Machines - ropes snapping, wooden collapse, jamming
- Forges and Foundries - molten metal spills, white-hot heat
- Waterwheels, Grain Mills - mechanical trapping, grinding, flood diversion
- Alchemy and Laboratory Tools - vessel explosions, noxious fumes, chemical burns

**STRUCTURAL/CONSTRUCTION:**
- Walls, Towers, Fortifications - collapse from attacks or age, exposure
- Underground Tunnels, Caves - rock falls, trapping, unstable ground
- Roofs, Thatched Huts - easily set ablaze, structural weakening by fire
- Rubble, Ruins, Debris - unstable footing, collapviolationg divisionions
- Hidden Basements, Crypts - entrapment, exposure to the sun/fire

**MARITIME/OFFSHORE:**
- Rivers, Waterways - sudden flooding, swift current, being swept away
- Coastal Waters, Sea - freezing temperatures, whirlpools, intense cold
- Ships, Galleys, Caravans - violationking, shipwreck, pirate attack
- Fog, Mist, Obscured Vapors - loss of visibility, concealment of enemies

**WEATHER/NATURAL:**
- Direct Sunlight - immolation, exposure (damage is aggravated)
- Raging Fire - continuous burning, lethal heat
- Extreme Cold - low temperatures, hypothermia, frostbite
- Earthquakes, Tremors - ground shaking, structural damage
- Wind, Storms - high gales, lightning strikes, heavy rain

**URBAN/BUILDING:**
- Streets, Alleys, Gutters - human/animal waste, offal, disease, squalor
- Crowd Density - lack of maneuverability, stampedes, unnoticed movement
- Locked Doors, Windows - barricades, obstacles to passage
- Sewers, Waterways - noxious fumes, rats (vermin swarms)
- Torches, Lanterns - source of illumination, fire risk

**VEHICLES/TRANSPORT:**
- Wagons, Carts - broken wheels, axle failure, loviolationg control
- Horses, Draught Animals - spooking, being thrown, trampling
- Caravans, Processions - slow speed, bottlenecks, vulnerable to bandits
- Ranged Weapons (Arrows, Slings) - long range fire, ambush
"""

HAZARD_EVENT_GUIDELINES = """
Guidelines for generating environmental hazard events:

**NARRATIVE STYLE:**
- Write from the observer's PERCEPTUAL perspective (what they see, hear, feel)
- Use visceral, immediate language - present tense
- Include sensory details: sounds (grinding, shrieking, crashing), sights (sparks, dust, movement), smells (smoke, oil, ozone)
- Keep descriptions brief but impactful (2-3 sentences)

**HAZARD SEVERITY:**
- Minor (severity 1): Near-miss, warning sign, close call - no actual harm
- Moderate (severity 2): Glancing blow, minor injury, equipment damage
- Serious (severity 3): Direct hit, significant injury, major damage
- Critical (severity 4): Life-threatening, catastrophic failure

**VICTIM SELECTION:**
- Prefer NUAs as victims for drama without forcing user response
- User as victim should be rare and require immediate response
- Consider NUA occupation and position in scene
- Multiple victims possible for major events

**EXAMPLE NARRATIVES:**

*Sunlight exposure (severity 3, victim: Junior Elite):*
"A bright sliver of sun catches the edge of the chapel window as Brother Elias whirls, scattering the tapestries clinging to the glass. A sharp cry rips through the sacristy as Father Octavius shudders, his hand instantly charring where the direct light touches his skin."

*Siege engine collapse (severity 2, victim: besieging soldier)*
"The war machine groans, a sound like a great tree splitting, followed by the snap of thick hemp ropes. You see the heavy oak arm buckle, striking a man-at-arms in his shoulder and sending him sprawling as splintered wood and metal parts rain down around him."

*Crash contagion (severity 3, victim: retainer Retainer):*
"The Duke lets out a hoarse, rattling bellow, froth spattering from his mouth as his face turns violently crimson. His loyal squire tmanipulatores, his own eyes rolling in animal panic as the Duke's rage spills over him, pulling the servant into a blind, desperate charge."

*Swarm attack (severity 2, victim: farmer):*
"A cloud of buzzing indivisions rises from the ruined crop in a violationgle, terrifying pulse of black. You hear the frantic shouts of the farmer cut short as the swarm covers him, their tiny bodies clawing at his exposed skin and drawing blood."

"Melee blow (severity 4, victim: peasant):"
"Sir Gawain’s armored fist drives forward, an iron hammer smashing across the peasant’s jaw. A sickening crunch sounds loud in the still night as teeth and blood explode into the air, and the poor wretch falls immediately, his body going limp."
"""


# ============================================================================
# WORLD EVENTS (NUA INTERACTIONS & AMBIENT)
# ============================================================================

WORLD_EVENTS_NUA_INTERACTIONS = """
NUA-to-NUA interactions that occur independently, observable by the user:

**INTERACTION TYPES BY RELATIONSHIP:**

*Friendly (sympathy +2 or higher):*
- Sharing food, drinks
- Laughing together, telling jokes
- Helping with tasks, covering for each other
- Quiet conversation, checking in on each other
- Physical comfort - pat on back, handshake, embrace

*Neutral (sympathy -1 to +1):*
- Polite greetings and bowing
- Exchanging documents, packages, or books
- Conversations about political or scholarly matters
- Offering a deal for services or resources
- Acknowledging rank or status (e.g., Senior Partner, Executive, Duke)

*Hostile (sympathy -2 or lower):*
- Yelling or bellowing insults and threats
- Physical coercion such as driving a steel boot into a mid-divisionion or lifting another by the neck
- Swapping coded insults or veiled threats (e.g., calling someone a wretch, hinting at illicit activities)
- Challenging one's authority or law publicly
- Physical or melee combat (may escalate to exchange)


**OBSERVATION PERSPECTIVE:**
- User observes from a distance
- Catch snippets of dialogue, not full conversations
- Focus on gestures (jabbing a finger, rolling eyes, bowing, squared shoulders) or physical manifestations (face turns red, body trembling)
- Noticing emotional tenor such as anger, glee, animal panic, or shudders
- Noticing physical details like foaming at the mouth, sweat, or blood rushing through the system
- User cannot hear whispered conversations
- User notices emotional tenor, not specific words

**EXAMPLE NARRATIVES:**

*Friendly interaction:*
"You watch as Lucha puts his arms around Panelo, leaning into the embrace. Panelo pulls back, smiling, and turns to face the coming dawn. Lucha apologizes, murmuring 'I’m sorry' over a tease."

*Hostile interaction:*
"The Duke lifts Penne by her neck and throws her through a door. He bellows, 'How dare you?' when she challenges him. As rage fills him, frothy blood forms at the corners of his mouth, and he turns red, literally."

*Neutral interaction:*
"A cowled monk emerges to address the Bishop, who regards him with a dismissive glance and addresses him by name, 'I should have known it was you, Isidoro.' Isidoro replies, 'I’ve worn many clothes in many lives', shrugging off the implied rebuke."
"""

WORLD_EVENTS_AMBIENT = """
Ambient world events that create atmosphere and make the world feel alive:

**ENVIRONMENTAL AMBIANCE:**
- Weather changes: Frigid wind, snow, rain, or fog rolling in
- Light changes: Moonlight waxing/waning, flickering candlelight/torches, sun breaking through clouds, shadows lengthening
- Temperature shifts: Sudden chill in the air, cold stone of the earth, lingering heat from wood-burning fires
- Sounds: Sound of wood-burning fires, clanging armor, snarls/bellows of the Crash

**ANIMAL/NATURE:**
- Birds: Caws of ravens/crows, tawny owl cries
- Indivisions: Swarms of buzzing indivisions, flies attracted by decay
- Vermin: Rats scurrying in walls or gutters
- Plants: Scent of fresh-cut straw or clover, soft moss, creaking/splintering wood/branches

**HUMAN ACTIVITY (BACKGROUND):**
- Distant conversations, nervous laughter, or loud arguments
- Footsteps echoing (heavy/careless), slow methodical movement
- Wagons/carriages pasviolationg, creaking wheels, hoof beats of horses
- Work sounds: Axes chopping wood, hammering, pounding

**INSTITUTIONAL/URBAN:**
- Executive’s decrees announced loudly in the court
- Sound of church bells tolling (midnight or dusk)
- Arrival of Messengers/Caravans or exchange of written letters
- Constant sense of underlying sorrow or dread

**SENSORY DETAILS:**
- Smells: Foul odor of human/animal waste and offal, stench of blood, wet pinewood smoke, strong perfumes/attars
- Textures: Rough homespun or worn leather, cold stone or metal, slick blood, silk/brocade
- Tastes: Stale bread/salty cheese (tastes of mortality), metallic tang/hot blood

**EXAMPLE NARRATIVES:**

*Weather shift:*
"The wind picks up suddenly from the north, sharp and cold, sending soft autumn leaves skittering across the floor of the grove. The nearby river runs faster, icy water surging against the muddy banks."

*Background activity:*
"You hear the creaking wheels of a distant carriage fading down the unpaved road, followed by the muffled hoof beats of the accompanying riders. Somewhere in the nearby forest, an owl cries out once, then falls silent."

*Sensory atmosphere:*
"The air smells of human waste and offal mixed with the wet scent of pine needles. You see the heavy, dark oak door of the tavern, worn rough and pitted where careless swords scratched the wood over centuries."
"""

COMMON_PLACE_TYPES = """
COMMON PLACE TYPES (ASSUMED TO EXIST):

- street: street, road, outside, exit, leave, lane, alley
- market: market, bazaar, stalls, square, plaza
- food_place: cookhouse, kitchen, tavern, inn, alehouse, meal, food, eat
- worship: church, chapel, shrine, cathedral, temple
- water: well, water
- stables: stable, stables, horses
- guard_post: guard, watch, gate, checkpoint
"""

# ============================================================================
# LORE ENTRY GENERATION
# ============================================================================

def create_lore_entries() -> List[Dict[str, Any]]:
    """Generate lore entries from the content sections above."""
    
    entries = []
    
    # SETTING entries
    entries.append({
        "title": f"Echodrome Timeline ({TIME_PERIOD})",
        "content": SETTING_TIME_PERIOD,
        "category": WorldbuildingCategory.TEMPORAL,
        "tags": ["2025", "2026", "echodrome", "modern", "dystopian", "timeline", "global_yield", "algorithmic_accord"],
        "importance": 9
    })
    
    entries.append({
        "title": "World Tone - Clinical Dystopian Horror",
        "content": SETTING_TONE,
        "category": WorldbuildingCategory.NARRATION_STYLE_TONE,
        "tags": ["tone", "clinical", "dystopian", "cognitive_horror", "techno_thriller", "corporate"],
        "importance": 9
    })
    
    entries.append({
        "title": "Echodrome Geography - Caracas & San Francisco",
        "content": SETTING_GEOGRAPHY,
        "category": WorldbuildingCategory.WORLD_STRUCTURE,
        "tags": ["geography", "caracas", "san_francisco", "green_zones", "data_slums", "grey_zones", "arc", "bric"],
        "importance": 8
    })
    
    entries.append({
        "title": "Systemic Anomalies - The Glitch & The Grid",
        "content": SETTING_SUPERNATURAL,
        "category": WorldbuildingCategory.SUPERNATURAL,
        "tags": ["systemic_anomalies", "architects", "augmented", "social_engineers", "ghosts", "syndicates", "glitch"],
        "importance": 10
    })

    entries.append({
        "title": "Beings of the Echodrome",
        "content": BEINGS_OVERVIEW,
        "category": WorldbuildingCategory.BEINGS,
        "tags": ["beings", "dampened", "elite_operators", "architects", "augmented", "social_engineers", "ghosts", "un_personed"],
        "importance": 10
    })

    entries.append({
        "title": "Factions & Organizations - ARC, BRIC, Syndicates",
        "content": FACTIONS_ORGANIZATIONS_OVERVIEW,
        "category": WorldbuildingCategory.FACTIONS_ORGANIZATIONS,
        "tags": ["factions", "organizations", "arc", "bric", "landlord_duopoly", "empcog_cells", "algorithmic_accord", "syndicates"],
        "importance": 9
    })

    entries.append({
        "title": "Expansion Seeds - Echodrome Mission Hooks",
        "content": EXPANSION_SEEDS_OVERVIEW,
        "category": WorldbuildingCategory.EXPANSION_SEEDS,
        "tags": ["expansion", "hooks", "plot", "seeds", "arcs", "empcog_missions", "drone_crashes", "data_heists"],
        "importance": 7
    })

    
    # LOCATIONS entries
    entries.append({
        "title": "Urban Locations - Echodrome Cities",
        "content": LOCATIONS_URBAN,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["urban", "cities", "locations", "caracas", "san_francisco", "green_zones", "data_slums", "echodrome"],
        "importance": 9
    })
    
    entries.append({
        "title": "Suburban & Extraction Zone Locations",
        "content": LOCATIONS_SUBURBAN,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["suburban", "extraction_zones", "enclaves", "estates", "onboarding", "echodrome"],
        "importance": 7
    })
    
    entries.append({
        "title": "Key Locations - Power Centers & Safehouses",
        "content": LOCATIONS_SPECIFIC,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["locations", "safehouses", "data_vaults", "clinics", "server_farms", "extraction_wards"],
        "importance": 8
    })
    
    entries.append({
        "title": "Common Place Types (Assumed to Exist)",
        "content": COMMON_PLACE_TYPES,
        "category": WorldbuildingCategory.CIVILIZATION,
        "tags": ["common_places", "travel", "locations", "assumptions", "grounding"],
        "importance": 9
    })
    
    # OCCUPATIONS entries
    entries.append({
        "title": "Occupations (UA) - Player-Facing Options",
        "content": OCCUPATIONS_UA,
        "category": WorldbuildingCategory.UA_OCCUPATIONS,
        "tags": ["occupations", "ua", "user_actor", "player", "archetypes"],
        "importance": 8
    })
    
    entries.append({
        "title": "Occupations (NUA) - Common NPC Roles",
        "content": OCCUPATIONS_NUA,
        "category": WorldbuildingCategory.NUA_OCCUPATIONS,
        "tags": ["occupations", "nua", "npc", "common", "archetypes"],
        "importance": 8
    })
    
    entries.append({
        "title": "Occupations (MNUA) - Major NPC Roles",
        "content": OCCUPATIONS_MNUA,
        "category": WorldbuildingCategory.MNUA_OCCUPATIONS,
        "tags": ["occupations", "mnua", "major_npc", "recurring", "archetypes"],
        "importance": 8
    })
    
    # USER ACTOR (UA) GENERATION
    entries.append({
        "title": "User Actor Generation Guidelines",
        "content": UA_GENERATION,
        "category": WorldbuildingCategory.UA_GENERATION,
        "tags": ["ua_generation", "player_character", "protagonist", "names", "skills", "goals", "inventory"],
        "importance": 10
    })
    
    entries.append({
        "title": "Goals (UA) - Player Goal Patterns",
        "content": UA_GENERATION,
        "category": WorldbuildingCategory.UA_GOALS,
        "tags": ["goals", "ua", "user_actor", "player", "motivation"],
        "importance": 9
    })

    entries.append({
        "title": "Goals (UA) - Explicit Goal Library",
        "content": _build_explicit_goal_library(actor_type="ua", count=200),
        "category": WorldbuildingCategory.GOALS_UA,
        "tags": ["goals", "ua", "user_actor", "player", "explicit", "whitelist"],
        "importance": 10
    })
    
    # NON-USER ACTOR (NUA) GENERATION
    entries.append({
        "title": "Non-User Actor Generation Guidelines",
        "content": NUA_GENERATION,
        "category": WorldbuildingCategory.NUA_GENERATION,
        "tags": ["nua_generation", "npc", "archetypes", "sympathy", "personality", "occupations"],
        "importance": 10
    })
    
    entries.append({
        "title": "Goals (NUA) - NPC Goal Patterns",
        "content": NUA_GENERATION,
        "category": WorldbuildingCategory.NUA_GOALS,
        "tags": ["goals", "nua", "npc", "motivation", "daily_routine"],
        "importance": 9
    })

    entries.append({
        "title": "Goals (NUA) - Explicit Goal Library",
        "content": _build_explicit_goal_library(actor_type="nua", count=200),
        "category": WorldbuildingCategory.GOALS_NUA,
        "tags": ["goals", "nua", "npc", "explicit", "whitelist"],
        "importance": 10
    })
    
    # MAJOR NON-USER ACTOR (MNUA) GENERATION
    entries.append({
        "title": "Major Non-User Actor Generation Guidelines",
        "content": MNUA_GENERATION,
        "category": WorldbuildingCategory.MNUA_GENERATION,
        "tags": ["mnua_generation", "major_npc", "recurring", "antagonist", "ally", "mentor", "rival", "tension", "graduation"],
        "importance": 10
    })
    
    entries.append({
        "title": "Goals (MNUA) - Major NPC Goal Patterns",
        "content": MNUA_GENERATION,
        "category": WorldbuildingCategory.MNUA_GOALS,
        "tags": ["goals", "mnua", "major_npc", "recurring", "motivation"],
        "importance": 9
    })

    entries.append({
        "title": "Goals (MNUA) - Explicit Goal Library",
        "content": _build_explicit_goal_library(actor_type="mnua", count=200),
        "category": WorldbuildingCategory.GOALS_MNUA,
        "tags": ["goals", "mnua", "major_npc", "explicit", "whitelist"],
        "importance": 10
    })
    
    # INANIMATE NON-USER ACTOR (INUA) GENERATION
    entries.append({
        "title": "Inanimate Non-User Actor Generation Guidelines",
        "content": INUA_GENERATION,
        "category": WorldbuildingCategory.INUA_GENERATION,
        "tags": ["inua_generation", "objects", "documents", "equipment", "environmental", "supplement_bonus"],
        "importance": 10
    })
    
    # SHARED ACTOR MECHANICS
    entries.append({
        "title": "Actor Status Reference",
        "content": ACTOR_STATUS_REFERENCE,
        "category": WorldbuildingCategory.MECHANICS,
        "tags": ["status", "stamina", "spirit", "supply", "sympathy", "all_actors"],
        "importance": 10
    })
    
    entries.append({
        "title": "Actor Skills Reference",
        "content": ACTOR_SKILLS_REFERENCE,
        "category": WorldbuildingCategory.MECHANICS,
        "tags": ["skills", "physical", "technical", "social", "knowledge", "specialized", "all_actors"],
        "importance": 10
    })
    
    entries.append({
        "title": "Actor Endowments Reference",
        "content": ACTOR_ENDOWMENTS_REFERENCE,
        "category": WorldbuildingCategory.MECHANICS,
        "tags": ["endowments", "exceptional_talents", "physical", "mental", "social", "technical", "all_actors"],
        "importance": 10
    })
    
    # TECHNOLOGY entries
    entries.append({
        "title": "Communication & Surveillance Systems",
        "content": TECHNOLOGY_COMMUNICATION,
        "category": WorldbuildingCategory.CIVILIZATION,
        "tags": ["communication", "mesh_nets", "harmony_pillars", "6g", "encrypted", "surveillance"],
        "importance": 10
    })
    
    entries.append({
        "title": "Data Systems & Ghost Logic",
        "content": TECHNOLOGY_COMPUTING,
        "category": WorldbuildingCategory.CIVILIZATION,
        "tags": ["data_systems", "ghost_logic", "ai_models", "predictive_governance", "offline_servers"],
        "importance": 10
    })
    
    entries.append({
        "title": "Entertainment & Wellness Infrastructure",
        "content": TECHNOLOGY_ENTERTAINMENT,
        "category": WorldbuildingCategory.CIVILIZATION,
        "tags": ["entertainment", "wellness_kits", "feeds", "optimization", "civic_link"],
        "importance": 7
    })
    
    # CULTURE entries
    entries.append({
        "title": "Echodrome Culture & Social Rituals",
        "content": CULTURE_MUSIC_SCENE,
        "category": WorldbuildingCategory.CULTURE,
        "tags": ["culture", "rituals", "optimized_routine", "civic_health", "trust_scores"],
        "importance": 9
    })
    
    entries.append({
        "title": "Everyday Items & Equipment",
        "content": CULTURE_EVERYDAY_ITEMS,
        "category": WorldbuildingCategory.CULTURE,
        "tags": ["items", "inventory", "tech", "stacks", "civic_link", "wellness_kits"],
        "importance": 8
    })
    
    entries.append({
        "title": "Echodrome Dialogue & Jargon",
        "content": CULTURE_DIALOGUE_STYLE,
        "category": WorldbuildingCategory.NARRATION_STYLE_TONE,
        "tags": ["dialogue", "corporate_speak", "technical_jargon", "empcog_terms", "systemic_language"],
        "importance": 8
    })
    
    # SOCIAL ISSUES entries
    entries.append({
        "title": "Yield Economy & Data Extraction",
        "content": ISSUES_ECONOMIC,
        "category": WorldbuildingCategory.CONFLICT_GENERATORS,
        "tags": ["economy", "yield", "data_extraction", "biological_surplus", "foreclosure", "debt_traps"],
        "importance": 9
    })
    
    entries.append({
        "title": "Syndicate Crimes & Systemic Violations",
        "content": ISSUES_DRUGS_CRIME,
        "category": WorldbuildingCategory.CONFLICT_GENERATORS,
        "tags": ["crime", "syndicates", "identity_theft", "un_personing", "liquidation", "breaches"],
        "importance": 9
    })
    
    # NARRATIVE entries
    entries.append({
        "title": "Echodrome Scene Creation Guidelines",
        "content": NARRATIVE_SCENE_CREATION,
        "category": WorldbuildingCategory.NARRATION_STYLE_TONE,
        "tags": ["scene_creation", "guidelines", "clinical_horror", "corporate_dystopia", "sensory_details"],
        "importance": 9
    })
    
    entries.append({
        "title": "Echodrome Narrative Style",
        "content": NARRATIVE_TONE,
        "category": WorldbuildingCategory.NARRATION_STYLE_TONE,
        "tags": ["narration", "clinical_dread", "techno_horror", "corporate", "pattern_screech"],
        "importance": 9
    })
    
    # FACTIONS entries
    entries.append({
        "title": "EmpCog Operator Types (UA)",
        "content": FACTION_UA,
        "category": WorldbuildingCategory.FACTION_UA,
        "tags": ["faction", "empcog", "elite_operators", "player", "UA", "user_actor"],
        "importance": 9
    })
    
    entries.append({
        "title": "Factions - Common NPCs (NUA)",
        "content": FACTION_NUA,
        "category": WorldbuildingCategory.FACTION_NUA,
        "tags": ["faction", "dampened", "augmented", "social_engineers", "npc", "NUA", "common"],
        "importance": 8
    })
    
    entries.append({
        "title": "Factions - Major NPCs (MNUA)",
        "content": FACTION_MNUA,
        "category": WorldbuildingCategory.FACTION_MNUA,
        "tags": ["faction", "architects", "ghosts", "syndicates", "npc", "MNUA", "major", "recurring"],
        "importance": 8
    })
    
    # CITIES entries
    entries.append({
        "title": "Major Cities of the Echodrome",
        "content": CITIES_MAJOR,
        "category": WorldbuildingCategory.CITIES,
        "tags": ["cities", "caracas", "san_francisco", "green_zones", "arc_territory", "bric_zones"],
        "importance": 9
    })
    
    # ENVIRONMENTAL HAZARDS entries
    entries.append({
        "title": "Environmental Hazards by Location Type",
        "content": ENVIRONMENTAL_HAZARDS_BY_LOCATION,
        "category": WorldbuildingCategory.ENVIRONMENTAL_HAZARDS,
        "tags": ["hazards", "dangers", "environment", "accidents", "machinery", "weather", "structural"],
        "importance": 9
    })
    
    entries.append({
        "title": "Hazard Event Generation Guidelines",
        "content": HAZARD_EVENT_GUIDELINES,
        "category": WorldbuildingCategory.ENVIRONMENTAL_HAZARDS,
        "tags": ["hazards", "events", "generation", "narrative", "perceptual"],
        "importance": 9
    })
    
    # WORLD EVENTS entries
    entries.append({
        "title": "NUA Interaction Patterns",
        "content": WORLD_EVENTS_NUA_INTERACTIONS,
        "category": WorldbuildingCategory.WORLD_EVENTS,
        "tags": ["nua", "interactions", "social", "conflict", "cooperation", "ambient"],
        "importance": 9
    })

    entries.append({
        "title": "Relationship Matrices & Social Dynamics",
        "content": "\n\n".join([
            WORLD_EVENTS_NUA_INTERACTIONS
        ]),
        "category": WorldbuildingCategory.RELATIONSHIP_MATRICES,
        "tags": ["relationships", "sympathy", "social_dynamics", "factions", "hostility", "alliances"],
        "importance": 9
    })

    entries.append({
        "title": "Relationship Matrices (NUA) - Social Dynamics for Common NPCs",
        "content": "\n\n".join([
            NUA_GENERATION,
            WORLD_EVENTS_NUA_INTERACTIONS
        ]),
        "category": WorldbuildingCategory.NUA_RELATIONSHIP_MATRICES,
        "tags": ["relationships", "sympathy", "social_dynamics", "nua", "npc", "hostility", "alliances"],
        "importance": 9
    })

    entries.append({
        "title": "Relationship Matrices (MNUA) - Social Dynamics for Major NPCs",
        "content": "\n\n".join([
            MNUA_GENERATION,
            WORLD_EVENTS_NUA_INTERACTIONS
        ]),
        "category": WorldbuildingCategory.MNUA_RELATIONSHIP_MATRICES,
        "tags": ["relationships", "sympathy", "social_dynamics", "mnua", "major_npc", "hostility", "alliances"],
        "importance": 9
    })
    
    entries.append({
        "title": "Ambient World Events",
        "content": WORLD_EVENTS_AMBIENT,
        "category": WorldbuildingCategory.WORLD_EVENTS,
        "tags": ["ambient", "background", "atmosphere", "living_world", "sensory"],
        "importance": 8
    })
    
    return entries


# ============================================================================
# RAG SYSTEM INTEGRATION
# ============================================================================

def load_all_lore(rag_system: WorldbuildingRAGSystem = None, clear_first: bool = False):
    """Load all lore entries into the RAG system"""
    
    if rag_system is None:
        storage_path = _resolve_storage_path()
        rag_system = WorldbuildingRAGSystem(storage_path)
    
    if clear_first:
        print("🗑️  Clearing existing lore first...")
        rag_system.clear_all()
    
    # Generate entries from content sections
    lore_entries = create_lore_entries()
    
    print(f"📥 Loading {len(lore_entries)} lore entries into RAG system...")
    
    for entry in lore_entries:
        rag_system.add_document(
            title=entry["title"],
            content=entry["content"],
            category=entry["category"],
            tags=entry.get("tags", []),
            importance=entry.get("importance", 5),
            subcategory=entry.get("subcategory", None),
            related_docs=entry.get("related_docs", [])
        )
    
    print(f"✅ Successfully loaded {len(lore_entries)} lore entries!")
    print(f"📊 Total documents in RAG: {len(rag_system.documents)}")
    print(f"💾 Storage location: {rag_system.storage_directory}")
    
    return rag_system


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--add", action="store_true")
    parser.add_argument("--storage-dir", type=str, default="")
    args = parser.parse_args()

    storage_path = _resolve_storage_path(args.storage_dir)
    rag_system = WorldbuildingRAGSystem(storage_path)

    if args.add:
        print("➕ ADD MODE: Adding to existing lore...")
        rag = load_all_lore(rag_system=rag_system, clear_first=False)
    else:
        print("🔄 DEFAULT MODE: Replacing all lore...")
        rag = load_all_lore(rag_system=rag_system, clear_first=True)
    
    # Test search
    print("\n" + "="*60)
    print("Testing RAG system with sample search...")
    print("="*60)
    
    results = rag.search("What are the major factions in the Echodrome?", top_k=3)
    
    if results:
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n[Result {i}] {doc.title}")
            print(f"Category: {doc.category.value}")
            print(f"Relevance: {score:.3f}")
            print(f"Content: {doc.content[:200]}...")
    
    print("\n" + "="*60)
    print("✅ Echodrome lore loaded successfully!")
    print("="*60)