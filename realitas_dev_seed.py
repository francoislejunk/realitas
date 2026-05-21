"""Seed a fresh dev ContextStore with a minimal Realitas world snapshot.

The seed is intentionally idempotent and conservative: if the target DB already
has world events for the session, it does nothing. That preserves live simulator
persistence while letting a new dev VPS expose /api/world from SQLite instead of
only the checked-in JSON fallback.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

from context_store import ContextStore, WorldTime


def seed_dev_context(*, db_path: Path, session_id: str = "default") -> Dict[str, Any]:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store = ContextStore(db_path)

    existing_events = store.get_recent_world_events(session_id=session_id, limit=1)
    if existing_events:
        return {"created": False, "db_path": str(db_path), "session_id": session_id}

    store.upsert_actor(
        session_id=session_id,
        actor_uuid="vessel-001",
        display_name="First Vessel",
        actor_type="vessel",
        serialized_sheet={
            "stance": "newly embodied",
            "drive": "understand what the world wants",
        },
        tags=["vessel", "player-facing"],
    )
    store.set_actor_location_state(
        session_id=session_id,
        actor_uuid="vessel-001",
        current_location_id="threshold-harbor",
        presence_state="awake",
        last_seen_world_minutes=485,
        home_location_id="threshold-harbor",
    )
    store.log_world_event(
        session_id=session_id,
        location_id="threshold-harbor",
        event_type="SITUATION_ACTIVE",
        summary="Threshold Harbor holds its breath as the first vessel wakes into a world that remembers.",
        importance=8,
        tags=["dev-seed", "vessel-awakening", "threshold-harbor"],
        payload={
            "actor_ids": ["vessel-001"],
            "memory_type": "situation",
            "pinned_memory": True,
            "disable_auto_memory_seed": False,
        },
        world_time=WorldTime(day=1, hour=8, minute=5),
    )
    return {"created": True, "db_path": str(db_path), "session_id": session_id}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a fresh Realitas dev ContextStore")
    parser.add_argument("--db", default="simulation_data/context/context.db", type=Path)
    parser.add_argument("--session", default="default")
    args = parser.parse_args()
    result = seed_dev_context(db_path=args.db, session_id=args.session)
    action = "created" if result["created"] else "skipped-existing"
    print(f"dev context seed {action}: {result['db_path']} session={result['session_id']}")


if __name__ == "__main__":
    main()
