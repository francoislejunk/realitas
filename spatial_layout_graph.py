from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class GraphNode:
    node_id: str
    name: str
    kind: str = "zone"  # e.g. zone/room/corridor
    area_weight: float = 1.0
    tags: List[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    a: str
    b: str
    kind: str = "door"  # door/archway/hallway
    width: float = 1.0
    bidirectional: bool = True


@dataclass
class LayoutGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)


def _normalize_name_key(s: str) -> str:
    return " ".join(str(s or "").lower().strip().split())


def build_layout_graph_for_location(
    *,
    location_name: str,
    location_type: str,
    scene_description: str = "",
) -> LayoutGraph:
    """Return a semantic adjacency/circulation graph (space-first).

    This is intentionally deterministic and lightweight (no LLM calls).
    """

    nm = _normalize_name_key(location_name)
    desc = _normalize_name_key(scene_description)
    ltype = _normalize_name_key(location_type)
    text = f"{nm} {desc} {ltype}".strip()

    g = LayoutGraph()

    def add(nid: str, name: str, *, kind: str = "zone", area_weight: float = 1.0, tags: Optional[List[str]] = None):
        g.add_node(GraphNode(node_id=nid, name=name, kind=kind, area_weight=float(area_weight), tags=list(tags or [])))

    def connect(a: str, b: str, *, kind: str = "door", width: float = 1.0):
        g.add_edge(GraphEdge(a=a, b=b, kind=kind, width=float(width), bidirectional=True))

    # Default fallback: a single main area.
    add("main", "Main Area", area_weight=3.0)

    # Basic pattern detection (expand over time).
    is_tavern = ("tavern" in text) or ("bar" in text) or ("pub" in text)
    is_house = any(k in text for k in ["house", "apartment", "flat", "home"])
    is_office = any(k in text for k in ["office", "cubicle", "workplace"])

    if is_tavern:
        g = LayoutGraph()
        add("public", "Public Floor", area_weight=4.0, tags=["public"])
        add("bar", "Bar Counter", area_weight=1.5, tags=["service", "anchor"])
        add("seating", "Seating", area_weight=2.5, tags=["public"])
        add("back", "Back Room", area_weight=1.2, tags=["staff"])
        add("restroom", "Restroom", area_weight=0.8, tags=["public"])

        connect("public", "bar", kind="archway", width=2.0)
        connect("public", "seating", kind="open", width=3.0)
        connect("public", "restroom", kind="door", width=1.0)
        connect("bar", "back", kind="door", width=1.0)

    elif is_house:
        g = LayoutGraph()
        add("living", "Living Area", area_weight=3.0, tags=["public"])
        add("kitchen", "Kitchen", area_weight=2.0, tags=["public", "service"])
        add("bed", "Bedroom", area_weight=2.0, tags=["private"])
        add("bath", "Bathroom", area_weight=1.0, tags=["private"])

        connect("living", "kitchen", kind="archway", width=1.5)
        connect("living", "bed", kind="door", width=1.0)
        connect("bed", "bath", kind="door", width=1.0)

    elif is_office:
        g = LayoutGraph()
        add("work", "Work Area", area_weight=3.0, tags=["public"])
        add("mgr", "Manager Office", area_weight=1.5, tags=["private"])
        add("storage", "Storage", area_weight=1.0, tags=["service"])

        connect("work", "mgr", kind="door", width=1.0)
        connect("work", "storage", kind="door", width=1.0)

    return g


def embed_graph_as_rect_zones(
    *,
    graph: LayoutGraph,
    width: float,
    height: float,
    padding_ratio: float = 0.06,
) -> Dict[str, List[Tuple[float, float]]]:
    """Embed a LayoutGraph into simple rectangular polygons.

    Returns: dict[node_id] -> polygon[(x,y),...]

    This is a first-pass embedder: it preserves *relative* size via area_weight
    and ensures all zones are within bounds.
    """

    w = float(width or 0.0)
    h = float(height or 0.0)
    if w <= 0.0 or h <= 0.0 or not graph.nodes:
        return {}

    pad_x = max(1.0, w * float(padding_ratio))
    pad_y = max(1.0, h * float(padding_ratio))

    usable_w = max(1.0, w - 2 * pad_x)
    usable_h = max(1.0, h - 2 * pad_y)

    nodes = list(graph.nodes.values())
    nodes.sort(key=lambda n: float(getattr(n, "area_weight", 1.0) or 1.0), reverse=True)

    polys: Dict[str, List[Tuple[float, float]]] = {}

    if len(nodes) == 1:
        x0 = pad_x
        y0 = pad_y
        x1 = pad_x + usable_w
        y1 = pad_y + usable_h
        polys[nodes[0].node_id] = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return polys

    # Hub in center.
    hub = nodes[0]
    hub_w = usable_w * 0.62
    hub_h = usable_h * 0.62
    hub_x0 = pad_x + (usable_w - hub_w) / 2.0
    hub_y0 = pad_y + (usable_h - hub_h) / 2.0
    hub_x1 = hub_x0 + hub_w
    hub_y1 = hub_y0 + hub_h
    polys[hub.node_id] = [(hub_x0, hub_y0), (hub_x1, hub_y0), (hub_x1, hub_y1), (hub_x0, hub_y1)]

    # Perimeter bands for remaining zones.
    remaining = nodes[1:]
    top_band = (pad_x, hub_y1, pad_x + usable_w, pad_y + usable_h)
    bottom_band = (pad_x, pad_y, pad_x + usable_w, hub_y0)
    left_band = (pad_x, hub_y0, hub_x0, hub_y1)
    right_band = (hub_x1, hub_y0, pad_x + usable_w, hub_y1)

    bands = [bottom_band, top_band, left_band, right_band]

    def band_capacity(b: Tuple[float, float, float, float]) -> float:
        bx0, by0, bx1, by1 = b
        return max(1.0, (bx1 - bx0) * (by1 - by0))

    band_caps = [band_capacity(b) for b in bands]

    total_weight = sum(max(0.1, float(n.area_weight or 1.0)) for n in remaining)

    for i, node in enumerate(remaining):
        b = bands[i % len(bands)]
        bx0, by0, bx1, by1 = b
        bw = max(1.0, bx1 - bx0)
        bh = max(1.0, by1 - by0)

        wt = max(0.1, float(node.area_weight or 1.0))
        share = min(0.85, max(0.2, wt / max(0.1, total_weight)))

        # Prefer long-thin rectangles along bands.
        if bw >= bh:
            rw = max(2.0, bw * share)
            rh = max(2.0, bh * 0.85)
        else:
            rw = max(2.0, bw * 0.85)
            rh = max(2.0, bh * share)

        # Deterministic placement within band.
        frac = (i + 1) / (len(remaining) + 1)
        rx0 = bx0 + (bw - rw) * frac
        ry0 = by0 + (bh - rh) * frac
        rx1 = rx0 + rw
        ry1 = ry0 + rh

        # Clamp.
        rx0 = min(max(rx0, pad_x), pad_x + usable_w - 1.0)
        ry0 = min(max(ry0, pad_y), pad_y + usable_h - 1.0)
        rx1 = min(max(rx1, rx0 + 1.0), pad_x + usable_w)
        ry1 = min(max(ry1, ry0 + 1.0), pad_y + usable_h)

        polys[node.node_id] = [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]

    return polys
