import json
from pathlib import Path

from context_store import ContextStore, WorldTime
from realitas_world_exporter import export_world_state


def test_export_world_state_from_context_store(tmp_path: Path):
    db_path = tmp_path / "context.db"
    output_path = tmp_path / "world-state.json"
    store = ContextStore(db_path)
    session_id = "test-session"

    store.upsert_actor(
        session_id=session_id,
        actor_uuid="nua",
        display_name="Nua",
        actor_type="vessel",
        serialized_sheet={"mood": "watchful"},
        tags=["vessel"],
    )
    store.set_actor_location_state(
        session_id=session_id,
        actor_uuid="nua",
        current_location_id="harbor-market",
        presence_state="listening",
        last_seen_world_minutes=4785,
    )
    store.log_world_event(
        session_id=session_id,
        location_id="harbor-market",
        event_type="SITUATION_ACTIVE",
        summary="Fishmongers argue under the awnings while Nua listens.",
        importance=8,
        tags=["market", "social-tension"],
        payload={"actor_ids": ["nua"]},
        world_time=WorldTime(day=4, hour=7, minute=45),
    )

    exported = export_world_state(
        db_path=db_path,
        output_path=output_path,
        session_id=session_id,
        world_name="Nua Harbor Market",
        promise="NPCs keep moving when the vessel is absent",
    )

    assert exported["world"]["name"] == "Nua Harbor Market"
    assert exported["world"]["status"] == "active-simulation"
    assert exported["world"]["location"] == "harbor-market"
    assert exported["world"]["world_time"] == {"day": 4, "hour": 7, "minute": 45}
    assert exported["actors"] == [
        {
            "id": "nua",
            "name": "Nua",
            "role": "vessel",
            "state": "listening",
            "location": "harbor-market",
        }
    ]
    assert exported["recent_events"][0]["summary"] == "Fishmongers argue under the awnings while Nua listens."
    assert exported["recent_events"][0]["importance"] == 8

    on_disk = json.loads(output_path.read_text(encoding="utf-8"))
    assert on_disk == exported
