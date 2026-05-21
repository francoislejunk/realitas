"""Export Realitas simulator context into the web-facing world-state JSON.

This is the bridge between the Python simulation persistence layer and the Node
web shell. The web server deliberately stays simple: it reads one JSON file.
This exporter owns translating ContextStore rows into that contract.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _json_loads(value: Optional[str], fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except Exception:
        return fallback


def _latest_world_event(conn: sqlite3.Connection, session_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT event_id, location_id, event_type, summary, importance,
               tags_json, payload_json,
               world_day, world_hour, world_minute, world_minutes_since_start,
               created_at
        FROM world_events
        WHERE session_id = ?
        ORDER BY
          COALESCE(world_minutes_since_start, -1) DESC,
          event_id DESC
        LIMIT 1;
        """,
        (session_id,),
    ).fetchone()


def _recent_events(conn: sqlite3.Connection, session_id: str, limit: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT event_id, location_id, event_type, summary, importance,
               tags_json, payload_json,
               world_day, world_hour, world_minute, world_minutes_since_start,
               created_at
        FROM world_events
        WHERE session_id = ?
        ORDER BY
          COALESCE(world_minutes_since_start, -1) DESC,
          event_id DESC
        LIMIT ?;
        """,
        (session_id, int(limit)),
    ).fetchall()
    return [
        {
            "id": int(row["event_id"]),
            "type": row["event_type"],
            "summary": row["summary"] or "",
            "importance": int(row["importance"] or 0),
            "location": row["location_id"],
            "tags": _json_loads(row["tags_json"], []),
            "world_time": {
                "day": row["world_day"],
                "hour": row["world_hour"],
                "minute": row["world_minute"],
            },
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _actors(conn: sqlite3.Connection, session_id: str, limit: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT a.actor_uuid, a.display_name, a.actor_type,
               s.current_location_id, s.presence_state
        FROM actors a
        LEFT JOIN actor_location_state s
          ON s.session_id = a.session_id AND s.actor_uuid = a.actor_uuid
        WHERE a.session_id = ?
        ORDER BY a.updated_at DESC, a.display_name ASC
        LIMIT ?;
        """,
        (session_id, int(limit)),
    ).fetchall()
    return [
        {
            "id": row["actor_uuid"],
            "name": row["display_name"] or row["actor_uuid"],
            "role": row["actor_type"] or "actor",
            "state": row["presence_state"] or "present",
            "location": row["current_location_id"],
        }
        for row in rows
    ]


def export_world_state(
    *,
    db_path: Path,
    output_path: Path,
    session_id: str = "default",
    world_name: str = "Realitas Dev Shard",
    promise: str = "AI Reality Simulator",
    event_limit: int = 8,
    actor_limit: int = 16,
) -> Dict[str, Any]:
    db_path = Path(db_path)
    output_path = Path(output_path)
    if not db_path.exists():
        raise FileNotFoundError(f"ContextStore database not found: {db_path}")

    conn = _connect(db_path)
    try:
        latest = _latest_world_event(conn, session_id)
        actors = _actors(conn, session_id, actor_limit)
        recent_events = _recent_events(conn, session_id, event_limit)
    finally:
        conn.close()

    latest_location = latest["location_id"] if latest is not None else None
    world_time = None
    if latest is not None and latest["world_day"] is not None:
        world_time = {
            "day": latest["world_day"],
            "hour": latest["world_hour"],
            "minute": latest["world_minute"],
        }

    state = {
        "world": {
            "name": world_name,
            "status": "active-simulation" if latest is not None or actors else "awaiting-simulation",
            "promise": promise,
            "location": latest_location or (actors[0].get("location") if actors else "uninitialized"),
            "world_time": world_time,
        },
        "actors": actors,
        "recent_events": recent_events,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_path.replace(output_path)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Export ContextStore state for the Realitas web API")
    parser.add_argument("--db", default="simulation_data/context/context.db", type=Path)
    parser.add_argument("--out", default="data/world-state.json", type=Path)
    parser.add_argument("--session", default="default")
    parser.add_argument("--world-name", default="Realitas Dev Shard")
    parser.add_argument("--promise", default="AI Reality Simulator")
    args = parser.parse_args()

    state = export_world_state(
        db_path=args.db,
        output_path=args.out,
        session_id=args.session,
        world_name=args.world_name,
        promise=args.promise,
    )
    print(f"exported {len(state['actors'])} actors and {len(state['recent_events'])} events to {args.out}")


if __name__ == "__main__":
    main()
