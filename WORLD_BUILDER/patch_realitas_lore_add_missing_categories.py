import sys
from pathlib import Path


INSERT_BLOCK = """

BEINGS_OVERVIEW = \"\"\"
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
\"\"\"

FACTIONS_ORGANIZATIONS_OVERVIEW = \"\"\"
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
\"\"\"

EXPANSION_SEEDS_OVERVIEW = \"\"\"
Expansion Seeds (Future Hooks) for the Dark Medieval World (1242):

- A courier route collapses after a string of disappearances; the cell must discover whether the cause is bandits, Lupines, or a Cainite feeding ground.
- A monastery scriptorium burns, and a fragment of Noddist lore vanishes into the black market.
- An Inquisitor arrives with unfamiliar authority; their questions suggest a hidden patron.
- A minor Domain shifts hands overnight; rumors claim Amaranth, but no witness remains sane.
- A village offers sanctuary in exchange for protection from \"the howling\" beyond the treeline.
- A relic changes owners repeatedly within a week; each bearer suffers different omens.
- A faction fractures into rival splinters; the UA must choose alliances or exploit the chaos.

Core Rule for Simulation:
- Expansion seeds should generate grounded medieval-horror arcs that reinforce faction conflict, travel peril, secrecy, and the Vigil.
\"\"\"
"""

INSERT_ENTRIES_BLOCK = """

    entries.append({
        \"title\": \"Beings of the Dark Medieval World\",
        \"content\": BEINGS_OVERVIEW,
        \"category\": WorldbuildingCategory.BEINGS,
        \"tags\": [\"beings\", \"mortals\", \"hunters\", \"cainites\", \"lupines\", \"witches\", \"spirits\"],
        \"importance\": 10
    })

    entries.append({
        \"title\": \"Factions & Organizations Overview\",
        \"content\": FACTIONS_ORGANIZATIONS_OVERVIEW,
        \"category\": WorldbuildingCategory.FACTIONS_ORGANIZATIONS,
        \"tags\": [\"factions\", \"organizations\", \"domains\", \"courts\", \"guilds\", \"inquisition\", \"hunters\"],
        \"importance\": 9
    })

    entries.append({
        \"title\": \"Expansion Seeds - Dark Medieval Hooks\",
        \"content\": EXPANSION_SEEDS_OVERVIEW,
        \"category\": WorldbuildingCategory.EXPANSION_SEEDS,
        \"tags\": [\"expansion\", \"hooks\", \"plot\", \"seeds\", \"arcs\"],
        \"importance\": 7
    })
"""


def die(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "WORLD_BUILDER" / "realitas_lore.py"
    text = target.read_text(encoding="utf-8")

    if "BEINGS_OVERVIEW" in text or "FACTIONS_ORGANIZATIONS_OVERVIEW" in text or "EXPANSION_SEEDS_OVERVIEW" in text:
        return die("Refusing to patch: one or more target blocks already exist in realitas_lore.py")

    # 1) Insert content blocks after SETTING_SUPERNATURAL closes (first occurrence)
    start = text.find('SETTING_SUPERNATURAL = """')
    if start == -1:
        return die("Could not find SETTING_SUPERNATURAL block start")

    end = text.find('"""', start + len('SETTING_SUPERNATURAL = """'))
    if end == -1:
        return die("Could not find SETTING_SUPERNATURAL closing triple-quote")

    end = text.find('\n', end)  # end-of-line after closing quotes
    if end == -1:
        return die("Could not locate newline after SETTING_SUPERNATURAL closing quotes")

    text = text[: end + 1] + INSERT_BLOCK + text[end + 1 :]

    # 2) Insert entries after the SUPERNATURAL entry append in create_lore_entries
    anchor = '"title": "Supernatural Elements - Vampiric Disciplines"'
    idx = text.find(anchor)
    if idx == -1:
        return die("Could not find supernatural entry anchor in create_lore_entries")

    # Find the end of that entries.append({...}) block by finding the next line that starts with '    })'
    block_end = text.find("\n    })", idx)
    if block_end == -1:
        return die("Could not find end of supernatural entries.append block")

    insert_at = block_end + len("\n    })")
    text = text[:insert_at] + INSERT_ENTRIES_BLOCK + text[insert_at:]

    target.write_text(text, encoding="utf-8")
    print("Patched realitas_lore.py with BEINGS / FACTIONS_ORGANIZATIONS / EXPANSION_SEEDS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
