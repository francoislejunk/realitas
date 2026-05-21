from pathlib import Path

from context_store import ContextStore
from realitas_dev_seed import seed_dev_context


def test_seed_dev_context_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "context.db"
    first = seed_dev_context(db_path=db_path, session_id="default")
    second = seed_dev_context(db_path=db_path, session_id="default")

    assert first["created"] is True
    assert second["created"] is False

    store = ContextStore(db_path)
    events = store.get_recent_world_events(session_id="default", limit=10)
    assert len(events) == 1
    assert events[0]["event_type"] == "SITUATION_ACTIVE"
    assert "Threshold Harbor" in events[0]["summary"]

    actor = store.get_actor(session_id="default", actor_uuid="vessel-001")
    assert actor is not None
    assert actor["display_name"] == "First Vessel"

    location = store.get_actor_location_state(session_id="default", actor_uuid="vessel-001")
    assert location is not None
    assert location["current_location_id"] == "threshold-harbor"
