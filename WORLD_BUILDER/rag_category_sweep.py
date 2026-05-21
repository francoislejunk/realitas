import os
import sys
from pathlib import Path
from typing import Dict, Tuple


def _resolve_storage_dir() -> Path:
    env = os.getenv("REALITAS_RAG_STORAGE_DIR", "").strip()
    if env:
        return Path(env)

    # Default used by the main sim
    return Path("simulation_data") / "worldbuilding_rag"


def main() -> int:
    # Import locally so this script can be executed from repo root:
    #   python WORLD_BUILDER/rag_category_sweep.py
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    from worldbuilding_rag import WorldbuildingRAGSystem, WorldbuildingCategory  # noqa: E402

    storage_dir = _resolve_storage_dir()
    rag = WorldbuildingRAGSystem(storage_directory=storage_dir)

    print(f"Storage location: {storage_dir}")
    print(f"Total documents loaded: {len(rag.documents)}")

    results: Dict[str, Tuple[int, int]] = {}
    missing_docs = []
    missing_hits = []

    for cat in WorldbuildingCategory:
        docs_in_cat = len(rag.docs_by_category.get(cat, []))

        # For the simplified DB, every doc includes a category-specific marker.
        # Querying by that marker makes hits deterministic.
        marker_query = f"SIMPLIFIED::{cat.value}"
        hits = rag.search(marker_query, top_k=3, category_filter=cat)
        hit_count = len(hits)

        results[cat.value] = (docs_in_cat, hit_count)

        if docs_in_cat == 0:
            missing_docs.append(cat.value)
        if hit_count == 0:
            missing_hits.append(cat.value)

    print("\n=== Category Sweep Results ===")
    for cat_value in sorted(results.keys()):
        docs_in_cat, hit_count = results[cat_value]
        print(f"- {cat_value}: docs={docs_in_cat} search_hits={hit_count}")

    print("\n=== Summary ===")
    if missing_docs:
        print("Missing docs (category has zero stored docs):")
        for c in missing_docs:
            print(f"- {c}")
    else:
        print("All categories have >= 1 stored doc.")

    if missing_hits:
        print("\nMissing search hits (category_filter search returned zero docs):")
        for c in missing_hits:
            print(f"- {c}")
    else:
        print("All categories produce >= 1 deterministic search hit.")

    if missing_docs or missing_hits:
        print("\nFAIL")
        return 2

    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
