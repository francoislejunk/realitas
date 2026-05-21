from pathlib import Path
import os

try:
    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory, WorldbuildingRAGSystem
except ModuleNotFoundError:
    from worldbuilding_rag import WorldbuildingCategory, WorldbuildingRAGSystem


def _resolve_storage_path(storage_dir: str = "") -> Path:
    sd = (storage_dir or "").strip()
    if sd:
        return Path(sd)

    env = os.getenv("REALITAS_RAG_STORAGE_DIR", "").strip()
    if env:
        return Path(env)

    # Default used by the main sim when pointed at a "simplified" directory
    return Path("./simulation_data/simplified_worldbuilding_rag")


def create_lore_entries():
    # Keep these deliberately tiny and distinctive so it's obvious what the agents are pulling.
    entries = [
        {
            "title": "TEMPORAL (SIMPLIFIED)",
            "content": "CURRENT YEAR: 1234\nERA: TEST ERA\nTECH LEVEL: NO GUNS, NO MODERN ELECTRONICS\n",
            "category": WorldbuildingCategory.TEMPORAL,
            "tags": ["simplified", "temporal"],
            "importance": 10,
        },
        {
            "title": "CITIES (SIMPLIFIED)",
            "content": "**AlphaCity**\n- A stone city with red banners.\n\n**BetaTown**\n- A muddy riverside town.\n",
            "category": WorldbuildingCategory.CITIES,
            "tags": ["simplified", "cities"],
            "importance": 10,
        },
        {
            "title": "UA_OCCUPATIONS (SIMPLIFIED)",
            "content": "- Tester\n- Courier\n- Baker\n",
            "category": WorldbuildingCategory.UA_OCCUPATIONS,
            "tags": ["simplified", "ua", "occupations"],
            "importance": 10,
        },
        {
            "title": "NUA_OCCUPATIONS (SIMPLIFIED)",
            "content": "- Guard\n- Merchant\n- Farmer\n",
            "category": WorldbuildingCategory.NUA_OCCUPATIONS,
            "tags": ["simplified", "nua", "occupations"],
            "importance": 10,
        },
        {
            "title": "MNUA_OCCUPATIONS (SIMPLIFIED)",
            "content": "- Captain\n- Magistrate\n- Priest\n",
            "category": WorldbuildingCategory.MNUA_OCCUPATIONS,
            "tags": ["simplified", "mnua", "occupations"],
            "importance": 10,
        },
        {
            "title": "MECHANICS (SIMPLIFIED)",
            "content": "RULE: Anything not listed in RAG does not exist.\nRULE: If an item is not in scene/inventory, it cannot be used.\n\nSKILLS VOCAB (Mode B):\n- Barter\n- Crafting\n- Endurance\n- Investigation\n- Melee\n- Perception\n- Stealth\n\nITEMS VOCAB (Mode B):\n- Torch\n- Rope\n- Dagger\n- Cloak\n- Bread\n- Waterskin\n",
            "category": WorldbuildingCategory.MECHANICS,
            "tags": ["simplified", "mechanics"],
            "importance": 10,
        },
        {
            "title": "GOALS_UA (SIMPLIFIED - EXPLICIT)",
            "content": "- Secure a safe place to sleep before dawn.\n- Deliver a sealed message without being followed.\n- Recover a stolen satchel and return it intact.\n- Find a reliable patron for steady work.\n- Prove your innocence to the local watch.\n",
            "category": WorldbuildingCategory.GOALS_UA,
            "tags": ["simplified", "goals", "ua", "explicit", "whitelist"],
            "importance": 10,
        },
        {
            "title": "GOALS_NUA (SIMPLIFIED - EXPLICIT)",
            "content": "- Keep your family fed through the week.\n- Avoid the guard’s suspicion during patrols.\n- Repay a small debt before penalties worsen.\n- Protect a sick relative from harm.\n- Maintain your stall’s reputation in the market.\n",
            "category": WorldbuildingCategory.GOALS_NUA,
            "tags": ["simplified", "goals", "nua", "explicit", "whitelist"],
            "importance": 10,
        },
        {
            "title": "GOALS_MNUA (SIMPLIFIED - EXPLICIT)",
            "content": "- Consolidate authority over the district without open conflict.\n- Silence a dangerous witness before testimony spreads.\n- Secure a written decree that shifts local power.\n- Uncover who has been stealing from the granaries.\n- Ensure a rival’s plan fails without revealing your hand.\n",
            "category": WorldbuildingCategory.GOALS_MNUA,
            "tags": ["simplified", "goals", "mnua", "explicit", "whitelist"],
            "importance": 10,
        },
        {
            "title": "FACTION_UA (SIMPLIFIED)",
            "content": "Testers Guild: A small guild of sanctioned testers and troubleshooters.\nCouriers Circle: A loose network of reliable messengers.\nBakers Union: A pragmatic group protecting ovens and grain.\n",
            "category": WorldbuildingCategory.FACTION_UA,
            "tags": ["simplified", "faction", "ua"],
            "importance": 10,
        },
        {
            "title": "FACTION_NUA (SIMPLIFIED)",
            "content": "Town Watch: The local guards who keep order (and take bribes).\nMarket Hands: Laborers and stall-keepers who share information.\nRiver Folk: People who work the docks and boats.\n",
            "category": WorldbuildingCategory.FACTION_NUA,
            "tags": ["simplified", "faction", "nua"],
            "importance": 10,
        },
        {
            "title": "FACTION_MNUA (SIMPLIFIED)",
            "content": "The Magistrate’s Office: Civil authority over disputes and records.\nThe Iron Captaincy: A disciplined militia leadership clique.\nThe Abbey Council: Clerical power brokers behind sealed doors.\n",
            "category": WorldbuildingCategory.FACTION_MNUA,
            "tags": ["simplified", "faction", "mnua"],
            "importance": 10,
        },
        {
            "title": "SUPERNATURAL (SIMPLIFIED)",
            "content": "NO MAGIC. NO SUPERNATURAL POWERS.\n",
            "category": WorldbuildingCategory.SUPERNATURAL,
            "tags": ["simplified", "supernatural"],
            "importance": 10,
        },
    ]

    # Ensure every category is represented at least once.
    present = {e.get('category') for e in entries}
    missing = [c for c in WorldbuildingCategory if c not in present]

    for cat in missing:
        entries.append(
            {
                "title": f"{cat.name} (SIMPLIFIED - COVERAGE)",
                "content": f"SIMPLIFIED::{cat.value}\nThis is a coverage harness document.\n",
                "category": cat,
                "tags": ["simplified", "coverage", cat.value],
                "importance": 1,
            }
        )

    return entries


def load_all_lore(rag_system: WorldbuildingRAGSystem = None, clear_first: bool = False):
    if rag_system is None:
        storage_path = _resolve_storage_path()
        rag_system = WorldbuildingRAGSystem(storage_path)

    if clear_first:
        rag_system.clear_all()

    lore_entries = create_lore_entries()
    for entry in lore_entries:
        rag_system.add_document(
            title=entry["title"],
            content=entry["content"],
            category=entry["category"],
            tags=entry.get("tags", []),
            importance=entry.get("importance", 5),
            subcategory=entry.get("subcategory", None),
            related_docs=entry.get("related_docs", []),
        )

    return rag_system


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--storage-dir", type=str, default="")
    args = parser.parse_args()

    storage_path = _resolve_storage_path(args.storage_dir)
    rag = load_all_lore(rag_system=WorldbuildingRAGSystem(storage_path), clear_first=True)
    print(f"Loaded simplified lore docs: {len(rag.documents)}")
    print(f"Storage location: {rag.storage_directory}")

    # Coverage report
    try:
        present = {getattr(doc, 'category', None) for doc in (rag.documents or {}).values()}
        missing = [c for c in WorldbuildingCategory if c not in present]
        if missing:
            print("Missing categories:")
            for c in missing:
                print(f"- {c.name} ({c.value})")
        else:
            print("All WorldbuildingCategory values are present in simplified RAG.")
    except Exception as e:
        print(f"Coverage report failed: {e}")
