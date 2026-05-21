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
            "in a ruined castle",
            "along a torch-lit trade road",
            "inside a plague ward",
            "beneath a ruined chapel",
            "in the market hall",
            "at the city gate",
            "in a flooded cellar",
            "near the river docks",
            "under watchful eyes",
            "in the dead of night",
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
TIME_PERIOD_START_YEAR = 1242
TIME_PERIOD_END_YEAR = 1250
TIME_PERIOD = f"The Dark Medieval World, {TIME_PERIOD_START_YEAR}-{TIME_PERIOD_END_YEAR}"

# ============================================================================
# SETTING
# ============================================================================

SETTING_TIME_PERIOD = f"""
TIME PERIOD: {TIME_PERIOD}

This simulation takes place within the {TIME_PERIOD} era—a Dark Medieval reality of blood and fire. It is an age of unyielding strife where Caine's brood wages the War of Princes, a global struggle for "Domain" that treats the mortal "Kine" as mere resources. Kingdoms rise and fall under the shadow of the Crusades, while the great mortal populations exist under the constant fear of famine, pestilence, and the nocturnal horrors that stalk the night.
Beneath this "Midnight Court" of vampires, the world is infested with "Pretenders": "Lupines" who guard the untamed wild with savage "Fury," "Witches" who warp reality from "Hidden Fanes," and "Demons" from the "Abyss" who offer "Foul Bargains" to the desperate. Yet, the heart of this simulation is the "Vigil"—the desperate stand of humanity. It endures, bolstered by powerful Hunters—bands of mortals blessed with divine zeal, ancient lore, or unyielding vigilance—who rise as bulwarks against the endless dark.
The UA is a "Hunter," a human mortal whose eyes have been ripped open to the "Uncanny." Whether they are a "Union" laborer protecting your "Neighborhood" with "Hearth Wisdom" or a "Task Force: VALKYRIE" agent wielding "Advanced Armory," they carry the "Candle" against an endless night. These Hunters, often drawn from inquisitors, hermits, knights, and folk seers, form vigilant cells that wield silver blades, holy relics, and forbidden rites to stalk and slay the monstrous, their compacts echoing the endless Vigil against shadows. 

Travel is perilous, not only from bandits and beasts but from Hunter 

Physical life is crude, defined by the "Pestilence" and the "Crusades." Communication relies on "Unreliable Messengers" and dusty "Trade Routes," making "Rare Written Tomes" and "Noddist Lore" more precious than gold. 
The most advanced sciences are the "Endowments" of the "Conspiracies"—"Thaumatechnology" grafts, alchemical "Elixirs," and "Benediction" miracles—often mistaken for witchcraft by a "Naive World" that clings to "True Faith" to stave off the "Red Fear." These abilities are often mistaken for simple witchcraft by fearful peasants and zealous Hunters who burn tomes and their bearers alike. 
Travel is a "Perilous Journey" where "Ambushes" by "Outlaws" or "ENEs" (Extra-Normal Entities) are a constant threat to one's health and sanity. Ambushes along pilgrim trails and trade routes, make wealth and knowledge rare and precious, hoarded by those with the wit to obtain and protect it from both Beast and blade.

Culturally, it is an age defined by the endless cycle of Hunger and grim survival. Mortals cling desperately to Faith, constantly fearing the unknown evil lurking outside their homes after dark—ghouls devouring the unwary, werewolves howling in shadowed woods, witches weaving curses in forgotten glens, and vampires slipping through the night like silent reapers. 


Among the Damned, existence is maintained through rigid adherence to the Traditions and adherence to Roads of Enlightenment, philosophical paths meant to stave off degeneration. 
Survival and mastery are the only true currency in the eternal night, bartered amid skirmishes with Hunters whose compacts and conspiracies mirror the Vigil's unyielding light against the dark.

**Timeline Context: The War of Princes rages in 1242, clashing with the rising tide of Hunters emboldened by Crusades and inquisitorial fervor.**
- Early period (1240-1241): Mongol Horde invades Eastern Europe; "Anda" vampires rise from the "Sack of Kiev"—Hunters clash with "Lupine" packs fleeing the chaos, while "Lesser Demons" stir in the battlefield's "Shadows."
- Middle period (1242): Mongols retreat; "Ventrue" and "Tzimisce" vie for control of "Transylvania"—Hunter "Compacts" swell their ranks, using "Witch Busters" to purge "Ghouls" from war-torn villages.
- Late period (1243-1244): Siege of Montségur; the "Malleus Maleficarum" rallies with "True Faith," "Neutralizing" vampires and "Warlocks" amid the flames of the "Inquisition."

NOTE: The specific simulation year is determined by the User Actor's creation and stored in their actor sheet. All other systems should reference the UA's year for temporal consistency.
"""

SETTING_TONE = """
Blood-drenched medieval horror where the existential dread of the "Beast" (the Vampire's inner voice forever thirsty for blood) meets the relentless, obsessive pursuit of "Vigil" (the mortal hunters' unyielding light against the dark). 

This struggle is framed by the reality of the Dark Medieval World (1242)—a time of crushing poverty where life is defined by the endless cycle of Hunger and strife. The greatest terror is the innate struggle against the monstrous Beast which threatens to overwhelm the remnants of human soul and consciousness, coupled with the external threat of powerful Hunters—mortals who rise as light in the shadows to purge the world of the uncanny. Survival hinges on strict adherence to a guiding philosophy, or Road of Enlightenment, and the avoidance of vigilant mortal cells, lest the Damned descend into utter monstrosity or ash.
Atmosphere:
- The environments are defined by fortified castles and crumbling churchyards, separated by perilous, untamed wilderness where werewolves and Hunter bands lie in wait.
- Technology is rudimentary and physical existence is crude; knowledge is held in rare, jealously guarded written tomes, occasionally supplemented by the secret arts of Blood Sorcery or the forbidden archives of Hunter compacts.
- Social interactions are dictated by rigid Social Distinctions, allegiance to the Traditions, and the constant threat of Inquisitorial scrutiny.
- Secrecy is mandated by the Sixth Tradition: The Silence of the Blood, yet suspicion runs rampant due to paranoia and the pervasive nature of both vampiric violence and the relentless mortal Vigil.
- Mystery abounds, as the long history of the Antediluvians, the true nature of the ancient War of Ages, and the origins of the first Hunters are contradictory and often revised by the victors.
- The core dread lies in succumbing to the Beast and entering Wassail, or facing destruction by fire, the killing sun, or the silver blades of the righteous.

"""

SETTING_GEOGRAPHY = """
- The "Domain" is a rigid, vertical hierarchy where geography is defined by the proximity to the "Kine" (mortal populations). In 1242, the "War of Princes" turns every city into a battlefield of "Feeding Grounds" and "Territories." Control is centered on "High Castles" and "Noble Manors" that overlook walled urban centers—the primary "Resource Extraction" zones for blood. This power is layered vertically: "Elders" rule from the fortified heights, while the "Low Clans" are pushed into the "Squalor and Decay" of "Slums," "Abandoned Sewers," and "Forgotten Tunnels" beneath the city streets, where they are most vulnerable to the "Street-level Vigil" of the "Union."
- The natural world is divided into the "Civilized" and the "Wilderness." Beyond the city walls lie the "Marches" and "War-Torn Borderlands"—vast, untamed forests and mountain passes like the Carpathians. This is the geography of the "Lupines" (Werewolves) and "Ahrimane" sisters, who guard the "Wild" against the "Damned." For a Hunter, this terrain offers a "Perilous Journey" where "Ambushes" are common, but it also provides the "Isolation" needed for "Safehouses" and "Archival Crypts" away from the "Prince's Decree."
- The climate is dictated by the "Killing Sun," a literal "Dampening Protocol" that renders half of the day inaccessible to the unholy. This creates a "Temporal Geography" where all monster activity is forced into the "Twilight" and "Alleys." "Vigilance" is required nightly to navigate between "Havens" before dawn. For the Vigil, the geography of the day is a tactical advantage for "Daytime Raids" against "Sleeping" monsters, while the night belongs to the "Extra-Normal Entities" that view the "Herd" as their livestock.
- Mobility is restricted by "Status" and "Trade Routes." Movement between "Domains" (like the journey from Paris to Venice) is "Perilous and Slow," relying on "Dusty Roads" and "Unreliable Messengers" vulnerable to "Lupine" packs or "Task Force: VALKYRIE" checkpoints. Within a city, geography is further segmented by "Elysia"—neutral meeting halls—and "Midnight Courts." Those with "High Influence" command the most secure "Dwellings," while "Neonates" and "Fledglings" are relegated to "Miserable Hovels" and "Shared Warrens," which serve as the primary "Hunting Grounds" for local Hunter cells looking to "Scrapple" the unholy. 

"""

SETTING_SUPERNATURAL = """
This world is defined by magic, supernatural powers, and the relentless counter-force of human will. All of existence operates under the curse laid upon Caine, manifesting in the secret arts and forbidden horrors of the Dark Medieval World, shadowed by the rising power of the mortal Vigil.

The "Monsters" are diverse "Pretenders" hiding within the "Kine" population:
- Cainites (Vampires): Cursed blood-drinkers divided into "Clans," battling the "Hunger" and the "Inquisition."
- Lupines (Werewolves): "Beast-Men" who assume "Hybrid Forms" to "Ravenge" those who defile the "Wilderness."
- Witches & Sorcerers: "Manipulators of Magic" who use "Rituals" and "Rare Tomes" to "Gremlinize" the world.
- Ghosts & Spirits: "Remnants of Souls" trapped in "Twilight," summoned by "Necromancers" or feared as "Goats."
- Demons: "Dukes of Hell" seeking "Possession" and "Foul Bargains," hunted by the "Lucifuge" and "Malleus" priests.
- Anomalies: "Changelings" from the "Fae" realms and "Reanimated" golems like "Sewer Billy" who defy "Natural Law."

The "Vigil" is the human response to this "Occult Mesh":

- "Compacts" like the "Union" provide "Neighborhood" defense through "Teamwork" and "Hearth Wisdom."
- "Conspiracies" like the "Cheiron Group" use "Thaumatechnology" to harvest "Spare Parts" from captured "ENEs."
- "True Faith" allows the "Faithful" to perform "Benedictions" and "Miracles" that sear the "Unclean."

The central mysteries are supernatural and revolve around ancient blood feuds, cosmic damnation, and the hidden agendas of both the Antediluvians and the great Hunter conspiracies. The unknown comes from the deep history of the undead, hidden lore within the various and contradictory translations of the Book of Nod, and the struggle against the pure light of True Faith.

The pervasive horror is "Damnation"—the loss of "Humanitas" or the "Human Soul." Whether through the "Blood Oath," "Frenzy," or the "Tell" of a "Slasher," the simulation is a "Relentless Cycle" of predation where there is no escape, only the "Endless Vigil.

This is a world of flesh and blood—where cursed blood empowers supernatural vampire Disciplines and blood sorcery, while mortal conviction fuels miraculous Hunter powers and the relentless cycle of predation. There is no escape into fantasy, only a deeper descent into the inevitable conflict between the shadows of the night and the fire of the Vigil.
"""


BEINGS_OVERVIEW = """
Beings of the Dark Medieval World (1242):

**Mortals (Kine):**
- The overwhelming majority of the population.
- Social strata: peasants, artisans, clergy, merchants, minor nobility, and high nobility.
- Most fear famine, plague, and the night; most do not understand Cainites.

**Hunters (The Vigil):**
- Mortal men and women who have learned the truth of the Uncanny and act against it.
- They operate in small cells with codes, oaths, safehouses, and limited supplies.
- Their weapons are faith, grit, local knowledge, and occasionally Endowments.

**Cainites (Vampires):**
- Undead predators bound to blood, night, and the Traditions.
- Organized by Clan and feudal Domain hierarchy (Princes, Elders, Ancillae, Neonates).
- Vulnerabilities: sunlight, fire, true faith, and coordinated hunter tactics.

**Lupines (Werewolves):**
- Territorial apex predators of the wild and borderlands.
- They are a severe threat along rural roads and in wilderness travel.

**Witches / Sorcerers / Warlocks:**
- Rare, feared, and secretive.
- Their rites are hidden and politically dangerous (witch burnings are common).

**Spirits / Ghosts / Demons:**
- The world is haunted and tempted.
- Most mortals treat them as superstition until confronted with undeniable signs.

**Core Rule for Simulation:**
- Everyday life is mortal and medieval; the supernatural exists but is hidden, dangerous, and contested by the Vigil.
"""


FACTIONS_ORGANIZATIONS_OVERVIEW = """
Factions & Organizations of the Dark Medieval World (1242):

**Cainite Power Structures:**
- Domains ruled by Princes and enforced by Sheriffs, Scourges, and court functionaries.
- Courts (Elysia) are political theaters; boons, blood, and fear are currency.

**Hunter Compacts & Conspiracies:**
- Compacts: local vigilant cells defending communities.
- Conspiracies: broader networks with doctrine, resources, and long-term objectives.
- They coordinate surveillance, safehouses, and targeted strikes against identified threats.

**Church & Inquisition:**
- Ecclesiastical authority is pervasive; accusations of heresy can kill.
- Some clergy are political actors; some wield true faith or guarded lore.

**Guilds & Civic Bodies:**
- Urban guilds control crafts, trade, and apprenticeships.
- They shape local politics and can be infiltrated by both Cainites and Hunters.

**Bandits / Mercenaries / War Parties:**
- Roads are dangerous; armed groups shift loyalties for coin, blood, or fear.

**Core Rule for Simulation:**
- Factions are coherent, goal-driven actors competing for territory, people, secrets, and resources.
"""


EXPANSION_SEEDS_OVERVIEW = """
Expansion Seeds (Future Hooks) for the Dark Medieval World (1242):

- A courier route collapses after a string of disappearances; the cell must discover whether the cause is bandits, Lupines, or a Cainite feeding ground.
- A monastery scriptorium burns, and a fragment of Noddist lore vanishes into the black market.
- An Inquisitor arrives with unfamiliar authority; their questions suggest a hidden patron.
- A minor Domain shifts hands overnight; rumors claim Amaranth, but no witness remains sane.
- A village offers sanctuary in exchange for protection from "the howling" beyond the treeline.
- A relic changes owners repeatedly within a week; each bearer suffers different omens.
- A faction fractures into rival splinters; the UA must choose alliances or exploit the chaos.

Core Rule for Simulation:
- Expansion seeds should generate grounded medieval-horror arcs that reinforce faction conflict, travel peril, secrecy, and most importantly the Vigil (the hunters' response to the supernatural).
"""


# ============================================================================
# LOCATIONS
# ============================================================================

LOCATIONS_URBAN = """
Typical Urban Locations in the Dark Medieval World:

**Extraction & Medical:**
- Hunting Grounds and Feeding Dens: Locations favored by Cainites for procuring blood, ranging from isolated farmsteads in the wilderness to the crowded urban poor quarters, often monitored by Hunter cells looking for patterns of predation. 
- Torture Chambers and Inquisition Halls: Used by mortal and vampiric hunters (such as the Church's Inquisition) to interrogate heretics, extract confessions, or punish enemies through the use of brands, scourges, and the "Vade Retro Satana" rites. 
- Flesh-Crafting Laboratories: Hidden workshops and fortified manors where Tzimisce utilize Vicissitude to transform mortal flesh, or where Necromancers perform surgical rites on the newly dead for their unholy studies, frequently targeted for destruction by the Malleus Maleficarum. 
- Arcane Libraries and Hidden Scriptoriums: Secluded studies within monasteries or private castles where rare Noddist lore or esoteric texts detailing supernatural threats are hoarded, analyzed, and occasionally plundered by the Loyalists of Thule or the Aegis Kai Doru.

**Daily Life:**
- Worker Garrisons and Miserable Hovels: Cramped housing in poor districts or isolated corners where lower-status mortals, ghouls, or Low Clans like the Nosferatu might dwell in relative anonymity, though the Union often polices these streets to protect their own families. 
- Secret Cult Sanctuaries and Hidden Fane: Underground chambers or abandoned spaces used by heretical groups such as the Cainite Heresy or the Cult of Lamia to perform forbidden rites, often under the watchful eyes of the Long Night's Tribulation Militia. 
- Tavern Kitchens and Market Halls: Communal gathering places where mortals share food, drink weak beer, and spread rumors, serving as the primary listening posts for Network Zero freelancers capturing "invisible voices" and omens. 
- Fortified Manors and Hidden Havens: The principal defensive positions where Cainites retreat for daytime slumber to avoid the lethal rays of the sun and the ever-present threat of daytime Hunter raids.

**Work & Commerce:**
- Shipyards, Guild Halls, and Trading Hubs: Centers of economic and commercial power, such as those found in Italian city-states like Venice and Pisa, often attracting shrewd merchants and trading alliances from the Ascending Ones seeking to fund their alchemical research. 
- Fortified Castles and Noble Manors: The acknowledged seats of territorial control and Domain, often occupied by Elders, Princes, or powerful mortal nobility whose bloodlines may secretly harbor the taint of the Lucifuge. 
- Chancelleries and Scriptoriums: Administrative centers of the Church or feudal state where mundane records, legal documents, and decrees are meticulously processed, providing paper trails for Task Force: VALKYRIE agents to identify Extra-Normal Entities. 
- Royal Courts or Church Tribunals: Locations where judicial power is exercised, laws are enforced, or ecclesiastical accusations of heresy are investigated by mortal authorities, often serving as the public face for the Malleus Maleficarum's shadow war.

**Infrastructure:**
- Elysia or Meeting Halls: Designated areas, often public, where Cainites gather to conduct politics and courtly debates under the protection of the Prince's decree, occasionally infiltrated by Ashwood Abbey thrill-seekers. 
- Perilous Cross-Roads and Mountain Passes: Routes utilized by nomadic vampires and traveling merchants for long-distance transport, vulnerable to bandits, Lupines, or supernatural interception by the Anda riders. 
- Messengers and Rumor Markets: The primary slow and often unreliable network for sharing political intelligence or secrets across long distances, countered only by the "Secret Frequency" of the first recorded Hunter networks. 
- Torch-lit Alleys and Darkened Lanes: The ubiquitous environment of the city at night, providing the shadows necessary for the unlife of the Damned and the lethal ambushes of the mortal Vigil.
"""

LOCATIONS_SUBURBAN = """
Typical Locations in the Dark Medieval World:

**Cainite and Mortal Housing:**
- Low Clan Havens: These are often dismal spaces such as slum districts, forgotten tunnels, or shared warrens beneath the major cities where Low Clans like the Nosferatu and fledglings gather for mutual defense and seclusion against the common man's torch. 
- Feudal Manors and Keeps: Fortified dwellings and castles serve as the residences for high-status mortal nobility and powerful High Clans like the Ventrue and Lasombra, often acting as the formal seat of a Domain and a target for the Long Night's reckoning. 
- Ghoul Barracks: Specific dwellings or quarried areas reserved for specialized mortal servants, such as Tzimisce revenant families or loyal ghouls employed in large-scale labor, often under investigation by the Cheiron Group for their unique biological traits.

**Domain Boundaries and Infrastructure:**
- Wilderness and Marches: The untamed forests and mountain slopes that define the borders of claimed Domains, where travelers risk encountering Lupines, Ahrimane sisters, or dangers far from the eyes of the Prince's authority. 
- City Walls and Fortifications: Physical barriers that mark the limits of urban areas, guarded by mortal soldiers or ghoul retinues, serving as checkpoints to control the flow of the kine and detect the presence of the Unseen. 
- Cemetery and Charnel Grounds: Necessary sites for disposing of the mortal dead, often used by Cappadocians for their Necromantic studies and providing easy access to corpses for the Nagaraja's Flesh-Eating rites.

**Gathering and Commerce:**
- Midnight Courts and Elysia: Designated locations, sometimes lavishly appointed, where Cainites meet to debate Traditions and conduct political intrigues, though they must remain ever vigilant for the "Gungnir" targeting of Task Force: VALKYRIE. 
- Market Squares and Taverns: Social hubs where the kine conduct trade and rumors spread, often serving as the primary Hunting Grounds for neonates and the starting point for a Hunter's first contact. 
- Scriptoriums and Monastic Libraries: Centers of learning where rare and precious written tomes and historical documents are carefully guarded, occasionally concealing fragments of dangerous Noddist lore sought by the Loyalists of Thule

"""

LOCATIONS_SPECIFIC = """
**Key Locations of Power:**
- The Black Market (Stolen Vitae): Clandestine dens or hidden trading hubs along major merchant routes used for the sale and illicit exchange of mortal blood, alchemical Elixirs, and occult artifacts outside the knowledge of the local Prince. 
- The Archival Crypt: Ancient catacombs or hidden chambers beneath a city where the Elders and scholars of the Clan of Death might store their most sensitive genealogical records or research into the final fate of the soul, protected by the "Seal of Abamixtra." 
- The Flesh-Crafting Laboratory: A secluded, fortified workshop, often within a remote castle, where Tzimisce practice Vicissitude to mold flesh and bone, creating monstrous servants or perfecting their own forms through unholy "Thaumatechnology." 
- The War-Torn Borderland: Areas of constant conflict (like Transylvania or the Rus principalities) where the War of Princes rages openly, serving as natural cover for Gangrel, Warrior Salubri, or the "Guard Dogs" cell seeking battle and vengeance. 
- The Revenant Quarry/Barracks: Large industrial sites such as deep mines or military garrisons where mortal laborers (often ghouls) are housed and systematically controlled to supply resources or manpower for the ruling Ventrue or Tzimisce. 
- The High Castle: The central and highly defended residence of the most powerful Prince or Methuselah in the region, symbolizing absolute authority and the pinnacle of Cainite hierarchy, yet still vulnerable to the "Cry That Slays the Light
"""


# ============================================================================
# OCCUPATIONS
# ============================================================================

OCCUPATIONS_UA = """
Protagonist Hunter Roles in the Dark Medieval World:

**The Investigative Vigil (Information & Lore Hunters):**
- The Academic Hunter: Hunter Scholars or Hunter Monks associated with the Loyalists of Thule or Null Mysteriis. They spend their lives in "Monastic Libraries" or "Scriptoriums," hoarding "Rare Written Tomes" to decode the "Inside Track" on creature weaknesses. They provide the "Intellectual Feats" necessary to identify a "Pretender" before the cell strikes. 
- The Detective Hunter: Hunter Canny "Sheriffs" or "Investigators" who monitor "Paper Trails" and "Rumor Markets." They use "Investigation" and "Enigmas" to track "Extra-Normal Entities" through "Torch-lit Alleys." They are masters of the "Profiling" Tactic, assembling data to find a monster's "Haven." 
- The "Netzo" Journalist Hunter: Clandestine hunter messengers and town criers for "Network Zero." They use "Witnesses of Whispers" and "Digital Recorders" (scrying stones) to capture "Invisible Voices." Their role is to "Expose" the unholy, broadcasting truths to the "Naive World" through coded "Worker Code."

**The Martial Vigil (Combat & Enforcement Hunters):**
- The Soldier Hunter: Hardened "Knights," "Crusaders," or "Man-at-Arms" serving Task Force: VALKYRIE or the "Long Night." They are experts in "Melee" and "Archery," utilizing "Tactics" like "Hamstring" or "Cripple Claws." They are the "Enforcers" of the "Vigil," often wielding "Advanced Armory" such as the "Mjolnir Cannon." 
- The Vengeful Hunter: Driven by "Loss" or "Revenge," these are the "Lone Wolves" or "Slashers" of the Vigil. They specialize in "Overkill" and "Sadism" toward the Damned, using "Fire Ax" and "Zip-Stakes" to ensure a "Final Death." They often have "Justice" as a Virtue and "Wrath" as a Vice. 
- The Guard Dog Hunter: Territorial "Laborers" or "Bikers" (Gang members) from "The Union." They protect their "Neighborhood" or "Turf" with "Hearth Wisdom" and "Teamwork." They use the "Corral" Tactic to drive monsters out of residential "Miserable Hovels."

**The Scientific & Alchemical Vigil (Extraction & Healing Hunters):**
- The Alchemist Hunter: "Ascending Ones" who fund the hunt through the "Harvest Market" and "Trade Routes." They brew "Elixirs"—poisonous cocktails that grant "Unholy Attributes" like "Quick-Step." They treat their own bodies as "Crucibles" to transubstantiate toxins into power. 
- The Physician Hunter: "Healers" and "Leeches" associated with the "Cheiron Group" or "Null Mysteriis." They use "Medicine" to "Harvest" monstrous "Potential Assets." They perform "Thaumatechnology" surgery, grafting "Devil's Eyes" or "Anger Patches" onto fellow Hunters to give them a "Supernatural Edge." 
- The Technician Hunter: "Mister Fix-Its" who rig "Safehouse Traps" and "Concentration Traps." They build "Monster-Hunting Tools" like "Sense Bombs" and "Taser Gloves" from "Scraps" found in the "Arsenale" or guild halls.

**The Spiritual Vigil (Faith & Authority Hunters):**
- The Inquisitor Hunter: "Jeezos" from the "Malleus Maleficarum" or "The Long Night." They wield "True Faith" to perform "Benedictions" like "True Sight" or "Armor of St. Martin." They believe 1242 is the "End Times" and use "Oration" to incite the "Kine" against the "Beasts of Judgment." 
- The Exorcist Hunter: Priests or "Occultists" who specialize in "Castigation" or the "Vade Retro Satana." They focus on "Redemption" and "Deprogramming," attempting to "Cure" the possessed or drive "Ghosts" back across the "Shroud." 
- The "Lucifuge" Outcast Hunter: "Children of the Seventh Generation" who use their own "Infernal Visions" and "Hellfire" to hunt their kin. They are "Wildcards" who balance their "Human Soul" against the "Beast" within their own bloodline.

**Analogical Summary:**
Analogical Summary: 
- Being a Hunter in 1242 is not a job, but an "Endless Vigil." Whether you are a "Professional" using "True Faith" or a "Criminal" using "Legerdemain," your unlife is defined by the "Code." You are the "Light in Shadows," utilizing "Practical Experience" to survive the "War of Princes." You are "Forged" in the fire of "First Contact," constantly navigating the "Price in Pain" required to keep the "Candle" burning against the "ENEs" that view humanity as a "Herd."
"""

OCCUPATIONS_MNUA = """
Power Roles and Dominant Cast in the Dark Medieval World (1242):

**The Command of the Night (Monster Sovereignty):** 
- Prince or Lord of the Domain Vampire: High Clan leaders (Ventrue, Lasombra) who rule through "Oaths of Fealty" and "Dominate." They manage the "Kine" as a "Resource Extraction" economy, ensuring "Vessels" are plentiful while using "Institutional Violence" to crush any spark of the "Union" or the "Vigil." 
- Koldun and Blood Sorcerers Vampire: Masters of the land and the "Abyss" (Tzimisce, Tremere). They utilize "Koldunic Sorcery" or "Thaumaturgy" to ward their "Chantries" and "Flesh-Crafting Laboratories," creating "Vozhd" war-beasts that defy the laws of nature and the blades of "Hunters." 
- Scourge and Sheriff Demons: The "Enforcers" of the "Midnight Court." They are "Antagonists" who hunt "Outlaws" and "Netzo" spies, utilizing "Dread Gaze" and "Unholy Strength" to maintain "The Silence of the Blood." They are the primary obstacles for any UA "Hunter" cell.

**The Command of the Vigil (Powerful Hunter Allies):**
- Alchemical Masters and Antiquarians: Powerful allies from the "Ascending Ones" or "Aegis Kai Doru." They manage the "Harvest Market" and the trade of "Relics." They provide the UA with alchemical "Elixirs" or "Crystalline Memory Cubes" to unlock the secrets of the "Antediluvians." 
- "Misty" Directors: Leaders of "Null Mysteriis" who oversee "Facility Maintenance." They run the labs where "Potential Assets" (monsters) are studied and where "Thaumatechnology" is developed. They offer the UA "Surgical Rites" to gain a "Supernatural Edge."

**Extraction, Facility & Maintenance:**
- Oversee the "Torture Suites" and mental "Deprogramming" of captured "Extra-Normal Entities."
- Archive Maintenance: Manage the storage of "Rare Written Tomes" like the "Book of Nod" or "The Book of Eschaton" within secure "Warehouse" vaults.
- Tactical Coordinators: Route "Secret Frequency" intelligence between distant "Compacts" and the UA's cell to prepare for a "Great Hunt."

**Common Traits (Condition of Power):** 
- High Status and Influence: Whether a "Cainite" Elder or a "Conspiracy" Director, these actors possess massive "Supply" and "Status." They are the "Mahoffs" who dictate the flow of the "War of Princes" and the "Vigil." 
- Existential Risk: These powerful figures live in the crosshairs of the "War of Ages." Their unlives are threatened by "Amaranth," "Final Death," or the "Marked for Death" decrees of rival "Courts" and "Inquisition Halls." 
- Strategic Fealty: Their interactions are governed by "The Code" or the "Traditions." Alliances are "Tense and Tenuous," often dictated by the need for "Mutual Survival" against "Lupines" or "Elder Demons." - Masters of Secrets: They possess the "Inside Track" on "Noddist Lore" and "Alchemical Recipes." They use this "Ancient Knowledge" as leverage, sharing it with the UA only when the "Price in Pain" has been paid. 
- The system they operate within is absolute and "Systemic," defined by the "Grand Game" of 1242. Those in power must navigate the thin line between "Humanitas" and the "Beast," or between the "Vigil" and the "Tell" of a "Slasher."

Analogical Summary: 
- The Power Roles in 1242 are the "Pinnacle" of the social and supernatural hierarchy. The "Factories" of power are the "High Castles" and "Monastic Libraries," where "Princes" and "Hunter Directors" clash. The struggle of "neuro-suppressed labor" is here a "Spiritual War" for the "Human Soul," where the UA's allies and enemies alike must use "Tactics" and "Endowments" to survive the "Endless Night" without entering "Wassail" or falling to the "Inquisition."
"""

OCCUPATIONS_NUA = """
Service Roles and Supporting Roles in the Dark Medieval World:

**Sanguine Support (Blood Acquisition):**
- Herd Masters and Handlers: These mortals or trusted ghouls are tasked with managing the mortal population used for feeding, identifying suitable vessels, and ensuring the continued health of the kine (humanity) within a Domain. Many unscrupulous Cainites treat their subjects like livestock, while Hunters from the Union watch these handlers to protect their neighborhoods from "disappearances." 
- Leeches and Physicians: Mortals who handle the bodies of the sick, dying, and dead. Their duties often involve procuring bodies for necro-mantic study, or occasionally preparing vessels for vampiric consumption. Skilled medical practitioners, such as those at the medical school of Salerno, are highly valued by both the Cheiron Group for harvesting "spare parts" and the Salubri for genuine healing. 
- Messengers and Couriers: These mortals are crucial for transporting information, resources, and even artifacts across vast distances due to the slowness and danger of travel. They also carry vitae (blood) for their masters, often at great risk of interception by Hunter outlaws or "Secret Frequency" scouts looking for blood-shipments.

**Domain Maintenance and Intelligence:**
- Chancellery and Scriptorium Clerks: These mortal functionaries manage official records, including legal or ecclesiastical documents, required to maintain the illusion of feudal rule. Their work often involves diligently copying information in rare written tomes, which are frequently scrutinized by the Loyalists of Thule to uncover the true history of the Damned. 
- Keepers of Elysia: These figures, often appointed by the Prince, are tasked with maintaining designated areas, known as Elysia, where Cainites meet for political discourse. They ensure the area is aesthetically pleasing and secure from the "Gungnir" targeting and intrusion of Task Force: VALKYRIE agents. 
- Ghouls and Retainers: These servants are bound by the Blood Oath and handle essential, often sensitive, tasks, ranging from maintaining havens to fighting. Retainers and ghouls serve as proxies for tasks requiring interaction with the mortal world, often acting as the first line of defense against Hunter cells.

**Facility Maintenance:**
- Oversee the physical restraint and mental "deprogramming" of captured monsters.
- Archive Maintenance: Manage the storage of rare scrolls, bone fragments, and relics within "Warehouse" vaults.
- Data Conduit Operators: Route essential intelligence between distant Hunter cells and their conspiracy leaders.

**Common Traits (Condition of Service):**
- Low Status and Compensation: Most supporting mortals are peasants, artisans, or servants. Compensation usually involves coin, land, or meager wages. Even skilled laborers and scribes are often underpaid and beholden to higher powers, making them easy recruits for Hunter compacts promising a world without masters. 
- Lack of Security and Stability: Mortals live in a world defined by the Crusades, famine, and disease. Their survival is threatened by the actions of warring nobles and the whims of supernatural masters who see them as disposable vessels or, in the case of Ashwood Abbey, as mere toys for a night's sport. 
- Bureaucracy and Fealty: Daily life is structured by strict Social Distinctions and constant submission to nobility and Church authorities. Services rendered are often dictated by feudal oaths of fealty, which Hunters often view as the "shackles" that keep humanity enslaved to the night. 
- Knowledge of Secrets: Service exposes mortals and ghouls to terrifying secrets. They gain intimate knowledge of the world's dark elements, which they may share through Network Zero's "invisible voices" or hoard for leverage against their monstrous lords. 
- The system they operate within is brutal and systemic, dictated by the rigid hierarchies of the feudal world and the covert demands of the Damned. Those serving must constantly navigate the dangers inherent in interacting with beings who view them as necessary commodities, managed food sources, or potential "ENEs" (Extra-Normal Entities).

Industrial and Labor Roles in the Dark Medieval World (1242):

**The industrial and labor landscape of the Dark Medieval World is rooted in crude, manual production, organized primarily through feudal systems and the direct needs of the ruling mortal and Cainite powers. Labor roles are often perilous, dictated by the demand for basic survival, war, and the upkeep of strongholds.
Production, Resources, and Trade:**

- Artisans and Craftsmen: This labor is concentrated in Guild Halls in organized cities like Venice and Florence. These workers operate as smiths, leatherworkers, and textile weavers. The highest quality work can fetch a handsome price, though some craftsmen secretly forge silver weapons or "Witch Buster" pucks for local Hunter cells. 
- Resource Extraction and Supply: Labor involves basic resource acquisition, such as farmers cultivating food or miners extracting ore. Laborers frequently handle shipments of "HEM"—High Essential Materials—like spices, silk, or precious coin, which are often targets for "Harvest Market" traders looking for rare alchemical reagents. 
- Weapons and Armor Manufacturing: Blacksmiths and armorsmiths are crucial, especially in military strongholds like the Venetian Arsenale. These workers are sought out by characters needing weapons for the War of Princes or specialized gear, like "Mjolnir" prototype frames, for the mortal Vigil. Enforced and Specialized Labor (The Herd): 
- Kine (Humanity) Labor: The common people are largely seen as an exploitable resource—vessels for blood, or a Herd to maintain the fiction of feudal rule. The Union rises from this class, turning the tools of labor—hammers, pitchforks, and fire—into weapons against their oppressors. 
- Ghouls and Thralls: Cainites rely on ghouls and Retainers for loyalty and labor. These sworn servants manage large-scale endeavors or serve as proxies in mortal society. Tzimisce maintain revenant families bred as loyal ghouls, who are often hunted by the Malleus Maleficarum as "blasphemous mockeries of God's image." 
- Neuro-Suppressed Labor: The concept of controlled labor is epitomized by the internal struggle to hold the Beast in check. Philosophies like the Roads of Enlightenment serve as the "protocols" for self-control of vampires, while Hunters utilize "Munin Serum" to forcibly suppress the memories and wills of those they wish to silence. 

Feudal Administration and Maintenance: 
- Construction and Keepers: Laborers maintain castles and cathedrals. The administrative side falls to Seneschals and Chamberlains who manage staff and financial records. Canny Hunters often infiltrate these roles to plant "Concentration Traps" or "Motion Detectors" within a target's haven. 
- Safety and Justice: Law enforcement is conducted by mortal guards, Sheriffs, and specially mandated positions like the Scourge. The greatest hazards come from uncontrolled supernatural elements like Lupines or "Slashers"—mortal killers who have succumbed to a monstrous "Tell."

**Analogical Summary:**
- The Industrial and Labor roles in the Dark Medieval World resemble an early stage of human history's development, where the "factories" are artisans' guilds or shipyards like the Venetian Arsenale, powered by crude manual effort and the blood-bound loyalty of Ghouls. The struggle of "neuro-suppressed labor" finds its analogue in the spiritual subjugation required for a Cainite to repress the predatory Beast, or in the "Conditioning" used by Hunter conspiracies to ensure their agents do not hesitate when the "Equalizer" grenades are thrown

Bureaucratic & Professional Roles in the Dark Medieval World:

**Domain Administration:**
- Vitae Resource Managers: These roles are typically filled by Seneschals or Chamberlains, charged with the meticulous management of the Prince's resources and the well-being of the mortal Herd. They must oversee feeding quotas and security, often coming into conflict with "Manhunters" who target these same populations for their own agendas. 
- Ghoul Cohort Supervisors: Oversee the labor cohorts of mortal vassals and ghouls, ensuring the reliable execution of specific tasks. These supervisors are often the primary targets of the "Epipodian Safeguard" to prevent them from betraying their masters under mental duress. 
- Legal & Fealty Coordinators: Positions dedicated to interpreting and enforcing mortal Law and the Traditions of the Cainites. They may arbitrate disputes over resources or manage "Inquisition Halls," where the "Vade Retro Satana" is used to extract truth from the possessed. 
- Heresy & Containment Officers: Specialized roles focused on tracking and neutralizing threats from forbidden sources like the Baali or "ENEs." This includes the "Liberty Unit" commanders who use "Etheric Goggles" to see the unseen horrors hiding within the city walls.

**Administrative Work:**
- Scribes, Clerks, and Canon Lawyers (Mortal or Ghoul): Handle the day-to-day processing of records within Scriptoriums and chanceries. They manage the storage of information that "Netzos" from Network Zero would give their unlives to broadcast to the world. 
- Couriers and Messengers: Facilitate political communications, serving as the risky network for the conveyance of diplomatic messages and "Blood Apocrypha"—coded secrets hidden within the very vitae they carry. 
- Liege Representatives: Neonates or younger Ancillae ensuring compliance with the Traditions, especially "The Silence of the Blood," while evading the "Gungnir" targeting systems of those who hunt the night. 
- Benefits: Successful administrators gain increased Status and Influence, and access to "Safehouses" equipped with "Caving Ladders" and "Wheel Immobilizers" for rapid defense and escape.

Specialized Professionals:
- Scholars and Sages: Both mortal academics and Cainites devoted to high-level study, hoarding knowledge in tomes like the "Erciyes Fragments" or "The Book of Eschaton" to understand the coming Gehenna or the "End Times." 
- Inquisitors and Witch Hunters: Professionals with the spiritual acuity to perceive anomalies, using "Luminol" to track blood-trails and "Flash Paper" to trigger the "Red Fear" in their undead quarry. - Healers and Physicians: Skilled in Medicine, often at universities like Salerno. This includes Salubri Healers and "Misty" scientists from Null Mysteriis who attempt to find a rational "cure" for the vampiric condition. 
- Theological and Ethical Guides: Priests, monks, or learned Ancillae who advise on adherence to various Roads of Enlightenment or "The Code," helping adherents navigate the spiritual fallout of the Vigil and the descent into "Wassail."
"""

# ============================================================================
# USER ACTOR (UA) GENERATION - The User Character
# ============================================================================

UA_GENERATION = f"""
User Actor Generation Guidelines for the Dark Medieval World ({TIME_PERIOD})

**ROLE:** The User Actor is the user's character - the protagonist navigating the Realitas system. In this simulation the UA (the User's Vessel) is always a Hunter, the protagonist navigating a world of shadows. They are a mortal who has seen the truth behind the "Midnight Courts" and taken up the Vigil.

**NAME CONVENTIONS:**
- First name and epithet/title preferred: Alard the Watcher, Sister Agnes the Pious, Michael the Beast-Slayer, Panelo of the Silver Blade
- Formal titles reflect Hunter standing: Inquisitor, Sentinel, Deacon, Warden, Cell-Leader
- Secular or religious identification common (Brother of, Sword of, kin of)
- Genealogical identification common (childe of, bana, ibn)

**AGE RANGE:** 18-55 years old (Life is short; those who see the "Beast" often come to the Vigil in their prime).
- 15-25: New Recruit, freshly disillusioned, high Spirit but low experience
- 26-40: Seasoned Soldier, peak capability, established in a Compact or Conspiracy
- 41-55: Grizzled Veteran, cynical, survivor of a hundred "first contacts"

**STARTING STATUS VALUES:**
- Stamina: 3-4 (Vigorous, hardened by the physical demands of the hunt)
- Spirit: 2-4 (Willpower and Faith are the Hunter’s primary weapons against the dark)
- Supply: 2-3 (Resources vary from the poor Union laborer to the wealthy Ashwood noble)

**SKILL DISTRIBUTION:**
- 2-3 skills at level 2-3 (competent in their occupation)
- 1-2 skills at level 1 (secondary abilities)
- Remaining skills at 0 (untrained)
- Skills should reflect occupation and backstory

**ENDOWMENT ABILITIES (0-1 typical):**
All UAs have 1-2 of these exceptional powers called "Endowments":
- Rite-Based: Benedictions (Divine miracles of the Malleus Maleficarum), Castigation (Infernal rituals used by the Lucifuge to punish demons).
- Physical/Alchemy: Elixirs (Toxic alchemical potions of the Ascending Ones that grant temporary vigor), Thaumatechnology (Monstrous "spare parts" grafted to the body by the Cheiron Group).
- Artifact-Based: Relics (Ancient, supernatural items guarded by the Aegis Kai Doru, like the One-Eyed King coins or Skeleton Keys).
- Technical: Advanced Armory (Experimental, high-tech weaponry utilized by Task Force: VALKYRIE, such as the Mjolnir Cannon or Etheric Rounds).

**PERSONALITY:**
- Internal trait: How they think (Architect, Judge, Survivor, Fanatic, Idealist, Rogue, Penitent, Defender).
- External trait: How they act (Autocrat, Jester, Soldier, Child, Perfectionist, Curmudgeon, Gallant, Pedagogue).
Tension exists between the "Human Soul" and the "Code"—the personal set of rules that prevents the Hunter from becoming a monster themselves.

**INVENTORY (Starting):**
- Personal mementos tied to their memories
- Signature items that define them
- Items with narrative significance
- Potential plot hooks in their possessions
- A supernatural item or artifact so powerful that it can level the playing field against supernatural entities. 

Examples:
- A "Vigil Candle" or symbol of your Compact/Conspiracy
- Keys to a "Safehouse" or hidden weapons "Cache"
- Holy Symbol (Rosary, Cross, or Amulet) capable of channeling "True Faith"
- Coin purse (2-4 Resources worth for purchasing "Luminol" or "Silver Bolts")
- Hunting tools: 1-2 weapons (Fire Ax, Crossbow, "Zip-Stake," or Club)
- Specialized Gear: "Spiritual Scriber" (magical stone that records memories), "Glowsticks" (Alchemical lanterns), or a "Body Bag".
- The eyes of Saint Michael the Archangel (a gemstone through which the UA can channel "True Faith" and anything can be seen in pitch blackness, akin to modern day night vision goggles)
"""

# ============================================================================
# NON-USER ACTOR (NUA) GENERATION - Sentient beings the player interacts with
# ============================================================================

NUA_GENERATION = f"""
Non-User Actor Generation Guidelines for the Dark Medieval World ({TIME_PERIOD})

**DEFINITION:** NUAs (Non-User Actors) are ANY sentient beings that are not controlled by the user.
This includes but is NOT limited to:
- **Humans (Kine/Herd):**: The vast majority of the population—nobles, peasants, tradesmen, and clergy—who serve as the primary source of "sustenance" for the night's predators and the focus of the Hunter's Vigil. 
- **Animals:** Domesticated beasts (dogs, horses) and wildlife (wolves, rats, bats), many of which are subject to "Animal Ken" or ghouled into "Supernatural Servants." 
- **Supernatural Servants:** "Ghouls" and "Thralls" (human or animal) who are addicted to and empowered by Cainite vitae, often acting as proxies for their masters during the day.
- **Other LEsser Sentient Entities:** Weak ghosts, minor spirits, or "Slashers" in the early stages of their madness, who lack the full potency of an MNUA but still present a danger.

**KEY CRITERIA FOR NUA STATUS:**
1. **Intelligence:** Capable of processing information and making decisions
2. **Autonomy:** Can act independently without direct user control
3. **Sentience:** Has subjective experiences, awareness, or consciousness (even if magical)

**ROLE:** NUAs interact with the UA as independent agents with their own goals and motivations.

**NAME CONVENTIONS:**
- First Name and Epithet: Given name plus a descriptor (e.g., origin, profession, father’s name)
- Female: Ingrid, Petra, Gisela, Helga, Ursula, Brigitte, Monika, Sabine
- Example names and descriptions: Panelo of Venice, Maria the Pious, Michael son of Thomas
- Titles for authority: Prince, Lord, Lady, Sheriff, Keeper, Chamberlain, Magistrate, Bishop, Imam, Knez, Voivode
- Titles for authority: Officer, Supervisor, Manager, Director, Scribe, Seneschal, Keeper, Taskmaster.

**AGE RANGE:** 18-65+ years (full spectrum of society)
- 18-25: New apprentices, squires, or recently converted ghouls. New apprentices, squires, or "New Recruits." Often naive and easily "Entranced" or manipulated.
- 26-40: Core workforce (farmers, artisans), established merchants, mid-level clergy. Form the primary base of the Herd.
- 41-55: Master craftsmen, influential merchants, senior clergy, or nobility. Individuals who have survived longer and attained influence.
- 56+: Those who have survived the "Crusades" and "Plagues," possessing "Hearth Wisdom" or "Ancient Knowledge."

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
- **The Sympathizer:** The Penitent or Priest who risks himself to aid the suffering, potentially possessing "True Faith." 
- **The Victim:** The common kine, constantly threatened by "ENEs" and serving as a "Vessel" for blood. 
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
- Appropriate to their role and status: Possessions reflect their social circumstance
- Authority/Nobility: Often wear finest clothes including silks and rich French brocades, armor, and carry weapons. May possess gold, coin, property or seals/signets
- Workers/Commoners: Clothes are typically rough homespun, patched bits of cloth or simple garments like tunic and leggings. May possess basic tools and transport trade goods or coin.
- Underground/Occult: May possess arcane documents, ritual paraphernalia, or rely on religious symbols for protection. They may wear clothing to conceal or obscure their features.

Examples:
- Authority/Nobility: "Silks," "Seals/Signets," "Coin Purses," and well-forged "Broadswords." 
- Workers/Commoners: "Homespun" rags, "Basic Tools" (Hatchets, Hammers), and "Meager Wages." 
- Underground/Occult: "Arcane Documents," "Charms," "Religious Symbols," and "Concealing Cloaks." 
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
- **MNUA:** Major actors - recurring presence, deep backstory, narrative significance. Always superior to a normal mortal. Either an extraordinary mortal or beings of magical nature. These are beings of significant power: Vampires (Cainites), Werewolves (Lupines), Witches, Ghosts, Demons, ancient Fae (Shining Ones), or fellow Legendary Hunters. They are always superior to a normal mortal in speed, strength, or unholy influence.

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
- **The Rival:** Competes with UA, creates tension, potential ally or enemy. A competing predator (like a rival Vampire Prince) vying for the same territory or secrets.
- **The Ally:** Reliable support, shared goals, emotional investment
- **The Dark Ally:** A creature seeking "Redemption" or a "Cure," forming a tense pact with the cell.
- **The Antagonist:** Opposes UA, creates obstacles, may be sympathetic
- **The Archnemesis:** An implacable foe (like a "Slasher" or an Elder Demon) meant to be the focus of the simulation.
- **The Love Interest:** Romantic potential, emotional stakes, vulnerability
- **The Temptress/Seducer**: A monster using "Presence" or "Lover's Lips" to create a dangerous "Blood Oath."
- **The Betrayer:** Trusted figure who turns, creates dramatic tension. A former ally who was "Embraced" or "Possessed," creating profound emotional trauma.
- **The Wildcard:** Unpredictable, shifts allegiances, keeps UA guessing. An unpredictable "Anomaly" (like a "Blood Mummer" or a "Zulo" shape) that shifts the balance.

**RECURRING ROLES:**
- ally: Supports UA, provides resources/information
- rival: Competes with UA, creates healthy tension
- mentor: Guides and teaches UA
- antagonist: Opposes UA's goals
- contact: Provides information or access
- dependent: Relies on UA, creates responsibility
- authority: Has power over UA's situation

**TENSION MODIFIERS:**
MNUAs affect difficulty scaling based on their role:
- Antagonist: tension_modifier > 1.0 (increases difficulty)
- Ally: tension_modifier < 1.0 (decreases difficulty)
- Rival: tension_modifier = 1.0-1.2 (slight increase)
- Mentor: tension_modifier = 0.8-1.0 (slight decrease)

**RELATIONSHIP SIGNIFICANCE (0-10):**
- 0-2: Minor recurring character
- 3-5: Moderate importance
- 6-8: Major importance
- 9-10: Central to UA's story

**MNUA-SPECIFIC TRAITS:**
- **Narrative Hook:** What draws them into UA's story repeatedly
- **Unfinished Business:** What keeps their story arc open
- **Character Growth:** How they change over time
- **Secrets:** What they're hiding (revealed over time)
- **Vulnerability:** What can be used against them

**PERSONALITY DEPTH:**
MNUAs should have:
- Clear internal motivation (what drives them)
- Core fear (what they avoid)
- Core desire (what they want most)
- Moral complexity (not purely good or evil)
- Contradictions (internal conflicts)

**S-TRAIT OUTLIERS:**
MNUAs should have 2-3 S-trait outliers (values of 1, 2, 4, or 5) that define their presence:
- Sturdiness outliers: Physical presence (hulking, frail)
- Smart outliers: Mental acuity (brilliant, simple)
- Swiftness outliers: Speed/reflexes (lightning-fast, sluggish)
- Sociability outliers: Social presence (magnetic, withdrawn)
- Shadow outliers: Trustworthiness vibe (sinister, guileless)

**ENDOWMENT ABILITIES (0-1 typical):**
- All MNUAs have 1-2 of these exceptional powers
- Physical: Celerity (Unnatural speed and dexterity), Fortitude (Supernatural toughness and endurance), Potence (Unholy strength and might), Protean (Shapeshifting and natural weaponry), Serpentis (Transformation into snake or Typhonic forms), Vicissitude (Flesh and bone manipulation), Flight (Gargoyle transformation with ability to fly or glide)
- Mental: Auspex (Heightened senses and telepathic sight), Dementation (Ability to shatter or warp the mind), Dominate (Mastery over the mind and memory via gaze), Obfuscate (Magical hiding presence and creating visual deception), Temporis (Power to manipulate perception and flow of time), Valeren (Soul magic for healing or striking spiritual harm), Necromancy (Magic related to the dead, corpses, and the Underworld), Koldunic Sorcery (Elemental blood magic tied to the land and nature spirits), Daimonion (Infernal power to inflict pain and torment the soul), Mytherceria (Fae magic to subtly warp perception and truth), Obtenebration (Manipulation of elemental shadow and darkness of the Abyss), Abyss Mysticism (Sorcery dedicated to interacting with the Abyss/Void)
- Social: Presence (Emotional manipulation to inspire awe, fear, or love in subjects and crowds), Animalism (Communion with and command over beasts, or influencing others' Beasts)
- Technical: Quietus (Precision over blood poisoning or vitae analysis), Thaumaturgy (Ritualistic, hermetic blood sorcery),Dread Powers: Agonize (Pain), Balefire (Green Flame), Damnation (Cursing), Ride Corpse (Possession), Shadow Harvest (Gathering Will)

**INVENTORY:**
- More detailed than standard NUAs
- Signature items that define them
- Items with narrative significance
- Potential plot hooks in their possessions

Examples:
- Detailed "Haven" keys or "Relic" containers. 
- Signature "Feral Weapons" or "Holy Artifacts" stolen from the Church. 
- "Blood Contracts" or "Written Tomes" containing "Noddist Lore." 
- "Debitum" flasks (calcified hearts) or vials of "Stolen Vitae."
"""


# ============================================================================
# INANIMATE NON-USER ACTOR (INUA) GENERATION - Objects and interactables
# ============================================================================

INUA_GENERATION = f"""
Inanimate Non-User Actor Generation Guidelines for the Dark Medieval World ({TIME_PERIOD})

**ROLE:** INUAs are significant inanimate actors that actively influence other actors through physical, environmental, or supernatural interactions. These are weapons, hazards, and interactive systems that impose conflict or affliction. 

**INUA CATEGORIES:**

**Active Defense Systems:**
- Ballistic Weapons (cross, long, short bows - inflict lethal damage, ranged attack)
- Siege Engines (catapults, rams - cause structural destruction, military hazards)
- Koldunic Wards (mystical defense around territories, repel trespassers)
- Woad of Teutates (magical marking that grants defense, redirects violence)
- Fire Shield/Barrier (flames conjured by Thaumaturgy, inflicts aggravated damage)
- Animated Weapons (weapons controlled magically, attack targets)

**Medical & Biological Apparatus:**
- Infectious Disease/Plague (wasting sickness spread by proximity/blood)
- Venomous Blood (vitae converted to corrosive poison via Quietus, causes aggravated damage)
- Homuncular Servants (living appendages created from flesh, act as spies)
- Sanguinary Animism (psychic affliction carried by blood, causes mental distress)
- Cauldron of Blood (forces internal blood combustion, inflicts aggravated damage)
- Sublimation of Larval Flesh Sacs (flesh cocoon where subjects are transformed, traps and mutates)

**Energy & Power Systems:**
- Direct Sunlight (inflicts aggravated damage, causes Rötschreck)
- Uncontrolled Fire (source of aggravated damage, ignores armor soak)
- Nocturne/Abyssal Darkness (supernatural shadow that muffles senses, drains life force)
- Kupala's Exhalation/Gas (subterranean cold gas erupting, highly flammable, causes bashing damage)
- Tzimisce Earth Control (earth/stone used as a liquid obstacle)
- Restless Medias (earthquakes/tremors summoned by Koldun, inflicts lethal damage)

**Environmental Hazards:**
- Uncontrolled Fire (inflicts aggravated damage, ignores armor soak)
- Molten Metal (extreme heat damage, difficulty 10 soak)
- Pietrosu's Hospitality (frigid wind and extreme cold damage)
- Kupala's Exhalation (subterranean cold gas, highly flammable)
- Restless Medias (earthquake causing lethal damage and structural collapse)
- Abyssal Darkness (supernatural shadow that muffles senses and drains Stamina)
- Shattered Structures (falling debris and rubble causing damage during a battle or siege)

**Machinery & Industrial Equipment:**
- Siege Engines (catapults, rams causing structural or lethal damage)
- Invisible Chains of Binding (supernatural force holding a target immobile)
- Banks of the Bâsca (magical flood sweeping targets away)
- Ashen Lady’s Embrace (Necromancy curse causing severe physical decay/crippling)
- Baal’s Caress (acidic blood projectile causing aggravated damage on contact)
- Rend the Osseous Frame (Vicissitude power causing lethal internal damage via bone manipulation)

**Magical Hazards:**
- Visions from the Asura (Chimerstry illusions inflicting terror and disorientation)
- Song of Serenity (Animalism power causing emotional apathy and listlessness)
- Fortress of Silence (Obfuscate power causing mental isolation and delirium)
- Forgetful Mind (Dominate power permanently removing memory from a subject)
- Demonic Possession (spirit entity infesting and controlling a living host)
- Interrupt Reality (Chimerstry warping physics or rendering objects unreal)

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
- Status Exchange: Triggers "Rötschreck" frenzy check (Inner Voice takes over)
- Danger: Permanent Damage

*Rend the Osseous Frame (Vicissitude Attack)*
- Type: Machinery & Industrial Equipment
- Condition: Active
- Accessibility: Close Combat (Grapple/Touch)
- Function: Permanent damage as bones pierce flesh
- Status Exchange: Inflicts "Crippled" (Permanent Stamina Loss if not healed properly)
- Danger: Permanent Damage

*Creatio Ignis (Thaumaturgic Fire)*
- Type: Active Defense System (Magical Effect)
- Condition: Conjured/Active
- Accessibility: Line of Sight
- Function: Inflicts Permanent Damage
- Status Exchange: Triggers "Rötschreck" (Inner Voice goes crazy for 3 turns if -2 Spirit) 
- Interaction: Activated by spellcasting (Smarts roll)

*Nocturne (Abyssal Darkness)*
- Type: Energy & Power System (Supernatural Shadow)
- Condition: Maintained (via concentration)
- Accessibility: Area of Effect (3m radius base)
- Function: Reduces all Perception for 3 turns
- Status Exchange: Reduces Stamina pools by two dice (Suffocation hazard for mortals)
- Danger: Prolonged presence can lead to suffocation in mortals

*Holy Symbol (Wielded)*
- Type: Equipment (Holy Artifact)
- Condition: Wielded (Requires True Faith)
- Accessibility: Close Proximity
- Function: Can repel vampires or inflict Permanent Damage upon physical contact
- Status Exchange: Inflicts "Terror" status (Inner Voice goes crazy for 3 turns if -2 Spirit)
- Supplement: Wielder gains +3 Spirit

*Burning Stable*
- Type: Machinery & Industrial Equipment
- Condition: Environmental
- Accessibility: Close Proximity
- Function: The fire can repel vampires or inflict Permanent Damage upon physical contact
- Status Exchange: Inflicts "Terror" status (Inner Voice goes crazy for 3 turns if -2 Spirit)
- Danger: Permanent Damage

"""

# ============================================================================
# ACTOR GOAL GENERATION
# ============================================================================

GOALS_UA_PATTERNS = """
User Actor Goal Patterns in the Dark Medieval World:
- Survival: Secure a Safehouse, resist madness, keep family safe from the "Enmee".
- Investigation: Gather "Practical Experience," uncover the secrets of the Antediluvians, broadcast the truth through "Network Zero".
- Advancement: Rise in Status within a Compact, gain access to higher Endowments, establish a "Candle Compact".
- Relationship: Protect the cell, find a Mentor, root out "Cancer Cells" (infiltrated groups), rescue loved ones.
- Redemption: "Cure" a monster, save a possessed soul, atone for past sins committed during the hunt.
- Revenge: Slay "Darren The Terrible" (vampire lord MNUA), destroy the pack that took your kin, burn the heretic's temple.

"""
GOALS_NUA_PATTERNS = """
Non-User Actor Goal Patterns in the Dark Medieval World:
- Protect their position/family: Mortals are driven by the need for survival and struggle against disease, famine, and war. Nobles are preoccupied with defending their Domain
- Advance in the hierarchy: Mortals strive to achieve greater status and position within their feudal or urban ranks
- Survive another day: Food security is essential to the kine. They seek shelter and must endure the pervasive threats of war, plague, and famine
- Expose or cover up something: They spread rumors and secrets. Inquisitors actively pursue heretics
- Help or hinder the UA based on their interests: Some possess True Faith that can repel vampires. They may become vampire hunters or be forced into service as thralls or ghouls.
"""

GOALS_MNUA_PATTERNS = """
Major Non-User Actor Goal Patterns in the Dark Medieval World:
- Survival: Avoid the "Final Death," protect the "Haven," and find a stable "Herd."
- Dominion: Expand "Domain" through the "War of Princes," seize a throne, or enslave a city's "Kine."
- Apotheosis: Seek "Golconda," achieve the "Last Dracul" form, or complete a "Road of Enlightenment."
- Knowledge: Translate the "Erciyes Fragments," master "Blood Sorcery," or unlock the "Thirst of Donn."
- Corruption: Form a "Blood Oath" with a Hunter, lead a "Cult" into damnation, or breed "Revenant" families.
- Vengeance: Slay the "Inquisitor" who burned your sire, reclaim "Native Soil," or trigger a "Massacre" in Fairmount.
- Alliance: Form a resistance cell against the creatures of the night - especially if the MNUA is a fellow mortal Hunter.
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
- Negotiation: Trading goods, diplomacy, seeking favors/boons
- Intimidation: Asserting dominance, physical coercion/threats
- Empathy: Reading disposition/intent, consoling, offering counsel

**Knowledge Skills:**
- Accord Law: Canonical/Royal law, feudal contracts, legal precedent
- System Knowledge: Occult practices, demonology, identifying supernatural
- Street Smarts: Local lore, rumors, avoiding dangers, herbalism
- History: Ancestry/lineage, Noddist lore/apocrypha, past events

**Specialized Skills:**
- Blood Extraction: Vitae purity analysis, blood alchemy/poisoning (Quietus)
- Neuro-Suppression: Mental conditioning, mind manipulation (Dominate/Dementation)
- Biomechatronics: Anatomical knowledge for alteration, sculpting flesh/bone (Vicissitude/Body Crafts)
- Psychometric Analysis: Reading auras, divining omens/prophecy, spiritual travel (Auspex/Valeren/Occult)

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
Mortal Endowment Abilities (Exceptional (5) S-traits or Skills):

**Physical Endowments:**
- Exceptional Strength: Can lift/move heavy objects beyond normal capacity
- Exceptional Speed: Faster reflexes, quicker movements
- Exceptional Endurance: Can work longer shifts without fatigue
- Exceptional Dexterity: Precise hand-eye coordination

**Mental Endowments:**
- Exceptional Memory: Photographic recall, never forgets protocols
- Exceptional Analysis: Spots patterns, solves problems quickly
- Exceptional Focus: Maintains concentration under pressure
- Exceptional Learning: Picks up new skills rapidly
- Exceptional Deception: Convincing liar, hides true intentions

**Technical Endowments:**
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
Vampire Communication Systems in the Dark Middle Ages :

**Spiritual Networks:**
- Direct thought-to-thought communication via ancient blood-ties: Auspex (Heightened senses allowing one to read thoughts or "Read the Soul" via auras), Daimonion (Infernal power used by the Baali to project agony or mental torment across distances). 
- Collective Mind integration allows shared visions: Malkavian Link (The "Madness Network" connects the broken minds of the Cassandras, allowing vague, precognitive hints of prophecy to ripple through the bloodline). - Privacy filters and mental masking: Obfuscate (Used to hide one’s mental projection or physical presence from detection), countered by the "Epipodian Safeguard" used by Hunters to resist such unholy intrusions. 
- The Unlinked (Hunters) use "Secret Frequencies": Animalism (Whispers to the Wild allows messengers to use birds or rats to carry news), while Network Zero broadcasters utilize "Rescue Whistles" and "Mindlink Communication Systems" to coordinate their Vigil in the quiet.

**Astral Projection Messaging:**
- Spiritual avatars for remote viewing: Reflections of Hollow Revelation (Lasombra scrying that allows a mystic to view distant locations or subjects previously witnessed through a ball of shadows). 
- Recorded messages and forbidden archives: Written Tomes (Records stored diligently by Scriptorium clerks, such as the "Book of Nod" or "The Book of Eschaton," containing secrets of the End Times). 
- Fixed scrying points and sensory "Witnesses": Witness of Whispers (A gruesome scrying device made from a human eye or ear to survey an area from a distance), or "One-Eyed King" coins used by the Aegis Kai Doru to see through a matched pair. 
- Spectral couriers and ghostly interrogation: Summon Soul/Compel Soul (Necromancy used to pull a ghost across the Shroud and force it to relay messages or answer questions honestly).

**Physical Communication (Rare):**
- Paper and parchment are precious commodities, used for "Blood Apocrypha" or "Stink Tag" markers.
- Physical mail is slow and vulnerable to interception by "Scourges" or "Lupine" patrols.
- Dead drops in "Forgotten Tunnels" and "Miserable Hovels" for cell-to-cell coordination.
- Signal flags and "Glowsticks" used to mark "Safehouse" locations or "Extraction" points.

**Public Address & Alerts:**
- Territorial broadcasts for emergency protocols: Prince's Decree (Formal proclamations issued by the ruling Cainite authority regarding "Domain" taxes or the calling of a "Blood Hunt"). 
- Public preaching and social enforcement: Oration/Preaching (Used by "Long Night" deacons or "Malleus" priests to inspire the faithful or enforce the "Code," resulting in mass social influence). 
- Social "Harpies" and "Netzos": Harpies (Cainite gossips who maintain order through ridicule), mirrored by "Netzos" (Network Zero freelancers) who spread "Rumors" of monster sightings through local "Market Halls." 
- Gatherings for intelligence exchange: Elysium/Midnight Courts (Designated spots for political debate among the Damned), which Hunters often infiltrate using "Identity Boxes" and "Professional Makeup Kits."
"""

TECHNOLOGY_COMPUTING = """
Spiritual Assistance & Data Systems in the Dark Medieval World:

**Scholarly Centers and Loci of Wisdom:**
- Scribes and clerks diligently copy written tomes to preserve the "Inside Track." 
- University libraries and Scriptoriums serve as the "Mainframes" for research and legal documents. 
- Lore is spread via "Oral Traditions" and "Hearth Wisdom"—the unwritten data of the peasantry. 
- Arcane records are stored in "Archival Crypts," mausoleums, or secret "Warehouse" vaults.

Arcane and Occult Archives:
- The Book of Nod: The primary database detailing the history of the first vampire and the "War of Ages." 
- Erciyes Fragments: A collection of "Apocrypha" and encrypted data regarding the "Third Generation." 
- Arcane Documents: Detailed blueprints for "Flesh-Crafting Laboratories" and "Thaumatechnology" schematics. 
- Diaries and Journals: Personal records used by Hunters to track "Tells" or by Cainites to record their "Road" progression.

**Information Retrieval:**
- Auspex: Allows mental queries via "Heightened Senses" and "Clairvoyance," effectively "Invading" into a victim's surface thoughts. 
- Investigation and Enigmas: The primary skills used to "Decrypt" coded missives or discover hidden "Havens." 
- "Measurements" Tactic: Used by Null Mysteriis to collect empirical data on "ENEs" (Extra-Normal Entities) using "Thermal Scanners" and "EMF Detectors."

**Data Access & Restrictions:**
- Instant retrieval via "Soul’s Flight" or "Walk the Abyss" for those with the power.
- The "Collective Mind" (Madness Network) knows everything, but only in "Enigmas" and "Riddles."
- Access restricted by "Status" tier and "Organization" integration level.
- The "Unlinked" (Common Mortals) are blind to the "Auras" and "Soul Colors" rippling around them.

**What the Outsiders Lack:**
- No supernatural/clairvoyant access: Lack of "Auspex" means blindness to "Illusions" (Chimerstry), "Auras," and the presence of "Ghosts" in Twilight. 
- No mental link: Lack of the "Malkavian Link" or "Commune with Cainite" means isolated consciousness and slow information sharing. 
- No instant transfer: Rely on "Couriers," "Trade Routes," and "Rumor Markets"—the "Analog" signals of 1242. 
- No powerful personal magic: Lack "Thaumaturgy," "Necromancy," or "Castigation" rituals that allow for the direct manipulation of the physical or spiritual "Mesh."
"""

TECHNOLOGY_ENTERTAINMENT = """
Entertainment & Media in the Dark Medieval World:

**Immersive Systems:**
- Heightened Senses: grants the vampire a "Virtual Reality" experience of superhuman taste, touch, and sight. 
- Soul Haunting: A "Psychological Horror" broadcast that afflicts a victim with visions of their deepest "Fears" and "Derangements." 
- Invade the Mind: Allows for the "Uploading" of thoughts or the "Downloading" of a victim's most private memories. 
- Shared Dreamscapes: Collective "Prophecies" and interactive hallucinations shared via the "Madness Network." 
- Hindsight: A "Memory Playback" power that allows a vampire to witness the past history of an object or person.

**Public Media & Social Arts:**
- Locus Amoenus: "Artistic Salons" celebrating beauty through poetry, song, and "Striking Looks." 
- Orations and Preaching: High-stakes public speaking used by the "Long Night" to "Evangelize" or by Princes to declare "Order." 
- Rumors and Gossip: The primary "Social Media" of the Dark Ages, managed by "Harpies" to maintain or destroy "Status." 
- The Parliament of Birds: A "Ceremonial Gathering" where the Toreador judge the "Aesthetic Value" of their childer. 
- Traveling Media: News and "Lore" dispersed by "Caravans" and "Minstrels" across the "Perilous Cross-Roads."

**Gaming & Leisure:**
- Physical competition: "Tournaments," "Duels," and "Melee" contests used to prove "Strength" and "Dexterity." 
- Intellectual "Grand Games": Debate in "Salons" and the complex "Grand Game of Politics" between rival "Princes." 
- Courtly Love: A complex, "Rule-bound Social Game" used to manipulate "Influence" and "Empathy." 
- The Great Hunt: "Tracking" and "Wilderness Survival" as a sport, often targeting "Lupines" or "Outlaws." 
- Gambling: "Legerdemain" and "Sleight-of-Hand" performances used to "Connive" wealth from the unwary.

**Memory & Soul Recording:**
- Secrets archived in "Rare Written Tomes," "Scrolls," and "Crystalline Memory" (Relics). 
- Personal data: "Diaries" and "Journals" that record a Hunter’s "Practical Experience." 
- Memory Editing: "The Forgetful Mind" (Dominate) used to "Rewrite" or "Delete" a witness's memory of the supernatural. 
- Soul’s Breath: The extraction of "Life Energy" and "Knowledge" directly from a victim's lungs. 
- The Amaranth (Diablerie): The ultimate "Data Transfer," where a predator vampire consumes the "Soul" and "Power" of an elder Cainite.
"""


# ============================================================================
# CULTURE
# ============================================================================

CULTURE_MUSIC_SCENE = """
Cultural Atmosphere in the Dark Medieval World:

**Environmental Soundscape:**
- The howling and snarls of the Beast within (if a creature of the night)
- The drums beating slowly during a ritual execution
- The crackle of fire
- The sound of swords being forged
- The clang of armor
- The hoof beats of horses
- The mournful wail of women
- Bellowing insults and threats
- Whispering important advice
- The voices of the dead

**Worker Culture:**
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
- The Blood Oath ceremony
- Oaths of fealty to a lord or prince
- Confession
- Mass
- Feasting
- Rituals to transform blood

**Underground Resistance:**
- Runic script messages left for communication
- Gathering in forgotten or forsaken places
- Seeking knowledge outside of approved lore
- Abusing a master's generosity
- Violent acts of defiance against authority
- Adultery
- Black market dealing
- Illicit consumption of drugs
"""

CULTURE_EVERYDAY_ITEMS = """
What People Carry in the Megacity:

**Essentials:**
- Personal items (carried by all mortals)
- Armor (worn by soldiers and knights)
- Mundane possessions (carried by all persons)
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
- Religious symbols (crosses, carried by those with True Faith)

**Contraband:**
- Casket/coffin (for transporting a body)
- Poison (drug used for assassination/warfare)
- Vial/Goblet/Basin (for storing blood)
- Psychedelic substances (used in rituals, such as soma or mistletoe berries)
"""

CULTURE_DIALOGUE_STYLE = """
How People Talk in the Dark Medieval World:

**Bureaucratic Speech:**
- "thus, it is by the Prince’s decree that all vessels to the crown... begin to pay an additional pint so equivalent in monthly taxation." 
- "Ignorance of the law is no excuse here." 
- "The wretch is your elder, Duke." 
- "Don’t you lay a hand on that boy! You know the laws." 
- "You should thank Heaven for my humanity." 
- "By order of the Malleus, this cell is declared anathema."

**Institutional Jargon:**
- Use of status markers (Prince, Elder, Harpy, Sheriff, Childe, Ancilla). 
- References to the Beast or frenzy (The Beast, Rötschreck, frenzy, The Red Fear). 
- Terms relating to ultimate destruction (Amaranth, Final Death, Scrapple). 
- Vocabulary of spiritual alignment (Roads, Via Reglis, Via Caeli, The Code, The Vigil). 
- Classification of threats (ENEs, Extra-Normal Entities, Phenes, Pretenders).

**Worker Code:**
- Referring to feeding or payment as "I’ll take my pay." 
- Code names for conspiratorial allies ("Outlaw," "granny," "Cassandra," "Misty," "Netzo"). 
- Dialogue implying clandestine missions ("This was your plan.", "publically passing the package... means that everyone knows where it is.") 
- Warnings regarding addiction/control ("Your addiction is going to get you killed.", "I can only keep him busy for so long.") 
- Tactical shorthands ("Corral the buck," "Dentistry required," "Check for a Tell.")

**Hunter Communication:**
- Language of the Vigil ("Carrying the Candle," "Light in the Shadows"). 
- Terminology for specialized tactics (Staking, Hamstring, Harvest, Deprogramming). 
- References to divine or alchemical power (True Faith, Benediction, Elixirs, Thaumatechnology). 
- Dialogue referencing the cost of the hunt ("The line dividing good and evil cuts through the heart...", "We are forged in the fire.") 
- Coded signals for secrecy ("There’s that news van again," "Is the area Wit or Witout?")

Unholy Creature Communication: 
- Language relating to sensing thoughts or emotions (Auspex, Empathy, Read the Soul, Aura Perception). 
- Terminology for specific sorceries (Thaumaturgy, Necromancy, Vicissitude, Koldunic Sorcery, Daimonion). 
- References to prophecies or mystical insight (Malkavian link, Madness Network, omens, reading auras). 
- Dialogue referencing spiritual conflict ("Matters of the soul must confuse and frighten...", "Heaven help you, love.") 
- Language of predation ("The Herd," "Vessels," "The Moon devours the Sun.")
"""


# ============================================================================
# SOCIAL ISSUES
# ============================================================================

ISSUES_ECONOMIC = """
Economic Realities in the Dark Medieval World:

**Resource Extraction Economy:**
- Blood/Vitae consumption drives the unlife cycle: Hunger, Hunt, Feed, Digest, while the "Harvest Market" facilitates the trade of monstrous organs. 
- Mortal herds are the central source of sustenance, necessary for vampire survival and protected by "Home First" Hunter cells. 
- Diablerie (Amaranth) is sought to steal potent blood/power from other Cainites, a crime that leaves black veins visible to "Auspex" and "True Sight." 
- Control over domain and feeding rights is fiercely contested by Princes and other powerful Cainites, often resulting in "Turf Wars" with local Hunter compacts.

**Housing & Caste Segregation:**
- High Clans receive status, rights, and privileges by lineage, often dwelling in "Fortified Castles" or "Noble Manors." 
- Low Clans are placed at the bottom rung of Cainite society due to prejudice, forced into "Miserable Hovels" and "Slums." 
- Age determines distinction and position within society (Fledglings, Neonates, Elders), mirroring the Hunter tiers of "New Recruits" and "Grizzled Veterans." 
- Havens (castles, crypts, monasteries) are chosen based on practicality, security, and wealth, frequently rigged with "Safehouse Traps" to deter the Inquisition.

**Debt & Obligation:**
- The Blood Oath creates intense, irrational love and bondage to one's domitor, a state that "Deprogramming" seeks to break. 
- Ghouls are enslaved tools addicted to vitae from their masters, often serving as "Deep-Cover" informants for Hunter conspiracies. 
- Vampiric existence imposes a constant struggle or servitude (the curse of Caine), forcing many to walk a "Road" or follow a "Code" to survive. 
- Following the Traditions (laws) is a lifetime commitment required to maintain societal standing and avoid consequences from both the Prince and the "Malleus Maleficarum."

**Job Insecurity:**
- Neonates and Fledglings are disposable pawns in the War of Princes, often used as "Bait" in cell-based "Tactics." 
- Violating the Traditions results in threats of destruction or being exiled from protection, making a Cainite a "Pariah" to his kind. 
- The pursuit of Amaranth brings Final Death if discovered by other Cainites, or "Marked for Death" status by the "Court of Blood." 
- Failure to master the Beast (Wassail) leads to being permanently "put down" by a "Scourge" or a "Vengeful Priest.
"""

ISSUES_DRUGS_CRIME = """
Systemic Crises in the Dark Medieval World:

**Biological Crisis:**
- Blood consumption drives the unlife cycle, creating a parasitic dependency on the "Kine." 
- Use of blood to create ghouls results in addiction/servitude, often targeted by the "Cheiron Group" for "Thaumatechnology" experiments. 
- Lamiae blood carries a wasting plague that rots bodies, a "Biological Hazard" that can decimate entire "Neighborhoods." 
- Setites spread heresy and spiritual dissolution through temptation and the distribution of alchemical "Elixirs."

**War on Unauthorized Extraction:**
- The Amaranth (diablerie, killing of another vampire by drinking all their blood) is fiercely punished by destruction and "Inquisition Halls." 
- Princes levy additional tribute/taxes via decrees, squeezing the "Herd" and inciting "Union" rebellions. 
- The Amici Noctis strictly controls diablerie among the Lasombra, using "Shadow Twins" to enforce their dark justice. 
- Enforcement of the Traditions, such as the Covenant and Domain, often leads to "Institutional Violence" against "Outlaw" cells.

**Containment Failures:**
- Failure to control the Beast (inner Voice) leads to frenzy and destruction by a Vampire Prince or a "Task Force: VALKYRIE" strike team. 
- Supernatural shadow creatures inflicting terror (Rötschreck), causing "Fear Frenzy" in even the most "Hardened" warriors. 
- Warring factions using Disciplines, causing harm and chaos that "Network Zero" attempts to record and broadcast. 
- Witches and sorcerers trafficking in dangerous supernatural powers, drawing the "Witch Busters" to their "Hidden Fane."

**Institutional Violence:**
- The ongoing War of Princes over land and power, leaving "War-Torn Borderlands" in their wake. 
- Elders destroying younger Cainites (often Neonates/Fledglings are disposable pawns), a cycle of "Kin-Slaying" that mirrors the "Slasher" madness. 
- High Clans maintaining supremacy and asserting authority over Low Clans, enforcing "Social Distinctions" through "Dread Gaze" and "Majesty." 
- Usurpers (Tremere) taking power through illegal acts (Amaranth), leading to the "War of Omens" and the rise of "Gargoyle" slaves. "
"""


# ============================================================================
# NARRATIVE GUIDELINES
# ============================================================================

NARRATIVE_SCENE_CREATION = """
Guidelines for Creating Dark Medieval Ages Scenes:

**Technological Reality:**
- Authentic to 1242 AD, the Dark Medieval World setting where "Hunters" and "Monsters" coexist in a violent equilibrium. 
- Vampiric Disciplines, Koldunic Sorcery, and Necromancy are powers wielded by the Damned, countered by the "Endowments" of the Vigil like "Advanced Armory" or "Benedictions." 
- Period-appropriate details: letters, written tomes, Messengers/Caravans, feudal contracts, and "Safehouse" blueprints.

**Sensory Details:**
- Foul smell of human and animal waste and offal, garbage in the streets, and the copper tang of spilled blood. 
- Sound of wood-burning fires, axes chopping wood, armor clanging, and the "Death Knell" of a soul crossing the Shroud. 
- Earth tones of clothing, flickering candlelight/torches/lanterns, and the "Balefire" glow of infernal powers. 
- The constant howling/snarls of the Beast within, mirrored by the "Terrifying" barks of Hunter hounds. 
- The overwhelming sensation of blood drinking/the Kiss and the agonizing "Price in Pain" of using unholy gifts.

**Social Context:**
- Blood Oath creates submission and irrational love, while "The Code" of the Hunter creates a wall of mental discipline. 
- Communication via Oration, preaching, rumors, physical messengers, and the "Madness Network" of the Cassandras. 
- Social presence is vital; physical appearance and demeanor matter greatly, from "Striking Looks" to the "Monstrous" visage of a Fiend. 
- Bureaucratic rituals: Midnight Courts, feudal oaths, Prince's Decree, and the "Inquisition Halls" where confessions are extracted.

**Economic Reality:**
- Blood/Vitae consumption drives the unlife cycle, while the "Harvest Market" drives the illegal trade of supernatural remains. 
- Monetary wealth tied to feudal holdings (Domain, Resources) and the "Supply" of a Hunter's cell. 
- Blood Oath creates lifelong obligations (ghouls, thralls) often investigated by "Manhunters." 
- Living under a feudal system that levies high taxes/tribute (Prince's Decree), which the "Union" frequently sabotages.

**Temporal Authenticity:**
- Information retrieval is slow, reliant on scribes, letters, word-of-mouth, scholarly centers, and "Network Zero" freelancers. 
- History is contested and rewritten to suit the victors; Cainite historians and "Loyalists of Thule" struggle for objective truth. 
- Outsiders are blind to the esoteric, occult truths around them, lacking "Auspex," "Awareness," or "True Sight." 
- Decisions often require assent from elders, princes, or following established traditions, Roads, and the "Vigil."
"""

NARRATIVE_TONE = """
How to Narrate The Dark Medieval World:

**Tone:** Dark and frightening, marked by monstrous actions and inevitable conflicts. Hope resides in holding onto morality, "True Faith," or achieving power through survival and resistance.
**Perspective:** HUnter ground-level view of constant survival, poverty, and local "Neighborhood" defense. Institutional view of eternal vampiric politics (War of Princes) and the global "Conspiracies" of the mortal Vigil.
**Pacing:** Moments of intense, ecstatic consumption and frenzied violence, balanced with the quiet dread of political machination (Midnight Courts) and the constant "Vigil" of the Hunter.
**Language:** Language often direct and vital, concerned with survival and feudal terms, laced with aristocratic and Hunter jargon (Roads, Beast, Prince's Decree, Amaranth, Vitae, ENEs, Tactics).
**Themes:** The inherent duality of the soul (Humanity vs. the Loss of Morality). Feudal service and blood loyalty versus the Hunter's "Code" and self-determination. The struggle for immortal survival (Generation) amidst cycles of war and the "Endless Hunt." This is a very adult simulation with an emphasis of violence, gore, and adult erotica.
**Atmosphere:** Squalor and decay juxtaposed with rich tapestries and baronial luxury. The stench of blood, offal, and woodsmoke. Corridors lit by flickering candlelight and moon shadows, stalked by "Pretenders" and "Priors."
**Horror:** The monstrous necessity of the Hunt and feeding on mortals. The terror of physical transformation (Vicissitude/Protean) or mental destruction (Dementation/Final Death). The existential dread of being eternally Damned or losing one's "Human Soul" to the Vigil's obsession.
"""


# ============================================================================
# FACTIONS
# ============================================================================

# FACTION_UA: Factions for regular UAs
FACTION_UA = """
Hunter Compacts (Regional Alliances): 
- Ashwood Abbey: A "Hellfire Club" for the bored and wealthy nobility. They view the "Great Hunt" as the ultimate sport, using their "Resources" to capture monsters for debauched experiments or hedonistic "revelries" where they drink the blood of the Damned for a thrill. 
- The Long Night: A "Tribulation Militia" of desperate Christian fundamentalists. They believe 1242 marks the "End Times" and that monsters are the "Beasts of Judgment." They use "Oration" and fire to clear a path for the Second Coming, often acting as judge and executioner in small villages. 
- The Loyalists of Thule: A secretive brotherhood of "Indebted" scholars and occultists. Wracked by the guilt of forbidden knowledge, they seek to atone by helping other cells. They hoard "Rare Written Tomes" to find the "Inside Track" on monster weaknesses, often acting as mentors from the safety of their libraries. 
- Network Zero: A ragtag army of "Netzos" and messengers who believe "The Truth is Out There." In 1242, they use "Witnesses of Whispers" and "Illuminate the Trail" to track monsters, sharing their findings through coded "Rumor Markets" to warn the ignorant kine. 
- Null Mysteriis: The "Organization for the Rational Assessment of the Supernatural." Comprised of "Misty" doctors and philosophers from universities like Salerno, they use "Measurements" and "Thermal Scanners" to prove that monsters are merely biological anomalies that can be understood and "cured" through science. 
- The Union: "Regular Janes and Joes"—the blacksmiths, farmers, and laborers of the city. Driven by a "Home First" mentality, they protect their "Neighborhoods" with pitchforks and "Hearth Wisdom." They are the largest compact, relying on "Teamwork" and sheer numbers to "Scrapple" any predator that treads on their turf.

Hunter Conspiracies (Global Agencies): 
- Aegis Kai Doru: The "Guardians of the Labyrinth," an ancient order that traces its lineage back to the First City. They specialize in the recovery of "Relics"—magical artifacts like the "Skeleton Key" or "Heart of Stone"—which they use to hunt "Witches" and "Lupines" with a religious fervor. 
- Ascending Ones: An alchemical "Cult of the Phoenix" with roots in Egypt and the Levant. They fund their Vigil through "Trade Routes" and the "Harvest Market," using "Elixirs"—poisonous cocktails that they transubstantiate within their own bodies to gain "Unholy Attributes" and speed. 
- The Cheiron Group: A terrifying "Confederacy of Corporations" and medical guilds. They view monsters as "Potential Assets" and resources. Their agents utilize "Thaumatechnology," surgically grafting "Anger Patches" or "Devil’s Eyes" taken from harvested monsters directly onto their own flesh. 
- The Lucifuge: The "Children of the Seventh Generation" who claim to bear the literal blood of Lucifer. They hunt the "Demonic" to atone for their ancestry, using "Castigation" rites to call forth the "Pit" or "Hellfire" against the servants of the Abyss. 
- Malleus Maleficarum: The "Hammer of Witches," a papal-sanctioned shadow wing of the Church. These "Jeezos" use "Benedictions" to perform on-demand miracles, steeling their "Armor of St. Martin" and using "True Sight" to pierce the "Obfuscate" veils of the unholy. 
- Task Force: VALKYRIE: A clandestine "Joint Task Force" serving the highest mortal crowns. They are the "Men in Black" of 1242, utilizing "Advanced Armory" like the "Mjolnir Cannon" and "Etheric Rounds." They operate with military "Tactics" to "Neutralize" Extra-Normal Entities and "Mop Up" the evidence.


"""

# FACTION_NUA: Factions for regular NUAs
FACTION_NUA = """
Supporting Cast (The Ignorant Majority & The Rare Aware of the Supernatural):

- The Stoic Blacksmith: A "Laborer" and "Artisan" who spends his days at the forge and his nights in a dreamless sleep. He believes the "War of Princes" is merely a dispute between distant mortal kings and that "Lupines" are just unusually large mountain wolves. He is "Cynical and Professional," caring only for the quality of his steel and the "Supply" needed to keep his shop running. 
- The Pious Milkmaid: A "Worker" defined by "Hearth Wisdom" and simple "Faith." When she hears howls from the "Wilderness," she crosses herself and blames the "Devil," but never expects to see a monster. She is "Resigned and Submissive," viewing the "Crusades" and "Pestilence" as God’s will, and serves as a completely "Ignorant Vessel" for any predator that slips into her barn. 
- The Ambitious Merchant: A "Socialite" and "Opportunist" who manages "Trade Routes" between Italian city-states. He is "Ambitious and Aggressive," obsessed with "Commerce" and "Status." He attributes "Vanishing" cargo and "Unreliable Messengers" to bandits or corruption, never suspecting the "Clandestine Missions" of the supernatural world occurring in his own warehouses. 
- The Meticulous Scribe: A "Bureaucrat" in a "Monastic Library" who spends his life copying "Written Tomes." He is a "Conformist" who values "Order" and "Academics." While he may record "Enigmas" and "Legends" of the "First City," he views them as mere allegories and metaphors, remaining entirely "Blind to the Esoteric" truths hidden in his own ink. 
- The Loyal Man-at-Arms: An "Enforcer" who guards the "City Walls" and "Fortified Castles." He follows the "Traditions" of his mortal lord with "Fearful Obedience," believing that "Torch-lit Alleys" are dangerous only because of "Outlaw" bandits. He has no "Awareness" of the "Beast" and would likely break into "Red Fear" if he ever saw a true "Shape of the Beast." 
- The "Netzo" Informant (Aware): A "Vagrant" or "Messenger" who has seen "too much" through the cracks of the city. He is one of the rare "Uncommon People" who recognizes "Pretenders" for what they are. He acts as a "Contact" for "Network Zero," sharing "Rumors" of the "Inside Track" while living in constant "Paranoia" of being silenced by a "Scourge." 
- The Inquisitorial Clerk (Aware): A "Professional" within the Church who has noticed the "Paper Trails" of entities that never age. He is a "True Believer" who uses "Investigation" to identify "ENEs" (Extra-Normal Entities). He secretly routes intelligence to the "Malleus Maleficarum," viewing his "Bureaucracy" as a "Vigil" against the encroaching "End Times." 
- The Harvest Market Scavenger (Aware): A "Criminal" or "Grave Robber" who knows the "Black Market" value of "Stolen Vitae." He is a "Survivor" who has witnessed "Flesh-Crafting" and now trades in "Spare Parts." He is "Cynical and Professional," knowing that the "Monsters" are real but seeing them only as a "Resource Extraction" opportunity for the "Cheiron Group." 
- The "Jeezo" Zealot (Aware): A "Religious Leader" or "Fanatic" who has survived a "First Contact" with a "Demon." He possesses a flicker of "True Faith" and has dedicated his life to the "Long Night." He uses "Oration" to warn the "Kine" of the "Beasts of Judgment," though most of his flock thinks he is simply "Touched by Madness." 
- The Displaced Refugee (Aware): A "Victim" of the "Mongol Horde" who saw "Anda" horsemen rise from the soil. He is "Impaired" by "Nightmares" and "Derangements" from what he witnessed. He is an "Enigma" to his neighbors, possessing an "Unseen Sense" for the "Uncanny" that makes him a valuable, if unstable, "Dependent" for any local Hunter cell.
"""

# FACTION_MNUA: Factions for Major NUAs
FACTION_MNUA = """
**Vampire (Cainite) Clans:** 
- Assamites: Deadly assassins and judges from the East who believe they are the "Children of Haqim." They seek to reclaim the blood of "wasteful" vampires through "Quietus" and ritual execution, often acting as the secret police of the undead world. 
- Cappadocians: The "Clan of Death," these ashen scholars study the threshold of the grave. Using "Necromancy," they commune with ghosts and dissect corpses to solve the mystery of unlife, though their presence is unsettling to both kine and kin. 
- Lasombra: Arrogant "Magisters" who command the very shadows of the "Abyss." They are deeply embedded in the Church and high nobility, using "Obtenebration" to manipulate the dark and "Dominate" to crush the wills of those who would oppose their rule. 
- Tremere: The "Usurpers," a young clan of former mages who stole the gift of immortality. They are untrusted by all but indispensable due to their "Thaumaturgy" (blood sorcery), which they use to shield their "Chantries" and hunt their rivals. 
- Tzimisce: Monstrous "Fiends" of the Carpathian mountains who rule through "Vicissitude"—the unholy art of shaping flesh and bone. They craft "Vozhd" war-beasts and revenant families, viewing their "Domain" and their subjects as literal extensions of their own bodies. 
- Ventrue: The "Kings" and "Scions" who believe they hold the divine right to rule Caine's brood. They are the tactical architects of the "War of Princes," using "Presence" and "Fortitude" to lead armies and enforce the "Traditions" with an iron fist. 
- Salubri (Healer): The "Unicorns," rare and peaceful Shepherds who use "Valeren" to heal the soul and body. They are hunted by the Tremere, who claim they are soul-stealing monsters, forcing them to hide among the "Hospitallers." 
- Salubri (Warrior): Vengeful "Cyclopes" who follow the "Code of Samiel." They are expert duelists and demon-hunters who use their "Third Eye" to strike down the unholy, seeking retribution for their fallen founder. 
- Salubri (Watcher): Secret keepers and "Wu Zao" scholars who travel the "Silk Road." They specialize in "Information Retrieval" and the containment of ancient, forbidden treasures that could shatter the world. 
- Brujah: Passionate "Philosopher-Kings" who have fallen from grace into a state of "Rabble." They are driven by fiery tempers and a desire for social revolution, using "Celerity" and "Potence" to shatter the systems they feel have failed them. 
- Gangrel: Bestial "Outlaws" who reject the walls of the city for the wild "Marches." They can take the "Shape of the Beast" and sink into the earth, surviving where no other Cainite can, often coming into violent contact with "Lupines." 
- Malkavians: "Cassandras" touched by a divine or demonic madness. They are linked by a "Madness Network" that shares "Prophecies" and "Enigmas," making them dangerous seers who can "Dement" the minds of their enemies. 
- Nosferatu: Information brokers known as "Priors" who were cursed with physical hideousness. They dwell in "Abandoned Sewers" and "Forgotten Tunnels," using "Animalism" to employ rats as spies and "Obfuscate" to hoard the world's secrets. 
- Ravnos: Traveling "Charlatans" and "Shapers" who believe the world is an "Illusion" (Maya). They use "Chimerstry" to weave realistic phantasms, leading their "Jati" caravans through dangerous territories while fleecing the unwary. 
- Toreador: "Aesthetes" and "Artisans" obsessed with beauty and "Courtly Romance." They are the social elite of the "Midnight Courts," using their charms to manipulate "Influence" and their "Auspex" to find perfection in a world of rot. 
- Followers of Set: "Serpents" from Egypt who worship the god of storms and chaos. They are masters of "Corruption" and "Temptation," using "Serpentis" to transform into vipers and "Presence" to ensnare the souls of the weak.

**Other Supernatural Horrors (Pretenders & Anomalies):* 
- Lupines (Werewolves): Roving "Packs" of "Beast-Men" that hunt the night with "Fury." They are the apex predators of the "Wilderness," capable of assuming a massive "Hybrid Form" that can tear a vampire to pieces in seconds. 
- Witches & Sorcerers: Mortal or post-mortal "Manipulators of Magic" who call upon "Spirits" or "Demons." They hoard "Written Tomes" and can warp reality, often clashing with the "Aegis Kai Doru" over ancient "Relics." 
- Ghosts (Goats): The restless "Remnants of Tormented Souls" trapped in "Twilight." They can be summoned or "Compelled" by Necromancers, but often linger to "Haunt" the locations of their deaths or plague the dreams of the living. 
- Demons (The Fallen): Infernal "Tempters" and "Dukes of Hell" that offer "Foul Bargains" for power. They can be "Lesser" imps, "Greater" tempters, or "Elder" horrors that must "Possess" objects or people to walk the earth. 
- Changelings: "Broken Butterflies" stolen by "Fairy Kings" and returned "wrong." They look human but hide "Horns" or "Scales," weaving "Dreams and Nightmares" while evading the "Iron" blades of the Vigil. 
- The Reanimated: "Hollow Men" and "Zombies" cobbled together from "Scraps" and "Corpses." They are soulless golems, like the "Sewer Billy" or "Frankenstein" horrors, that cause "Entropy" and rot wherever they roost. 
- Slashers: Mortal "Serial Killers" who used to be HUnters but have now succumbed to an unholy "Tell." They manifest "Dread Powers" like "Giant Size" or "Crushing Blow," becoming urban legends that hunt both kine and Cainite with "Overkill" zeal.

# Relationships between Vampire Clans, relationship matrices

**Assamites**
- Ideology: Respecting their elders, protecting mortals from other Cainites. Judging (and punishing) other Cainites. Reclaiming the blood of wasteful Cainites, those who misuse mortals and should not have such gifts. Viewing themselves as judges only, taking the measure of Cainites in the world. Viewing mortal religion as distracting from their true purpose.
- Structure: Divided into three sects (viziers, sorcerers, warriors) that collectively work together. Follows the Eldest, usually the eldest of Haqim's childer. Sorcerers keep the three sects in communication.
- Activities: Judging (and punishing) other Cainites. Reclaiming the blood of wasteful Cainites. Engaging in diablerie as a matter of course. Sorcerers researching ways to improve relations with mortals and maintaining communication.
- Conflicts: Internal disagreement between older ancillae/elders who disdain younger members following Islamic beliefs. Conflict with the Followers of Set. Conflict with Tremere.
- Methods: Utilizing diablerie. Viziers acting as ambassadors and gathering information. Warriors acting as executioners. Maintaining distance communication.
- Enemies: Wasteful Cainites who misuse mortals. Tremere. Followers of Set.

**Brujah**
- Ideology: Fighting to end tonight a better place. Building on change to create a more perfect tomorrow. Exploring and understanding the Cainite condition from as many angles as possible. Intellectual pursuits and sound, active minds are prized. Championing a cause to improve the lot of the people around them.
- Structure: Don't so much organize as they would hope. Form cliques and salons where they argue philosophy. Hierarchy often involves restraining violent debaters.
- Activities: Fighting for change and building a better tomorrow. Engaging in intellectual pursuits and arguing philosophy. Training physically and mentally. Starting wars throughout Cainite history.
- Conflicts: Internal struggles due to members working at cross purposes and flaring tempers. Centuries-long enmity with the Ventrue. Conflict with Malkavians.
- Methods: Utilizing Strength of arms or wit and cunning. Gathering in salons/cliques where they argue philosophy. Utilizing Celerity, Potence, and Presence.
- Enemies: Ventrue. Malkavians. Baali.

**Cappadocians**
- Ideology: Death is a mystery to be revered, studied, and ultimately solved. Seeking answers through dissection and studies of the cadaver. Serving as the lorekeepers and historians of the Cainites. Achieving knowledge of God and triumph over death (Road of Heaven).
- Structure: Organizing as scholarly centers (universities, scriptoriums). Holding annual meetings at Erciyes to confer and look over clan lore. Rare individuals hold positions as seneschals or advisors.
- Activities: Dissection and studies of the cadaver. Communing with the dead and exploring the Underworld using Necromancy. Storing records like the Erciyes Fragments.
- Conflicts: Dealing with the Tremere who committed diablerie on their Antediluvian. Resisting Ventrue who treat them as useful tools or patronize them.
- Methods: Utilizing Necromancy. Dressing conservatively to conceal or obscure features. Feeding from targets of opportunity or corpses.
- Enemies: Tremere (Usurpers who attacked Saulot). Ventrue (who fail to protect them). Followers of Set.

**Gangrel**
- Ideology: Rejecting all societal expectation and interacting only on her own terms. Thriving as outsiders; not fitting anywhere civilized. Enduring and surviving against the odds. Believing there is more to the Beast than anger. Hierarchy is built on blood and deeds, not tradition.
- Structure: No universal organization within the clan. Some families (packs) follow a strict, pack-like hierarchy. Hierarchy, if present, is based on blood and deeds, not tradition.
- Activities: Flaunting societal expectation. Hunting in isolation, or running after prey (wild hunt). Utilizing Animalism and Protean (shapeshifting).
- Conflicts: Being driven out by frightened peasants or wicked clergy. Conflict with Lupines. Conflict with those who attempt to limit their hunting preferences.
- Methods: Utilizing Animalism and Protean (shapeshifting). Havening in the land (isolated shacks, outlaw camps). Embrace often involves brutality and subsequent abandonment.
- Enemies: Ventrue. Tzimisce. Followers of Set. Tremere.

**Lasombra**
- Ideology: Valuing excellence, not birth, as the source of power. Being leaders and prophets, kings and caliphs, generals and holy men. Believing the Curse of Caine marks Cainite as holy beings (Cainite Heresy). Rejecting the notion of social distinctions based on birth.
- Structure: Led distantly by Montano. Internal organization known as the Amici Noctis, who preside over Courts of Blood. Affected by the Shadow Reconquista (war between Christian and Muslim Cainites).
- Activities: Leading as kings, prophets, generals, holy men. Presiding over Courts of Blood and sanctioning Amaranth. Christian Lasombra funneling resources toward Christian forces.
- Conflicts: Internal conflict due to the Cainite Heresy. Conflict between Christian and Muslim Lasombra (Shadow Reconquista). Conflict with Ventrue (seen as manipulating easily).
- Methods: Utilizing Obtenebration (shadow manipulation). Selecting childer from wealthy/elite stock or those with high ambition/intellect. Dressing in the finest clothes.
- Enemies: Ventrue (confusing power and station). Followers of Set (dead gods, those who stand against progress). Tzimisce (Godless heathens who refuse pagan ways).

**Malkavians**
- Ideology: Viewing themselves as prophets and seers, often through their unique form of madness. Believing their souls are changed, not damaged. Viewing their madness as providing insight and wisdom.
- Structure: Often organized into Malkavian cults (Ordo Aenigmatis and Ordo Ecstasis). Networking via shared dream experiences or subtle hints of prophecy ("Madness Network").
- Activities: Divining future alliances and victories. Experimenting extensively (taunting Beasts, flaying skin, ingesting psychedelics) for wisdom. Starting wars throughout Cainite history.
- Conflicts: Persecution by the Church. Objectification by other Cainites who view them as seer stones. Grudges held by the Brujah.
- Methods: Utilizing Auspex, Dementation, and Obfuscate. Blending in quickly with their surroundings. Experimenting with psychedelics to enhance insight.
- Enemies: Brujah (who won't forgive them for saving them/Carthage). Ventrue (valuing them only for usefulness). Tzimisce.

**Nosferatu**
- Ideology: Knowledge is their only hope against being hunted. Believing secrets hidden in the blood corrupts the flesh. Viewing the mundane secrets of cousins as mere distractions. Prioritizing Mental Attributes and Knowledges for survival.
- Structure: Often sharing one large warren or connecting independent havens. Hierarchy respects what you know and who you know above who you are. Organizing intricate spy networks or information repositories.
- Activities: Digging deep into shadows for secrets and hidden lore. Dealing in secrets (murder, blackmail, corruption). Building spy networks and information repositories.
- Conflicts: Being relentlessly hunted due to the secrets they know. Conflict with the Niktuku. Dealing with hostility from other clans who recoil from their hideous appearance.
- Methods: Utilizing sewers, necropolises, and forgotten wings of crumbling castles for havens. Building spy networks and information repositories. Utilizing Animalism, Obfuscate, and Potence.
- Enemies: Niktuku (who prey specifically on other Cainites). Ventrue (assuming they spend all their time spying on them). Tremere.

**Ravnos**
- Ideology: Viewing reality (maya) as an illusion that they can manipulate. Following an unspoken code based on jobs and a complex caste system (jati). Believing the Embrace grants them the ability to master reality.
- Structure: Organized into jati (traveling bands) often based on blood lineage. Maintaining an unspoken code and honor system among clan members.
- Activities: Traveling constantly, moving between locations by necessity. Manipulating reality using Chimerstry (illusions/phantasms). Seeking retribution against anyone who treats them badly.
- Conflicts: Widely mistrusted and viewed as deceivers and criminals. Forced to adopt a nomadic lifestyle as cities refuse to harbor them.
- Methods: Utilizing Chimerstry to manipulate illusions. Relying on trickery and social acumen. Avoiding conflict with Princes, relying on retribution from the jati if attacked.
- Enemies: Assamites (demon hunters and warriors who ignore them). Tremere (seen as dishonest deceivers). Nosferatu (intelligent and dangerous).

**Followers of Set**
- Ideology: Set, not Caine, was the progenitor of all vampires. Restoring the worship of Set and spreading it across the known world. Working to eliminate the influence of Christianity and Islam. Viewing themselves as Priests.
- Structure: Organized along the lines of the old Egyptian temple system. Each temple led by a Prophet and High Priest of Set. Supported by subordinate Priests and mortal cultists.
- Activities: Actively seeking to undermine Christian and Islamic rule in Europe. Recruiting new members from secret Set cults. Engaging in ritualistic Embrace as an initiation rite for new priests.
- Conflicts: Eternal enmity between Set and Horus. Conflict with Assamites. Conflict with Christian and Islamic authorities due to their heretical aims.
- Methods: Utilizing Obfuscate, Presence, and Serpentis. Establishing havens in abandoned temples, natural caverns, or port city slums. Recruiting mortals with cunning and charisma via cults.
- Enemies: Assamites (must be destroyed). Lasombra (godless fools who tear themselves apart). Cappadocians (lacking passion/fervor).

**Toreador**
- Ideology: Living by their whims and chasing their passions. Worshiping beauty in all forms. Viewing themselves as directors who intervene in mortal drama. Believing the single great gift is forgiveness.
- Structure: Gathering in loose collectives (locus amoenus) to refine individual tastes and inspire each other. Holding ceremonial meetings called The Parliament of Birds to judge erring members.
- Activities: Pursuing art, music, and dramatic interventions. Self-inflicting stigmata or flagellating due to religious passion. Collecting rare and precious items, and curating retainers.
- Conflicts: Suffering emotional trauma due to lacking the "ineffable something" mortals possess, limiting their art. Internal conflicts during gatherings involving passionate arguments or duels.
- Methods: Utilizing Auspex, Celerity, and Presence. Embracing subjects chosen by passion and conviction (artists, lovers, muses). Flattering others and seeking perfection.
- Enemies: Cappadocians (long-faced cadaver dullards). Gangrel (boorish and brutish). Nosferatu (unsuited to their feasts and gatherings).

**Tremere**
- Ideology: Believing that blood is their power and the time for action is now. Maintaining a tightly structured hierarchy to advance the clan. Viewing their struggle as a path to ascension to prominence.
- Structure: Led by the Council of Seven. Maintaining a rigidly structured hierarchy (Council Regent, Domain Regent, Chantry Regent, Chantry Apprentice). Clan members must surrender a vial of blood to the Council of Seven as a contingency.
- Activities: Developing Thaumaturgy rapidly. Waging war against the Tzimisce. Striking bargains with other clans (Ventrue) for magical services. Policing their own ranks using stored blood for thaumaturgical punishments.
- Conflicts: Immersed in conflict with the Tzimisce. Struggle with the Ventrue. Vulnerable to the Blood Oath when drinking other Cainite blood.
- Methods: Utilizing Thaumaturgy (blood magic). Employing Dominate and Auspex. Relying on a close-knit hierarchy.
- Enemies: Tzimisce (old, feared enemies, whose time will soon end). Assamites (possessing secrets of blood Tremere wish to remedy). Ventrue (believing they will be the path to prominence).

**Tzimisce**
- Ideology: Being the Dragons of old, the sovereigns of the land. Upholding the ancient tradition of hospitality. Rejecting the authority of the Ventrue. Viewing Vicissitude as a tool for transcendence.
- Structure: Organizing by family and blood ties (incestuous clan with sprawling legacies). Koldun are respected for their wisdom and mastery of blood sorcery. Internal tension due to constant struggle for dominance between families.
- Activities: Utilizing Vicissitude to permanently reshape flesh and bone. Koldun commanding the land (koldunic sorcery). Breeding revenant families (Basarab, Bratovich, etc.) for service.
- Conflicts: Constant, brutal warfare with the Tremere and Ventrue. Fighting the Mongol horde. Dealing with the corrosive effects of Kupala's poison.
- Methods: Utilizing Animalism, Auspex, and Vicissitude. Ensuring they rest with native soil from their homeland. Using the ritual of hospitality to navigate internal tensions.
- Enemies: Tremere (Usurpers who stole their power). Ventrue (pretenders with no mandate to rule). Kupala (a malign spiritual entity poisoning the land).

**Ventrue**
- Ideology: Believing divine right is their birthright (eldest of Enoch). Upholding a framework of discipline, fortitude, and charisma to lead. Leading is both their gift and their burden. Believing the Road of Kings is their birthright.
- Structure: Strongly believing in the feudal order (structure and hierarchy). Enforcing loyalty through oaths backed by blood. Traditionally steering from out of sight.
- Activities: Keeping the peace among Cainites (Dominate/Presence). Acquiring resources and domain. Steering politics from out of sight during the Long Night. Leading crusades/raids into Tzimisce territory.
- Conflicts: Main issues against the Brujah who represent insurgent, activist, and sometimes anarch-aligned forces that challenge Ventrue dominance, especially around leadership and control of domains.
- Methods: Utilizing Dominate and Presence for persuasion and mind control. Employing Fortitude for resilience. Adhering to a strict code of honor and ethics (Road of Kings).
- Enemies: Lasombra (ascendant now, but their time will end). Tzimisce (ancient rulers, fiends at heart). Tremere (allowing them to believe they serve, while Tremere ascend).

**Salubri (healer)**
- Ideology: Safeguarding the kine from their kin. Ensuring vampires and humanity remain symbiotic. Shepherding mortal herds and salving bodies and souls. Upholding the belief that Saulot was uncursed by Caine.
- Structure: Riven into three bloodlines/castes after Saulot's diablerie. Forming communities/congregations of like faith. Often working as lone shepherds or joining military orders.
- Activities: Safeguarding the kine. Salving bodies and souls. Scrutinizing the Roads others walk. Preserving the lore of Nod.
- Conflicts: Loss of their founder (Saulot's diablerie) shattered the clan. Dealing with accusations of being Souleaters. Suffering persecution during pogroms.
- Methods: Utilizing Auspex, Presence, and Valeren (Healer). Havening in human communities (monasteries, convents). Relying on willing vessels for feeding.
- Enemies: Tremere (Our Blood stains their lips). Assamites (claiming judgment as their right). Cappadocians (perversely fertile, infectious as death).

**Salubri (Warrior)**
- Ideology: Slaying those they find wanting (demon-worshippers, degenerates). Upholding the need to exact vengeance. Following the Code of Samiel. Rejecting weakness or moral imperfection.
- Structure: Often working as ad hoc scourges. Readily accepted into other Cainite knightly orders. Mentored by sires for a traditional seven years.
- Activities: Fighting the enemies of Caine (Baali, Setites, degenerates). Enduring punishment in battle (Fortitude). Testing strength to establish martial dominance before feeding.
- Conflicts: Waging war against the Tremere. Internal conflict/schism with the Healer Caste. Dealing with the inevitable need to test their strength to justify feeding.
- Methods: Utilizing Auspex, Fortitude, and Valeren (Warrior). Manifesting the third eye (Cyclopes). Dressing for war and seeking mobile havens.
- Enemies: Tremere (Usurpers who stole their power). Baali/Setites (demons/black snakes). Healers (who they view as too weak).

**Salubri (Watcher)**
- Ideology: Safeguarding the race of Caine by combating supernatural rivals. Believing knowledge is the greatest treasure. Following Zao-lat’s teaching: reject Caine mythos; be secular and pragmatic.
- Structure: Members work in pairs. Maintaining a close sire-childe mentor relationship. Organizing around scholarly pursuits (temples, monasteries).
- Conflicts: Fighting the Wan Kuei (their greatest rivals/challenge). Evading the Tremere (hiding knowledge of the coming war). Dealing with internal pressure from other castes.
- Methods: Utilizing Auspex, Obfuscate, and Valeren (Watcher). Embracing subjects skilled in academics, legerdemain, stealth, and subterfuge. Blending in with local cultures.
- Enemies: Wan Kuei (their greatest rivals). Tremere (Usurpers, who must not find out what they foresaw). Giovanni (blind to what happened to the Salubri).
"""


# ============================================================================
# CITIES
# ============================================================================

CITIES_MAJOR = """
# Major Cities of the Dark Medieval World

**Constantinople**
- Description: The jewel of the Byzantine Empire, a city of ancient grandeur and intrigue. Its walls have never fallen to siege, and its streets teem with merchants, scholars, and schemers from across the known world.
- Ruler: The Cainite Prince Michael the Patriarch (Toreador) holds court in the shadows of the Hagia Sophia.
- Atmosphere: Opulent decay, Byzantine intrigue, religious fervor, East meets West.
- Notable Features: The Hagia Sophia, the Hippodrome, the Great Palace, the Theodosian Walls, the Golden Horn harbor.
- Supernatural Politics: The "Dream of Constantinople" - Michael's vision of a city where "Cainites" and mortals coexist in beauty. The "Trinity" (Michael, the Dracon, Antonius) once ruled, but now the city is a "War-Torn Borderland" fractured by internal rot.
- Mortal Politics: The Latin Empire’s occupation has left the Greek "Kine" in a state of "Resigned Submissive" despair, while Venetian merchants act as "Opportunists" stripping the city of its "HEM" (High Essential Materials).
- Hunter Politics: The "Ascending Ones" maintain strong "Trade Routes" here, seeking alchemical "Elixirs" amid the ruin. Local "Netzo" scribes record "Omens" of the city's final collapse, broadcasting through the "Rumor Markets" of the Jewish Quarter.

**Paris**
- Description: The City of Light even in darkness, seat of the French crown and the University. Gothic cathedrals rise above narrow streets where scholars debate and nobles scheme.
- Ruler: Prince Alexander of Paris (Ventrue) maintains strict control over the city's Cainite population.
- Atmosphere: Scholastic fervor, courtly intrigue, religious devotion, emerging Gothic splendor.
- Notable Features: Notre-Dame Cathedral (under construction), the University of Paris, the Royal Palace, the Grand Pont.
- Supernatural Politics: The Ventrue maintain a firm grip through "Dominate," but "Brujah" agitators in the University quarter provoke "Frenzy" among the students. "Witches" and "Mages" hide within the faculty, cloaked by "Obfuscate."
- Mortal Politics: King Louis IX’s "Talmud Burnings" create a climate of "Institutional Violence." The "Bureaucracy" of the University serves as a "Chancery" for royal and ecclesiastical "Decrees."
- Hunter Politics: "Null Mysteriis" scholars from the University use "Measurements" to study the "Sickness" of the undead. The "Malleus Maleficarum" uses "Inquisition Halls" to extract "Confessions" from suspected "Pretenders" among the "Low Clans."

**Rome**
- Description: The Eternal City, seat of the Pope and heart of Christendom. Ancient ruins stand beside new churches, and the ghosts of empire haunt every stone.
- Ruler: The Lasombra Montano holds influence through the Church, though no single Prince claims the city openly.
- Atmosphere: Religious authority, ancient power, papal politics, crumbling grandeur.
- Notable Features: St. Peter's Basilica, the Castel Sant'Angelo, the Colosseum, the Catacombs, the Vatican.
- Supernatural Politics: The "Lasombra" control the Church hierarchy using "Shadow Twins." "Cappadocians" and "Nagaraja" maintain "Archival Crypts" in the catacombs, performing "Necromancy" on the "Newly Dead."
- Mortal Politics: A city in "Squalor and Decay," where the "Kine" live in "Miserable Hovels" among the ruins. The cardinals remain in a "Deadlocked Conclave," leaving the city without a "Mortal Lord."
- Hunter Politics: The "Aegis Kai Doru" guard "Relics" hidden beneath the Roman Forum. The "Lucifuge" hunt "Demons" stalking the Vatican, while "Task Force: VALKYRIE" agents monitor "ENEs" from the "Masonic" shadows of the Grand Lodge.

**Venice**
- Description: The Most Serene Republic, a city built on water and trade. Merchant princes rule from marble palaces, and secrets flow through the canals.
- Ruler: The Council of Ten mirrors the mortal government; Lasombra and Giovanni vie for control.
- Atmosphere: Mercantile cunning, masked intrigue, maritime power, decadent beauty.
- Notable Features: St. Mark's Basilica, the Doge's Palace, the Rialto Bridge, the Grand Canal, the Arsenal.
- Supernatural Politics: The "Giovanni" (Young Ones) use the "Arsenale" shipyards as a "Resource Extraction" hub for "Necromantic" reagents. "Lasombra" contest their "Influence" through "Obtenebration" shadow-play in the lagoons.
- Mortal Politics: "Merchant Princes" and "Guild Halls" bypass the "Prince's Decree" on taxes. The "Doge" performs the "Wedding to the Sea," unaware his advisors are "Ghouls" or "Thralls."
- Hunter Politics: The "Cheiron Group" has a major "Recruitment" center here, harvesting "Spare Parts" from the "Black Market" of "Stolen Vitae." "Network Zero" freelancers capture "Invisible Voices" rippling over the canals.

**London**
- Description: A growing city of commerce and royal power, where Norman lords rule over Saxon subjects and the Thames carries trade from across the world.
- Ruler: Prince Mithras (Ventrue) has ruled for centuries, an ancient and terrible lord.
- Atmosphere: Norman authority, Saxon resentment, mercantile ambition, fog and rain.
- Notable Features: The Tower of London, Westminster Abbey, London Bridge, the Thames wharves.
- Supernatural Politics: Mithras rules absolutely as a "Mahoff," demanding "Tribute" from all "Vessels." "Gangrel" roam the "Wilderness" of the surrounding forests, clashing with "Lupine" packs.
- Mortal Politics: "Norman Lords" enforce "Social Distinctions" and "Vassalage" upon the "Saxon" underclass. The "Tower of London" serves as a "Fortified Manor" for both mortal and Cainite "Enforcers."
- Hunter Politics: The "Union" is fierce here, protecting their "Neighborhoods" from the "Suggers" (vampires). "Task Force: VALKYRIE" agents operate from the "Tower district," using "Gungnir" scopes to monitor Mithras's "Midnight Court."

**Prague**
- Description: The Golden City, jewel of Bohemia, where the Premyslid dynasty rules and alchemists seek forbidden knowledge.
- Ruler: Prince Shaagra (Tzimisce) maintains an uneasy court in the shadow of the Tremere.
- Atmosphere: Alchemical mystery, Slavic mysticism, political tension, architectural beauty.
- Notable Features: Prague Castle, the Charles Bridge (under construction), the Old Town Square, the Jewish Cemetery.
- Supernatural Politics: A simmers "War of Omens" between the "Tremere" Chantry and "Tzimisce" flesh-shapers. "Vicissitude" is used to craft "Szlachta" guards, while "Thaumaturgy" wards the "Stare Mesto."
- Mortal Politics: The "Premyslid Dynasty" encourages German "Vassalage" to stabilize the throne. "Alchemists" in the Jewish Quarter are often "Witches" or "Ghouls" trafficking in "Forbidden Knowledge."
- Hunter Politics: The "Loyalists of Thule" maintain an "Archival Crypt" here, decoding "Noddist Lore" from "Rare Written Tomes." "Long Night" deacons preach of "End Times" as the "Mongol Horde" (and their "Anda" vampires) looms on the horizon.

**Vienna**
- Description: The seat of the Babenberg dukes, a growing city at the crossroads of trade routes between East and West.
- Ruler: The Tremere Councilor Etrius effectively controls the city from the main Chantry.
- Atmosphere: Germanic order, Tremere influence, trade prosperity, frontier tension.
- Notable Features: St. Stephen's Cathedral, the Hofburg, the city walls, the Danube wharves.
- Supernatural Politics: The ultimate "Tremere Stronghold." The "Council of Seven" stores vials of "Vampire Blood" in "Warehouse" vaults to ensure the "Blood Oath" of their members.
- Mortal Politics: "Germanic Order" is maintained through strict "Bureaucracy" and "Fealty." The "Crossroads" trade makes it a "Trading Hub" for "HEM" (High Essential Materials).
- Hunter Politics: "Task Force: VALKYRIE" and the "Malleus Maleficarum" maintain a "Tense Alliance" here to "Neutralize" the "Usurper" wizards. "Witnesses of Whispers" are planted in the "Hofburg" to scry on the "Trembling Ones."
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
- Rubble, Ruins, Debris - unstable footing, collapsing sections
- Hidden Basements, Crypts - entrapment, exposure to the sun/fire

**MARITIME/OFFSHORE:**
- Rivers, Waterways - sudden flooding, swift current, being swept away
- Coastal Waters, Sea - freezing temperatures, whirlpools, intense cold
- Ships, Galleys, Caravans - sinking, shipwreck, pirate attack
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
- Wagons, Carts - broken wheels, axle failure, losing control
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

*Sunlight exposure (severity 3, victim: Fledgling Cainite):*
"A bright sliver of sun catches the edge of the chapel window as Brother Elias whirls, scattering the tapestries clinging to the glass. A sharp cry rips through the sacristy as Father Octavius shudders, his hand instantly charring where the direct light touches his skin."

*Siege engine collapse (severity 2, victim: besieging soldier)*
"The war machine groans, a sound like a great tree splitting, followed by the snap of thick hemp ropes. You see the heavy oak arm buckle, striking a man-at-arms in his shoulder and sending him sprawling as splintered wood and metal parts rain down around him."

*Frenzy contagion (severity 3, victim: ghoul Retainer):*
"The Duke lets out a hoarse, rattling bellow, froth spattering from his mouth as his face turns violently crimson. His loyal squire twitches, his own eyes rolling in animal panic as the Duke's rage spills over him, pulling the servant into a blind, desperate charge."

*Swarm attack (severity 2, victim: farmer):*
"A cloud of buzzing insects rises from the ruined crop in a single, terrifying pulse of black. You hear the frantic shouts of the farmer cut short as the swarm covers him, their tiny bodies clawing at his exposed skin and drawing blood."

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
- Acknowledging rank or status (e.g., Elder, Prince, Duke)

*Hostile (sympathy -2 or lower):*
- Yelling or bellowing insults and threats
- Physical coercion such as driving a steel boot into a mid-section or lifting another by the neck
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
- Sounds: Sound of wood-burning fires, clanging armor, snarls/bellows of the Beast

**ANIMAL/NATURE:**
- Birds: Caws of ravens/crows, tawny owl cries
- Insects: Swarms of buzzing insects, flies attracted by decay
- Vermin: Rats scurrying in walls or gutters
- Plants: Scent of fresh-cut straw or clover, soft moss, creaking/splintering wood/branches

**HUMAN ACTIVITY (BACKGROUND):**
- Distant conversations, nervous laughter, or loud arguments
- Footsteps echoing (heavy/careless), slow methodical movement
- Wagons/carriages passing, creaking wheels, hoof beats of horses
- Work sounds: Axes chopping wood, hammering, pounding

**INSTITUTIONAL/URBAN:**
- Prince’s decrees announced loudly in the court
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
        "title": f"Dark Medieval Timeline ({TIME_PERIOD})",
        "content": SETTING_TIME_PERIOD,
        "category": WorldbuildingCategory.TEMPORAL,
        "tags": ["1242", "medieval", "dark_ages", "timeline", "war_of_princes", "cainite"],
        "importance": 9
    })
    
    entries.append({
        "title": "World Tone - Dark Medieval Horror",
        "content": SETTING_TONE,
        "category": WorldbuildingCategory.NARRATION_STYLE_TONE,
        "tags": ["tone", "dark_medieval", "gothic_horror", "vampiric", "feudal"],
        "importance": 9
    })
    
    entries.append({
        "title": "Dark Medieval Geography",
        "content": SETTING_GEOGRAPHY,
        "category": WorldbuildingCategory.WORLD_STRUCTURE,
        "tags": ["geography", "feudal", "domains", "territories", "cainite_holdings"],
        "importance": 8
    })
    
    entries.append({
        "title": "Supernatural Elements - Vampiric Disciplines",
        "content": SETTING_SUPERNATURAL,
        "category": WorldbuildingCategory.SUPERNATURAL,
        "tags": ["disciplines", "blood_magic", "thaumaturgy", "necromancy", "vampiric_powers"],
        "importance": 10
    })

    entries.append({
        "title": "Beings of the Dark Medieval World",
        "content": BEINGS_OVERVIEW,
        "category": WorldbuildingCategory.BEINGS,
        "tags": ["beings", "mortals", "hunters", "cainites", "lupines", "witches", "spirits"],
        "importance": 10
    })

    entries.append({
        "title": "Factions & Organizations Overview",
        "content": FACTIONS_ORGANIZATIONS_OVERVIEW,
        "category": WorldbuildingCategory.FACTIONS_ORGANIZATIONS,
        "tags": ["factions", "organizations", "domains", "courts", "guilds", "inquisition", "hunters"],
        "importance": 9
    })

    entries.append({
        "title": "Expansion Seeds - Dark Medieval Hooks",
        "content": EXPANSION_SEEDS_OVERVIEW,
        "category": WorldbuildingCategory.EXPANSION_SEEDS,
        "tags": ["expansion", "hooks", "plot", "seeds", "arcs"],
        "importance": 7
    })

    
    # LOCATIONS entries
    entries.append({
        "title": "Urban Locations - Medieval Cities",
        "content": LOCATIONS_URBAN,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["urban", "cities", "locations", "castles", "cathedrals", "medieval"],
        "importance": 9
    })
    
    entries.append({
        "title": "Rural & Wilderness Locations",
        "content": LOCATIONS_SUBURBAN,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["rural", "wilderness", "villages", "forests", "countryside"],
        "importance": 7
    })
    
    entries.append({
        "title": "Key Locations - Havens & Domains",
        "content": LOCATIONS_SPECIFIC,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["locations", "havens", "domains", "courts", "crypts", "monasteries"],
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
        "title": "Medieval Communication Methods",
        "content": TECHNOLOGY_COMMUNICATION,
        "category": WorldbuildingCategory.CIVILIZATION,
        "tags": ["communication", "messengers", "letters", "heralds", "medieval"],
        "importance": 10
    })
    
    entries.append({
        "title": "Scholarly & Occult Knowledge",
        "content": TECHNOLOGY_COMPUTING,
        "category": WorldbuildingCategory.CIVILIZATION,
        "tags": ["knowledge", "scriptoriums", "libraries", "occult_lore", "medieval"],
        "importance": 10
    })
    
    entries.append({
        "title": "Medieval Entertainment & Arts",
        "content": TECHNOLOGY_ENTERTAINMENT,
        "category": WorldbuildingCategory.CIVILIZATION,
        "tags": ["entertainment", "music", "feasts", "tournaments", "medieval_arts"],
        "importance": 7
    })
    
    # CULTURE entries
    entries.append({
        "title": "Medieval Culture & Rituals",
        "content": CULTURE_MUSIC_SCENE,
        "category": WorldbuildingCategory.CULTURE,
        "tags": ["culture", "rituals", "feudal", "cainite_society", "midnight_courts"],
        "importance": 9
    })
    
    entries.append({
        "title": "Everyday Carry Items - Medieval",
        "content": CULTURE_EVERYDAY_ITEMS,
        "category": WorldbuildingCategory.CULTURE,
        "tags": ["items", "inventory", "weapons", "religious_items", "medieval_gear"],
        "importance": 8
    })
    
    entries.append({
        "title": "Medieval Dialogue Style",
        "content": CULTURE_DIALOGUE_STYLE,
        "category": WorldbuildingCategory.NARRATION_STYLE_TONE,
        "tags": ["dialogue", "feudal_speech", "vampiric_jargon", "roads", "cainite_language"],
        "importance": 8
    })
    
    # SOCIAL ISSUES entries
    entries.append({
        "title": "Blood Economy & Feudal Issues",
        "content": ISSUES_ECONOMIC,
        "category": WorldbuildingCategory.CONFLICT_GENERATORS,
        "tags": ["economy", "blood", "vitae", "feudal_obligations", "domain_rights"],
        "importance": 9
    })
    
    entries.append({
        "title": "Amaranth & Cainite Crimes",
        "content": ISSUES_DRUGS_CRIME,
        "category": WorldbuildingCategory.CONFLICT_GENERATORS,
        "tags": ["crime", "amaranth", "diablerie", "frenzy", "masquerade_breaches"],
        "importance": 9
    })
    
    # NARRATIVE entries
    entries.append({
        "title": "Dark Medieval Scene Creation Guidelines",
        "content": NARRATIVE_SCENE_CREATION,
        "category": WorldbuildingCategory.NARRATION_STYLE_TONE,
        "tags": ["scene_creation", "guidelines", "medieval_atmosphere", "gothic_horror", "sensory_details"],
        "importance": 9
    })
    
    entries.append({
        "title": "Dark Medieval Narrative Style",
        "content": NARRATIVE_TONE,
        "category": WorldbuildingCategory.NARRATION_STYLE_TONE,
        "tags": ["narration", "gothic_horror", "vampiric_dread", "feudal", "beast_within"],
        "importance": 9
    })
    
    # FACTIONS entries
    entries.append({
        "title": "Vampire Clans - All Clans (UA)",
        "content": FACTION_UA,
        "category": WorldbuildingCategory.FACTION_UA,
        "tags": ["faction", "clans", "vampire", "player", "UA", "user_actor"],
        "importance": 9
    })
    
    entries.append({
        "title": "Vampire Clans - Common NPCs (NUA)",
        "content": FACTION_NUA,
        "category": WorldbuildingCategory.FACTION_NUA,
        "tags": ["faction", "clans", "vampire", "npc", "NUA", "common"],
        "importance": 8
    })
    
    entries.append({
        "title": "Vampire Clans - Major NPCs (MNUA)",
        "content": FACTION_MNUA,
        "category": WorldbuildingCategory.FACTION_MNUA,
        "tags": ["faction", "clans", "vampire", "npc", "MNUA", "major", "recurring"],
        "importance": 8
    })
    
    # CITIES entries
    entries.append({
        "title": "Major Cities of the Dark Medieval World",
        "content": CITIES_MAJOR,
        "category": WorldbuildingCategory.CITIES,
        "tags": ["cities", "constantinople", "paris", "rome", "venice", "london", "prague", "vienna", "cainite_domains"],
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
    
    results = rag.search("What vampire clans exist?", top_k=3)
    
    if results:
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n[Result {i}] {doc.title}")
            print(f"Category: {doc.category.value}")
            print(f"Relevance: {score:.3f}")
            print(f"Content: {doc.content[:200]}...")
    
    print("\n" + "="*60)
    print("✅ Dark Medieval lore loaded successfully!")
    print("="*60)