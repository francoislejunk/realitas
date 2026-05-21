import json
import sqlite3
import threading
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class WorldTime:
    day: int
    hour: int
    minute: int

    @property
    def minutes_since_start(self) -> int:
        return (max(self.day, 1) - 1) * 1440 + self.hour * 60 + self.minute


class ContextStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS position_snapshots (
                        snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        location_id TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        entity_name TEXT,
                        entity_type TEXT,
                        x REAL,
                        y REAL,
                        facing_direction REAL,
                        is_active INTEGER,
                        zone_id TEXT,
                        world_day INTEGER,
                        world_hour INTEGER,
                        world_minute INTEGER,
                        world_minutes_since_start INTEGER,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    );
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_position_snapshots_lookup
                    ON position_snapshots(session_id, location_id, entity_id, created_at);
                    """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS world_events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        location_id TEXT,
                        event_type TEXT NOT NULL,
                        summary TEXT,
                        importance INTEGER,
                        tags_json TEXT,
                        payload_json TEXT,
                        world_day INTEGER,
                        world_hour INTEGER,
                        world_minute INTEGER,
                        world_minutes_since_start INTEGER,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    );
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_world_events_lookup
                    ON world_events(session_id, location_id, world_minutes_since_start, created_at);
                    """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS actor_memory_items (
                        memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        actor_id TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source_event_id INTEGER,
                        importance INTEGER NOT NULL DEFAULT 5,
                        pinned INTEGER NOT NULL DEFAULT 0,
                        initial_strength REAL NOT NULL DEFAULT 1.0,
                        decay_rate REAL NOT NULL DEFAULT 0.0005,
                        world_minutes_first_seen INTEGER,
                        world_minutes_last_recalled INTEGER,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    );
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_actor_memory_lookup
                    ON actor_memory_items(session_id, actor_id, memory_type, importance);
                    """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS actors (
                        actor_uuid TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        display_name TEXT,
                        actor_type TEXT,
                        serialized_sheet_json TEXT,
                        tags_json TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    );
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_actors_lookup
                    ON actors(session_id, display_name, updated_at);
                    """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS location_cast (
                        session_id TEXT NOT NULL,
                        location_id TEXT NOT NULL,
                        actor_uuid TEXT NOT NULL,
                        role TEXT,
                        schedule_json TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        PRIMARY KEY (session_id, location_id, actor_uuid)
                    );
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_location_cast_lookup
                    ON location_cast(session_id, location_id);
                    """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS actor_location_state (
                        session_id TEXT NOT NULL,
                        actor_uuid TEXT NOT NULL,
                        current_location_id TEXT,
                        presence_state TEXT,
                        en_route_to_location_id TEXT,
                        eta_world_minutes INTEGER,
                        last_seen_world_minutes INTEGER,
                        follow_target_uuid TEXT,
                        pursue_target_uuid TEXT,
                        home_location_id TEXT,
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        PRIMARY KEY (session_id, actor_uuid)
                    );
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_actor_location_state_lookup
                    ON actor_location_state(session_id, current_location_id, presence_state, eta_world_minutes);
                    """
                )

                conn.commit()
            finally:
                conn.close()

    def record_position_snapshot(
        self,
        *,
        session_id: str,
        location_id: str,
        entities: Iterable[Dict[str, Any]],
        world_time: Optional[WorldTime] = None,
    ) -> None:
        rows: List[tuple] = []
        wday = world_time.day if world_time else None
        whour = world_time.hour if world_time else None
        wmin = world_time.minute if world_time else None
        wms = world_time.minutes_since_start if world_time else None

        for e in entities:
            rows.append(
                (
                    session_id,
                    location_id,
                    e.get("entity_id"),
                    e.get("entity_name"),
                    e.get("entity_type"),
                    e.get("x"),
                    e.get("y"),
                    e.get("facing_direction"),
                    1 if e.get("is_active", True) else 0,
                    e.get("zone_id"),
                    wday,
                    whour,
                    wmin,
                    wms,
                )
            )

        if not rows:
            return

        with self._lock:
            conn = self._connect()
            try:
                conn.executemany(
                    """
                    INSERT INTO position_snapshots (
                        session_id, location_id, entity_id, entity_name, entity_type,
                        x, y, facing_direction, is_active, zone_id,
                        world_day, world_hour, world_minute, world_minutes_since_start
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    rows,
                )
                conn.commit()
            finally:
                conn.close()

    def log_world_event(
        self,
        *,
        session_id: str,
        event_type: str,
        summary: str = "",
        location_id: Optional[str] = None,
        importance: int = 5,
        tags: Optional[List[str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        world_time: Optional[WorldTime] = None,
    ) -> int:
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        payload_obj = payload or {}
        payload_json = json.dumps(payload_obj, ensure_ascii=False)

        wday = world_time.day if world_time else None
        whour = world_time.hour if world_time else None
        wmin = world_time.minute if world_time else None
        wms = world_time.minutes_since_start if world_time else None

        with self._lock:
            conn = self._connect()
            try:
                # Noise reduction: normalized-summary de-dupe for INFO_LEARNED bursts
                try:
                    if event_type == 'INFO_LEARNED' and wms is not None:
                        def _norm(s: str) -> str:
                            try:
                                s = (s or '').lower()
                                s = re.sub(r"[^a-z0-9\s]+", " ", s)
                                s = re.sub(r"\s+", " ", s).strip()
                                return s
                            except Exception:
                                return (s or '').strip().lower()

                        norm_summary = _norm(summary)
                        if norm_summary:
                            window_minutes = 3
                            min_wms = int(wms) - int(window_minutes)
                            if location_id is None:
                                rows = conn.execute(
                                    """
                                    SELECT event_id, summary
                                    FROM world_events
                                    WHERE session_id = ? AND location_id IS NULL AND event_type = ?
                                      AND world_minutes_since_start IS NOT NULL
                                      AND world_minutes_since_start >= ?
                                    ORDER BY event_id DESC
                                    LIMIT 8;
                                    """,
                                    (session_id, event_type, int(min_wms))
                                ).fetchall()
                            else:
                                rows = conn.execute(
                                    """
                                    SELECT event_id, summary
                                    FROM world_events
                                    WHERE session_id = ? AND location_id = ? AND event_type = ?
                                      AND world_minutes_since_start IS NOT NULL
                                      AND world_minutes_since_start >= ?
                                    ORDER BY event_id DESC
                                    LIMIT 8;
                                    """,
                                    (session_id, location_id, event_type, int(min_wms))
                                ).fetchall()

                            for r in rows or []:
                                if _norm(r["summary"] or '') == norm_summary:
                                    return int(r["event_id"])
                except Exception:
                    pass

                # Noise reduction: time-window de-dupe for high-frequency event types
                try:
                    noisy_types = {
                        'CLUE_DETECTED': 3,
                        'SITUATION_ACTIVE': 3,
                        # Inventory updates can be emitted multiple times in quick succession
                        # (e.g., retries / overlapping subsystems). Keep only one per short window
                        # when the summary is identical.
                        'INVENTORY_UPDATED': 2,
                    }
                    if event_type in noisy_types and wms is not None:
                        window_minutes = int(noisy_types.get(event_type, 3))
                        min_wms = int(wms) - int(window_minutes)
                        if location_id is None:
                            row = conn.execute(
                                """
                                SELECT event_id, summary, world_minutes_since_start
                                FROM world_events
                                WHERE session_id = ? AND location_id IS NULL AND event_type = ?
                                  AND world_minutes_since_start IS NOT NULL
                                  AND world_minutes_since_start >= ?
                                ORDER BY event_id DESC
                                LIMIT 1;
                                """,
                                (session_id, event_type, int(min_wms))
                            ).fetchone()
                        else:
                            row = conn.execute(
                                """
                                SELECT event_id, summary, world_minutes_since_start
                                FROM world_events
                                WHERE session_id = ? AND location_id = ? AND event_type = ?
                                  AND world_minutes_since_start IS NOT NULL
                                  AND world_minutes_since_start >= ?
                                ORDER BY event_id DESC
                                LIMIT 1;
                                """,
                                (session_id, location_id, event_type, int(min_wms))
                            ).fetchone()

                        if row is not None and (row["summary"] or "") == (summary or ""):
                            return int(row["event_id"])
                except Exception:
                    pass

                # Noise reduction: de-dupe consecutive identical events
                try:
                    if location_id is None:
                        row = conn.execute(
                            """
                            SELECT event_id, summary, tags_json, payload_json
                            FROM world_events
                            WHERE session_id = ? AND location_id IS NULL AND event_type = ?
                            ORDER BY event_id DESC
                            LIMIT 1;
                            """,
                            (session_id, event_type)
                        ).fetchone()
                    else:
                        row = conn.execute(
                            """
                            SELECT event_id, summary, tags_json, payload_json
                            FROM world_events
                            WHERE session_id = ? AND location_id = ? AND event_type = ?
                            ORDER BY event_id DESC
                            LIMIT 1;
                            """,
                            (session_id, location_id, event_type)
                        ).fetchone()

                    if row is not None:
                        if (row["summary"] or "") == (summary or "") and (row["tags_json"] or "") == tags_json and (row["payload_json"] or "") == payload_json:
                            return int(row["event_id"])
                except Exception:
                    pass

                cur = conn.execute(
                    """
                    INSERT INTO world_events (
                        session_id, location_id, event_type, summary, importance,
                        tags_json, payload_json,
                        world_day, world_hour, world_minute, world_minutes_since_start
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        session_id,
                        location_id,
                        event_type,
                        summary,
                        int(importance),
                        tags_json,
                        payload_json,
                        wday,
                        whour,
                        wmin,
                        wms,
                    ),
                )
                conn.commit()
                event_id = int(cur.lastrowid)

                # Best-effort: auto-seed long-term memories from high-signal world events
                # (callers can opt out by setting payload['disable_auto_memory_seed']=True)
                try:
                    disable_seed = bool(payload_obj.get('disable_auto_memory_seed'))
                except Exception:
                    disable_seed = False

                if not disable_seed:
                    try:
                        high_signal = {
                            'INFO_LEARNED',
                            'DETAIL_ESTABLISHED',
                            'STATUS_CHANGED',
                            'ITEM_GAINED',
                            'ITEM_LOST',
                            'FACTION_AFFILIATION',
                            'SITUATION_ACTIVE',
                        }
                        actor_ids = payload_obj.get('actor_ids') if isinstance(payload_obj, dict) else None
                        force_seed = False
                        try:
                            force_seed = bool(payload_obj.get('force_auto_memory_seed'))
                        except Exception:
                            force_seed = False

                        should_seed = (
                            (event_type in high_signal)
                            or (force_seed and str(event_type) == 'CLUE_DETECTED')
                            or (force_seed and str(event_type) == 'INVENTORY_UPDATED')
                        )
                        if should_seed and actor_ids and isinstance(actor_ids, list):
                            for aid in actor_ids:
                                if not aid:
                                    continue
                                try:
                                    memory_type = str(payload_obj.get('memory_type') or str(event_type).lower())
                                except Exception:
                                    memory_type = str(event_type).lower()

                                pinned = False
                                try:
                                    pinned = bool(payload_obj.get('pinned_memory'))
                                except Exception:
                                    pinned = False
                                if event_type == 'DETAIL_ESTABLISHED':
                                    pinned = True if pinned is False else pinned

                                decay_rate = None
                                try:
                                    dr = payload_obj.get('decay_rate')
                                    if dr is not None:
                                        decay_rate = float(dr)
                                except Exception:
                                    decay_rate = None

                                if decay_rate is None:
                                    try:
                                        decay_rate = {
                                            'INFO_LEARNED': 0.00015,
                                            'DETAIL_ESTABLISHED': 0.0,
                                            'STATUS_CHANGED': 0.00025,
                                            'ITEM_GAINED': 0.0002,
                                            'ITEM_LOST': 0.00025,
                                            'INVENTORY_UPDATED': 0.00025,
                                            'SITUATION_ACTIVE': 0.00022,
                                        }.get(str(event_type), 0.00022)
                                    except Exception:
                                        decay_rate = 0.00022

                                try:
                                    decay_rate_f = float(decay_rate)
                                except Exception:
                                    decay_rate_f = 0.00022

                                try:
                                    self.remember(
                                        session_id=session_id,
                                        actor_id=str(aid),
                                        memory_type=memory_type,
                                        content=str(summary or ''),
                                        importance=int(importance),
                                        pinned=bool(pinned),
                                        decay_rate=decay_rate_f,
                                        source_event_id=int(event_id),
                                        world_time=world_time
                                    )
                                except Exception:
                                    pass
                    except Exception:
                        pass

                return event_id
            finally:
                conn.close()

    def get_recent_world_events(
        self,
        *,
        session_id: str,
        location_id: Optional[str] = None,
        limit: int = 25,
        min_world_minutes_since_start: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT event_id, session_id, location_id, event_type, summary, importance,
                   tags_json, payload_json,
                   world_day, world_hour, world_minute, world_minutes_since_start,
                   created_at
            FROM world_events
            WHERE session_id = ?
        """
        params: List[Any] = [session_id]

        if location_id is not None:
            query += " AND location_id = ?"
            params.append(location_id)

        if min_world_minutes_since_start is not None:
            query += " AND world_minutes_since_start >= ?"
            params.append(int(min_world_minutes_since_start))

        query += " ORDER BY event_id DESC LIMIT ?"
        params.append(int(limit))

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(query, tuple(params)).fetchall()
                out: List[Dict[str, Any]] = []
                for r in rows:
                    out.append({
                        "event_id": r["event_id"],
                        "session_id": r["session_id"],
                        "location_id": r["location_id"],
                        "event_type": r["event_type"],
                        "summary": r["summary"],
                        "importance": r["importance"],
                        "tags": json.loads(r["tags_json"] or "[]"),
                        "payload": json.loads(r["payload_json"] or "{}"),
                        "world_day": r["world_day"],
                        "world_hour": r["world_hour"],
                        "world_minute": r["world_minute"],
                        "world_minutes_since_start": r["world_minutes_since_start"],
                        "created_at": r["created_at"],
                    })
                return out
            finally:
                conn.close()

    def get_world_events_by_type(
        self,
        *,
        session_id: str,
        event_type: str,
        location_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Fetch recent world events filtered by type.

        This is intended for durable, queryable canon facts (e.g., generated cities).
        """
        et = (event_type or '').strip()
        if not et:
            return []

        query = """
            SELECT event_id, session_id, location_id, event_type, summary, importance,
                   tags_json, payload_json,
                   world_day, world_hour, world_minute, world_minutes_since_start,
                   created_at
            FROM world_events
            WHERE session_id = ? AND event_type = ?
        """
        params: List[Any] = [session_id, et]

        if location_id is not None:
            query += " AND location_id = ?"
            params.append(location_id)

        query += " ORDER BY event_id DESC LIMIT ?"
        params.append(int(limit))

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(query, tuple(params)).fetchall()
                out: List[Dict[str, Any]] = []
                for r in rows or []:
                    out.append({
                        "event_id": r["event_id"],
                        "session_id": r["session_id"],
                        "location_id": r["location_id"],
                        "event_type": r["event_type"],
                        "summary": r["summary"],
                        "importance": r["importance"],
                        "tags": json.loads(r["tags_json"] or "[]"),
                        "payload": json.loads(r["payload_json"] or "{}"),
                        "world_day": r["world_day"],
                        "world_hour": r["world_hour"],
                        "world_minute": r["world_minute"],
                        "world_minutes_since_start": r["world_minutes_since_start"],
                        "created_at": r["created_at"],
                    })
                return out
            finally:
                conn.close()

    def upsert_actor(
        self,
        *,
        session_id: str,
        actor_uuid: str,
        display_name: str,
        actor_type: str,
        serialized_sheet: Dict[str, Any],
        tags: Optional[List[str]] = None,
    ) -> None:
        sheet_json = json.dumps(serialized_sheet or {}, ensure_ascii=False)
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO actors (
                        actor_uuid, session_id, display_name, actor_type, serialized_sheet_json, tags_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(actor_uuid) DO UPDATE SET
                        session_id=excluded.session_id,
                        display_name=excluded.display_name,
                        actor_type=excluded.actor_type,
                        serialized_sheet_json=excluded.serialized_sheet_json,
                        tags_json=excluded.tags_json,
                        updated_at=datetime('now');
                    """,
                    (
                        str(actor_uuid),
                        str(session_id),
                        str(display_name or ''),
                        str(actor_type or ''),
                        sheet_json,
                        tags_json,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def get_actor(self, *, session_id: str, actor_uuid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    """
                    SELECT actor_uuid, session_id, display_name, actor_type, serialized_sheet_json, tags_json, created_at, updated_at
                    FROM actors
                    WHERE session_id = ? AND actor_uuid = ?
                    LIMIT 1;
                    """,
                    (str(session_id), str(actor_uuid)),
                ).fetchone()
                if row is None:
                    return None
                return {
                    'actor_uuid': row['actor_uuid'],
                    'session_id': row['session_id'],
                    'display_name': row['display_name'],
                    'actor_type': row['actor_type'],
                    'serialized_sheet': json.loads(row['serialized_sheet_json'] or '{}'),
                    'tags': json.loads(row['tags_json'] or '[]'),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                }
            finally:
                conn.close()

    def add_actor_to_location_cast(
        self,
        *,
        session_id: str,
        location_id: str,
        actor_uuid: str,
        role: str = '',
        schedule: Optional[Dict[str, Any]] = None,
    ) -> None:
        schedule_json = json.dumps(schedule or {}, ensure_ascii=False)
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO location_cast (session_id, location_id, actor_uuid, role, schedule_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, location_id, actor_uuid) DO UPDATE SET
                        role=excluded.role,
                        schedule_json=excluded.schedule_json;
                    """,
                    (str(session_id), str(location_id), str(actor_uuid), str(role or ''), schedule_json),
                )
                conn.commit()
            finally:
                conn.close()

    def get_location_cast(self, *, session_id: str, location_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT actor_uuid, role, schedule_json
                    FROM location_cast
                    WHERE session_id = ? AND location_id = ?
                    ORDER BY created_at ASC;
                    """,
                    (str(session_id), str(location_id)),
                ).fetchall()
                out: List[Dict[str, Any]] = []
                for r in rows or []:
                    out.append({
                        'actor_uuid': r['actor_uuid'],
                        'role': r['role'],
                        'schedule': json.loads(r['schedule_json'] or '{}'),
                    })
                return out
            finally:
                conn.close()

    def set_actor_location_state(
        self,
        *,
        session_id: str,
        actor_uuid: str,
        current_location_id: Optional[str],
        presence_state: str,
        en_route_to_location_id: Optional[str] = None,
        eta_world_minutes: Optional[int] = None,
        last_seen_world_minutes: Optional[int] = None,
        follow_target_uuid: Optional[str] = None,
        pursue_target_uuid: Optional[str] = None,
        home_location_id: Optional[str] = None,
    ) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO actor_location_state (
                        session_id, actor_uuid,
                        current_location_id, presence_state,
                        en_route_to_location_id, eta_world_minutes, last_seen_world_minutes,
                        follow_target_uuid, pursue_target_uuid, home_location_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, actor_uuid) DO UPDATE SET
                        current_location_id=excluded.current_location_id,
                        presence_state=excluded.presence_state,
                        en_route_to_location_id=excluded.en_route_to_location_id,
                        eta_world_minutes=excluded.eta_world_minutes,
                        last_seen_world_minutes=excluded.last_seen_world_minutes,
                        follow_target_uuid=excluded.follow_target_uuid,
                        pursue_target_uuid=excluded.pursue_target_uuid,
                        home_location_id=excluded.home_location_id,
                        updated_at=datetime('now');
                    """,
                    (
                        str(session_id),
                        str(actor_uuid),
                        current_location_id,
                        str(presence_state or ''),
                        en_route_to_location_id,
                        int(eta_world_minutes) if eta_world_minutes is not None else None,
                        int(last_seen_world_minutes) if last_seen_world_minutes is not None else None,
                        follow_target_uuid,
                        pursue_target_uuid,
                        home_location_id,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def get_actor_location_state(self, *, session_id: str, actor_uuid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    """
                    SELECT session_id, actor_uuid,
                           current_location_id, presence_state,
                           en_route_to_location_id, eta_world_minutes, last_seen_world_minutes,
                           follow_target_uuid, pursue_target_uuid, home_location_id,
                           updated_at
                    FROM actor_location_state
                    WHERE session_id = ? AND actor_uuid = ?
                    LIMIT 1;
                    """,
                    (str(session_id), str(actor_uuid)),
                ).fetchone()
                if row is None:
                    return None
                return dict(row)
            finally:
                conn.close()

    def remember(
        self,
        *,
        session_id: str,
        actor_id: str,
        memory_type: str,
        content: str,
        importance: int = 5,
        pinned: bool = False,
        initial_strength: float = 1.0,
        decay_rate: float = 0.0005,
        source_event_id: Optional[int] = None,
        world_time: Optional[WorldTime] = None,
    ) -> int:
        world_minutes = world_time.minutes_since_start if world_time else None
        with self._lock:
            conn = self._connect()
            try:
                # Noise reduction: de-dupe consecutive identical memories for same actor/type
                try:
                    row = conn.execute(
                        """
                        SELECT memory_id, content, importance, pinned
                        FROM actor_memory_items
                        WHERE session_id = ? AND actor_id = ? AND memory_type = ?
                        ORDER BY memory_id DESC
                        LIMIT 1;
                        """,
                        (session_id, actor_id, memory_type)
                    ).fetchone()
                    if row is not None and (row["content"] or "") == (content or ""):
                        mem_id = int(row["memory_id"])
                        # Keep the higher importance, and pin if either is pinned
                        new_importance = max(int(row["importance"] or 5), int(importance))
                        new_pinned = 1 if (bool(row["pinned"]) or bool(pinned)) else 0
                        conn.execute(
                            """
                            UPDATE actor_memory_items
                            SET importance = ?, pinned = ?,
                                world_minutes_last_recalled = COALESCE(?, world_minutes_last_recalled)
                            WHERE memory_id = ?;
                            """,
                            (new_importance, new_pinned, world_minutes, mem_id)
                        )
                        conn.commit()
                        return mem_id
                except Exception:
                    pass

                cur = conn.execute(
                    """
                    INSERT INTO actor_memory_items (
                        session_id, actor_id, memory_type, content, source_event_id,
                        importance, pinned, initial_strength, decay_rate,
                        world_minutes_first_seen, world_minutes_last_recalled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        session_id,
                        actor_id,
                        memory_type,
                        content,
                        source_event_id,
                        int(importance),
                        1 if pinned else 0,
                        float(initial_strength),
                        float(decay_rate),
                        world_minutes,
                        world_minutes,
                    ),
                )
                conn.commit()
                return int(cur.lastrowid)
            finally:
                conn.close()

    def recall(
        self,
        *,
        session_id: str,
        actor_id: str,
        query: Optional[str] = None,
        limit: int = 12,
        world_time: Optional[WorldTime] = None,
        min_strength: float = 0.08,
    ) -> List[Dict[str, Any]]:
        now_minutes = world_time.minutes_since_start if world_time else None

        def _norm_content(s: str) -> str:
            try:
                s = (s or '').lower()
                s = re.sub(r"[^a-z0-9\s]+", " ", s)
                s = re.sub(r"\s+", " ", s).strip()
                return s
            except Exception:
                return (s or '').strip().lower()

        sql = """
            SELECT memory_id, memory_type, content, source_event_id,
                   importance, pinned, initial_strength, decay_rate,
                   world_minutes_first_seen, world_minutes_last_recalled, created_at
            FROM actor_memory_items
            WHERE session_id = ? AND actor_id = ?
        """
        params: List[Any] = [session_id, actor_id]

        if query:
            sql += " AND content LIKE ?"
            params.append(f"%{query}%")

        sql += " ORDER BY pinned DESC, importance DESC, memory_id DESC LIMIT ?"
        params.append(int(max(limit * 5, limit)))

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(sql, tuple(params)).fetchall()
                scored: List[Dict[str, Any]] = []
                for r in rows:
                    pinned = bool(r["pinned"]) if r["pinned"] is not None else False
                    initial_strength = float(r["initial_strength"] or 1.0)
                    decay_rate = float(r["decay_rate"] or 0.0)

                    eff_strength = initial_strength
                    if pinned:
                        eff_strength = 1.0
                    elif now_minutes is not None and r["world_minutes_first_seen"] is not None:
                        dt = max(0, int(now_minutes) - int(r["world_minutes_first_seen"]))
                        eff_strength = initial_strength * math.exp(-decay_rate * dt)

                    if not pinned and eff_strength < float(min_strength):
                        continue

                    importance = int(r["importance"] or 5)
                    score = (10.0 if pinned else 0.0) + (importance / 10.0) + eff_strength

                    scored.append({
                        "memory_id": r["memory_id"],
                        "memory_type": r["memory_type"],
                        "content": r["content"],
                        "source_event_id": r["source_event_id"],
                        "importance": importance,
                        "pinned": pinned,
                        "effective_strength": eff_strength,
                        "score": score,
                        "world_minutes_first_seen": r["world_minutes_first_seen"],
                        "world_minutes_last_recalled": r["world_minutes_last_recalled"],
                        "created_at": r["created_at"],
                    })

                scored.sort(key=lambda x: x["score"], reverse=True)

                out: List[Dict[str, Any]] = []
                seen_norm: set = set()
                for m in scored:
                    if len(out) >= int(limit):
                        break
                    try:
                        nc = _norm_content(m.get('content') or '')
                        if nc and nc in seen_norm:
                            continue
                        if nc:
                            seen_norm.add(nc)
                    except Exception:
                        pass
                    out.append(m)

                if now_minutes is not None and out:
                    try:
                        ids = [m["memory_id"] for m in out]
                        placeholders = ",".join(["?"] * len(ids))
                        conn.execute(
                            f"UPDATE actor_memory_items SET world_minutes_last_recalled = ? WHERE memory_id IN ({placeholders});",
                            tuple([int(now_minutes)] + ids)
                        )
                        conn.commit()
                    except Exception:
                        pass

                return out
            finally:
                conn.close()

    def get_latest_position_snapshot(
        self,
        *,
        session_id: str,
        location_id: str,
        limit_entities: int = 250,
    ) -> List[Dict[str, Any]]:
        """Return the latest known row per entity_id for a given location.

        Uses snapshot_id ordering as the authoritative write order.
        """
        query = """
            SELECT ps.*
            FROM position_snapshots ps
            INNER JOIN (
                SELECT entity_id, MAX(snapshot_id) AS max_snapshot_id
                FROM position_snapshots
                WHERE session_id = ? AND location_id = ?
                GROUP BY entity_id
            ) latest
            ON ps.entity_id = latest.entity_id AND ps.snapshot_id = latest.max_snapshot_id
            WHERE ps.session_id = ? AND ps.location_id = ?
            ORDER BY ps.entity_type DESC, ps.entity_name ASC
            LIMIT ?
        """

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    query,
                    (session_id, location_id, session_id, location_id, int(limit_entities))
                ).fetchall()

                out: List[Dict[str, Any]] = []
                for r in rows:
                    out.append({
                        "entity_id": r["entity_id"],
                        "entity_name": r["entity_name"],
                        "entity_type": r["entity_type"],
                        "x": r["x"],
                        "y": r["y"],
                        "facing_direction": r["facing_direction"],
                        "is_active": bool(r["is_active"]) if r["is_active"] is not None else None,
                        "zone_id": r["zone_id"],
                        "world_day": r["world_day"],
                        "world_hour": r["world_hour"],
                        "world_minute": r["world_minute"],
                        "world_minutes_since_start": r["world_minutes_since_start"],
                        "created_at": r["created_at"],
                    })
                return out
            finally:
                conn.close()
