"""
pygame_narrative_display.py

Pygame-based frontend display window for Realitas Neo.

Architecture: subprocess + TCP socket IPC
  - When imported by redesigned_main.py, spawns THIS file as a separate subprocess
    with --server <port>.  Each process has its own pygame instance — no thread
    conflicts with the spatial map.
  - Protocol: newline-delimited JSON over a loopback TCP socket.
    game  -> display : {"type": "scene"|"narrator"|..., "text": "..."}
    game  -> display : {"type": "input_request", "prompt": "..."}
    display -> game  : {"type": "input", "text": "..."}

Public API (same as before — redesigned_main.py unchanged):
    start_narrative_display() -> bool
    stop_narrative_display()
    send_scene(text), send_narrator(text), send_perceptual(text),
    send_internal_voice(text), send_iv_exchange_iv(text), send_iv_exchange_ua(text),
    send_separator(), send_system(text)
    get_input_from_display(prompt) -> Optional[str]
    make_input_func() -> callable
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ─── pygame only needed when running as the display server ───────────────────
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class MessageType(Enum):
    SCENE          = "scene"
    NARRATOR       = "narrator"
    PERCEPTUAL     = "perceptual"
    INTERNAL_VOICE = "iv"
    IV_VOICE       = "iv_voice"
    IV_UA          = "iv_ua"
    SYSTEM         = "system"
    SEPARATOR      = "separator"
    PROMPT         = "prompt"
    USER_INPUT     = "user_input"


@dataclass
class Message:
    text: str
    msg_type: MessageType = MessageType.NARRATOR
    timestamp: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════════════════════
# THEME
# ═══════════════════════════════════════════════════════════════════════════════

BG_COLOR    = (13,  13,  20)
BG_HEADER   = (8,   8,  14)
BG_INPUT    = (18,  18,  30)
CHROME_LINE = (32,  28,  50)

TITLE_COLOR  = (155, 148, 200)
STATUS_COLOR = (70,   65, 100)

TYPE_COLORS: Dict[MessageType, Tuple] = {
    MessageType.SCENE:          (200, 180, 255),
    MessageType.NARRATOR:       (218, 212, 202),
    MessageType.PERCEPTUAL:     (145, 138, 158),
    MessageType.INTERNAL_VOICE: (140, 218, 232),
    MessageType.IV_VOICE:       (210, 168, 252),
    MessageType.IV_UA:          (160, 238, 185),
    MessageType.SYSTEM:         (100, 158, 208),
    MessageType.SEPARATOR:      (40,   38,  60),
    MessageType.PROMPT:         (240, 214, 128),
    MessageType.USER_INPUT:     (240, 214, 128),
}

ACCENT_COLORS: Dict[MessageType, Optional[Tuple]] = {
    MessageType.SCENE:          (130, 100, 210),
    MessageType.NARRATOR:       None,
    MessageType.PERCEPTUAL:     (80,  72, 100),
    MessageType.INTERNAL_VOICE: (75, 185, 210),
    MessageType.IV_VOICE:       (165, 110, 220),
    MessageType.IV_UA:          (90, 195, 130),
    MessageType.SYSTEM:         None,
    MessageType.SEPARATOR:      None,
    MessageType.PROMPT:         (195, 165,  70),
    MessageType.USER_INPUT:     (195, 165,  70),
}

BG_TINTS: Dict[MessageType, Optional[Tuple]] = {
    MessageType.SCENE:          (20,  16,  32),
    MessageType.NARRATOR:       None,
    MessageType.PERCEPTUAL:     None,
    MessageType.INTERNAL_VOICE: (13,  20,  30),
    MessageType.IV_VOICE:       (20,  14,  30),
    MessageType.IV_UA:          (12,  22,  18),
    MessageType.SYSTEM:         None,
    MessageType.SEPARATOR:      None,
    MessageType.PROMPT:         (22,  20,  12),
    MessageType.USER_INPUT:     (22,  20,  12),
}

BORDER_IDLE   = (42,  38,  62)
BORDER_ACTIVE = (115,  85, 175)
BAR_BG  = (20,  18,  30)
BAR_FG  = (58,  52,  84)

DEFAULT_W   = 920
DEFAULT_H   = 1024   # MAP_H(280) + DIVIDER_H(4) + original 740
HEADER_H    = 34
INPUT_H     = 56
SCROLLBAR_W = 6
PAD         = 16
ACCENT_W    = 3
ACCENT_MARG = 6
ACCENT_PAD  = 10
MSG_PAD_Y   = 7
MSG_GAP     = 2
LINE_GAP    = 3
FONT_BODY   = 15
FONT_LABEL  = 11
FONT_INPUT  = 15
FONT_TITLE  = 13
MAX_MSGS    = 600
SCROLL_SPD  = 45

# ── Map panel (top of window) ─────────────────────────────────────────────────
MAP_H       = 280           # Height of the map panel
DIVIDER_H   = 4             # Divider line between map and narrative
MAP_PAD     = 12            # Padding inside map panel
MAP_BG      = (245, 240, 230)   # Parchment background
MAP_FLOOR   = (250, 245, 235)   # Interior floor
MAP_WALL    = (30,   30,  30)   # Wall / border colour
MAP_DIVIDER = (42,   38,  62)   # Same as CHROME_LINE for the divider bar


@dataclass
class Block:
    msg_type: MessageType
    lines:  List[str]
    color:  Tuple
    accent: Optional[Tuple]
    bg:     Optional[Tuple]
    label:  Optional[str]
    height: int


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY SERVER  (runs in the subprocess)
# ═══════════════════════════════════════════════════════════════════════════════

class NarrativeDisplayServer:
    """
    Pygame window.  Listens for JSON commands on a TCP socket.
    Runs entirely in the display subprocess — no threading conflicts.
    """

    def __init__(self, port: int):
        self._port = port
        self._messages: List[Message] = []
        self._scroll_px: int = 0
        self._input_text = ""
        self._input_cursor = 0
        self._waiting_for_input = False
        self._pending_input_conn = None   # socket waiting for user's reply
        self._screen = None
        self._font_body = self._font_label = self._font_input = self._font_title = None
        self._clock = None
        self._vessel_name: str = ""   # set once vessel is chosen
        self._map_state: dict = {}    # last map state received from game

    def run(self):
        if not PYGAME_AVAILABLE:
            print("[NarrativeDisplay] pygame not available — server exiting")
            return

        os.environ.setdefault('SDL_VIDEO_WINDOW_POS', '960,50')
        pygame.init()
        pygame.key.set_repeat(350, 45)
        self._screen = pygame.display.set_mode((DEFAULT_W, DEFAULT_H), pygame.RESIZABLE)
        pygame.display.set_caption("Realitas Neo  —  Narrative")
        self._font_body, self._font_label, self._font_input, self._font_title = self._load_fonts()
        self._clock = pygame.time.Clock()

        # Accept connections in a background thread
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('127.0.0.1', self._port))
        server_sock.listen(5)
        server_sock.setblocking(False)

        conns: List[socket.socket] = []
        buffers: Dict[int, bytes] = {}

        self._messages.append(Message("", MessageType.SEPARATOR))

        while True:
            # ── accept new connections ────────────────────────────────────────
            try:
                conn, _ = server_sock.accept()
                conn.setblocking(False)
                conns.append(conn)
                buffers[id(conn)] = b""
            except BlockingIOError:
                pass

            # ── read from connections ─────────────────────────────────────────
            dead = []
            for conn in conns:
                try:
                    chunk = conn.recv(4096)
                    if not chunk:
                        dead.append(conn)
                        continue
                    buffers[id(conn)] += chunk
                    while b"\n" in buffers[id(conn)]:
                        line, buffers[id(conn)] = buffers[id(conn)].split(b"\n", 1)
                        try:
                            msg = json.loads(line.decode("utf-8"))
                            self._handle_message(msg, conn)
                        except Exception:
                            pass
                except BlockingIOError:
                    pass
                except Exception:
                    dead.append(conn)
            for c in dead:
                conns.remove(c)
                buffers.pop(id(c), None)

            # ── pygame events ─────────────────────────────────────────────────
            for event in pygame.event.get():
                self._handle_event(event)

            self._draw()
            pygame.display.flip()
            self._clock.tick(30)

    def _handle_message(self, msg: dict, conn: socket.socket):
        mtype = msg.get("type", "narrator")
        if mtype == "vessel_name":
            self._vessel_name = msg.get("name", "")
            return
        if mtype == "map_state":
            self._map_state = msg.get("state", {})
            return
        if mtype == "input_request":
            self._waiting_for_input = True
            self._pending_input_conn = conn
            # Don't add the prompt text as a message block — the header
            # already shows "Your turn, Elias." when waiting for input.
        elif mtype == "separator":
            self._messages.append(Message("", MessageType.SEPARATOR))
            if len(self._messages) > MAX_MSGS:
                self._messages = self._messages[-MAX_MSGS:]
        elif mtype == "stop":
            pygame.quit()
            sys.exit(0)
        else:
            try:
                mt = MessageType(mtype)
            except ValueError:
                mt = MessageType.NARRATOR
            text = msg.get("text", "")
            if text:
                self._messages.append(Message(text, mt))
                if len(self._messages) > MAX_MSGS:
                    self._messages = self._messages[-MAX_MSGS:]
                if self._scroll_px <= 0:
                    self._scroll_px = 0

    def _handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)

        if event.type == pygame.MOUSEWHEEL:
            self._scroll_px = max(0, self._scroll_px - event.y * SCROLL_SPD)
            return

        if event.type != pygame.KEYDOWN:
            return

        k = event.key
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            text = self._input_text.strip()
            self._input_text = ""
            self._input_cursor = 0
            if text:
                self._messages.append(Message(text, MessageType.USER_INPUT))
                self._scroll_px = 0
            if self._waiting_for_input and self._pending_input_conn:
                try:
                    reply = json.dumps({"type": "input", "text": text}) + "\n"
                    self._pending_input_conn.sendall(reply.encode("utf-8"))
                except Exception:
                    pass
                self._waiting_for_input = False
                self._pending_input_conn = None
            else:
                # Even if not waiting, still send so game can receive
                pass

        elif k == pygame.K_BACKSPACE:
            if self._input_cursor > 0:
                self._input_text = (self._input_text[:self._input_cursor - 1]
                                    + self._input_text[self._input_cursor:])
                self._input_cursor -= 1
        elif k == pygame.K_DELETE:
            if self._input_cursor < len(self._input_text):
                self._input_text = (self._input_text[:self._input_cursor]
                                    + self._input_text[self._input_cursor + 1:])
        elif k == pygame.K_LEFT:
            self._input_cursor = max(0, self._input_cursor - 1)
        elif k == pygame.K_RIGHT:
            self._input_cursor = min(len(self._input_text), self._input_cursor + 1)
        elif k == pygame.K_HOME:
            self._input_cursor = 0
        elif k == pygame.K_END:
            self._input_cursor = len(self._input_text)
        elif k == pygame.K_PAGEUP:
            self._scroll_px = min(self._scroll_px + 200, 99999)
        elif k == pygame.K_PAGEDOWN:
            self._scroll_px = max(0, self._scroll_px - 200)
        elif event.unicode and ord(event.unicode) >= 32:
            self._input_text = (self._input_text[:self._input_cursor]
                                + event.unicode
                                + self._input_text[self._input_cursor:])
            self._input_cursor += 1

    # ── fonts ─────────────────────────────────────────────────────────────────

    def _load_fonts(self):
        for name in ["Consolas", "Courier New", "Lucida Console",
                     "DejaVu Sans Mono", "Liberation Mono", "Courier"]:
            try:
                return (pygame.font.SysFont(name, FONT_BODY),
                        pygame.font.SysFont(name, FONT_LABEL, bold=True),
                        pygame.font.SysFont(name, FONT_INPUT),
                        pygame.font.SysFont(name, FONT_TITLE, bold=True))
            except Exception:
                continue
        fb = pygame.font.Font(None, FONT_BODY + 4)
        return fb, fb, fb, fb

    # ── word wrap ─────────────────────────────────────────────────────────────

    def _wrap(self, text: str, font, max_w: int) -> List[str]:
        if not text:
            return []
        lines = []
        for para in text.split('\n'):
            if not para.strip():
                lines.append(""); continue
            words, cur = para.split(' '), ""
            for word in words:
                cand = (cur + " " + word).strip() if cur else word
                if font.size(cand)[0] <= max_w:
                    cur = cand
                else:
                    if cur:
                        lines.append(cur)
                    if font.size(word)[0] > max_w:
                        part = ""
                        for ch in word:
                            if font.size(part + ch)[0] <= max_w:
                                part += ch
                            else:
                                if part: lines.append(part)
                                part = ch
                        cur = part
                    else:
                        cur = word
            if cur:
                lines.append(cur)
        return lines or [""]

    # ── block builder ─────────────────────────────────────────────────────────

    def _make_block(self, msg: Message, text_w: int) -> Block:
        line_h = self._font_body.get_linesize() + LINE_GAP
        if msg.msg_type == MessageType.SEPARATOR:
            return Block(MessageType.SEPARATOR, [], TYPE_COLORS[MessageType.SEPARATOR],
                         None, None, None, 14)
        vessel = self._vessel_name or "You"
        label_map = {
            MessageType.SCENE:          "Perception",
            MessageType.INTERNAL_VOICE: "Inner Voice",
            MessageType.IV_VOICE:       "Inner Voice",
            MessageType.IV_UA:          vessel,
            MessageType.PROMPT:         vessel,
            MessageType.USER_INPUT:     vessel,
            MessageType.SYSTEM:         None,
            MessageType.NARRATOR:       "Perception",
            MessageType.PERCEPTUAL:     "Perception",
        }
        label = label_map.get(msg.msg_type)
        indented = msg.msg_type in (MessageType.PERCEPTUAL,)
        effective_w = text_w - (12 if indented else 0)
        display_text = msg.text
        lines = self._wrap(display_text, self._font_body, effective_w)
        label_h = (self._font_label.get_linesize() + 4) if label else 0
        total_h = label_h + len(lines) * line_h + MSG_PAD_Y * 2 + MSG_GAP
        return Block(
            msg_type=msg.msg_type,
            lines=lines,
            color=TYPE_COLORS.get(msg.msg_type, TYPE_COLORS[MessageType.NARRATOR]),
            accent=ACCENT_COLORS.get(msg.msg_type),
            bg=BG_TINTS.get(msg.msg_type),
            label=label,
            height=total_h,
        )

    # ── draw ──────────────────────────────────────────────────────────────────

    def _draw_map(self, w: int):
        """Render the mini-map panel at the top of the window."""
        s = self._screen
        pygame.draw.rect(s, MAP_BG, (0, 0, w, MAP_H))

        if not self._map_state:
            placeholder = self._font_label.render("[ Awaiting map data... ]", True, (160, 150, 130))
            s.blit(placeholder, (PAD, (MAP_H - placeholder.get_height()) // 2))
            return

        location_name = self._map_state.get("location_name", "Unknown Location")
        map_w = float(self._map_state.get("width", 20.0))
        map_h = float(self._map_state.get("height", 20.0))
        actors    = self._map_state.get("actors", {})
        obstacles = self._map_state.get("obstacles", {})

        # Location name (top-left)
        loc_surf = self._font_label.render(location_name.upper(), True, (80, 70, 55))
        s.blit(loc_surf, (PAD, MAP_PAD))

        # Map drawing area (below location name label)
        name_h  = self._font_label.get_linesize() + 4
        area_t  = MAP_PAD + name_h + 4
        area_l  = MAP_PAD
        area_w  = w - MAP_PAD * 2
        area_h  = MAP_H - area_t - MAP_PAD

        if map_w <= 0 or map_h <= 0 or area_w <= 0 or area_h <= 0:
            return

        # Scale to fit, maintaining aspect ratio
        scale = min(area_w / map_w, area_h / map_h)
        drawn_w = map_w * scale
        drawn_h = map_h * scale
        off_x = area_l + (area_w - drawn_w) / 2
        off_y = area_t + (area_h - drawn_h) / 2

        def w2s(wx: float, wy: float) -> Tuple[int, int]:
            return (int(off_x + wx * scale), int(off_y + wy * scale))

        # Floor + border
        pygame.draw.rect(s, MAP_FLOOR, (int(off_x), int(off_y), int(drawn_w), int(drawn_h)))
        pygame.draw.rect(s, MAP_WALL,  (int(off_x), int(off_y), int(drawn_w), int(drawn_h)), 2)

        # Obstacles (furniture / inanimate actors)
        for obs in obstacles.values():
            ox, oy = w2s(obs.get("x", 0), obs.get("y", 0))
            ow = max(4, int(obs.get("width",  2) * scale))
            oh = max(4, int(obs.get("height", 2) * scale))
            pygame.draw.rect(s, (140, 100, 70), (ox, oy, ow, oh))

        # Actor colour map
        _ACTOR_COLORS = {
            "ua":   (50,  150, 80),
            "nua":  (70,  130, 200),
            "mnua": (220, 180, 50),
            "inua": (140, 100, 70),
        }
        # Draw actors
        for act in actors.values():
            atype  = act.get("type", "nua")
            color  = _ACTOR_COLORS.get(atype, (100, 100, 100))
            ax, ay = w2s(act.get("x", 0), act.get("y", 0))
            radius = max(3, min(8, int(scale * 0.8)))
            pygame.draw.circle(s, color, (ax, ay), radius)
            pygame.draw.circle(s, MAP_WALL, (ax, ay), radius, 1)
            name_lbl = self._font_label.render(act.get("name", "?")[:10], True, (30, 30, 30))
            s.blit(name_lbl, (ax + radius + 2, ay - name_lbl.get_height() // 2))

    def _draw(self):
        s = self._screen
        w, h = s.get_size()
        s.fill(BG_COLOR)
        self._draw_map(w)
        pygame.draw.rect(s, MAP_DIVIDER, (0, MAP_H, w, DIVIDER_H))
        self._draw_header(w)
        self._draw_messages(w, h)
        self._draw_input(w, h)

    def _draw_header(self, w):
        s = self._screen
        top = MAP_H + DIVIDER_H
        pygame.draw.rect(s, BG_HEADER, (0, top, w, HEADER_H))
        pygame.draw.line(s, CHROME_LINE, (0, top + HEADER_H), (w, top + HEADER_H), 1)
        ts = self._font_title.render("REALITAS  NEO", True, TITLE_COLOR)
        s.blit(ts, (PAD, top + (HEADER_H - ts.get_height()) // 2))
        dot_col = (85, 195, 115) if self._waiting_for_input else (55, 50, 80)
        dx, dy = w - PAD - 6, top + HEADER_H // 2
        pygame.draw.circle(s, dot_col, (dx, dy), 5)
        if self._waiting_for_input:
            vessel = self._vessel_name or "You"
            waiting_text = f"Your turn, {vessel}." if self._vessel_name else "Your turn."
            lbl = self._font_label.render(waiting_text, True, (85, 195, 115))
            s.blit(lbl, (dx - lbl.get_width() - 10, top + (HEADER_H - lbl.get_height()) // 2))

    def _draw_messages(self, w, h):
        s = self._screen
        ta_top = MAP_H + DIVIDER_H + HEADER_H + 1
        ta_h   = h - MAP_H - DIVIDER_H - HEADER_H - INPUT_H - 1
        ta_w   = w - SCROLLBAR_W - 1
        line_h   = self._font_body.get_linesize() + LINE_GAP
        label_lh = self._font_label.get_linesize() + 4
        text_x0  = PAD + ACCENT_MARG + ACCENT_W + ACCENT_PAD
        text_w   = ta_w - text_x0 - PAD

        blocks = [self._make_block(m, text_w) for m in self._messages]
        total_h = sum(b.height for b in blocks)
        max_scroll = max(0, total_h - ta_h)
        self._scroll_px = min(self._scroll_px, max_scroll)
        viewport_start = max(0, total_h - ta_h - self._scroll_px)

        s.set_clip(pygame.Rect(0, ta_top, ta_w, ta_h))
        content_y = 0
        for block in blocks:
            if content_y + block.height <= viewport_start:
                content_y += block.height; continue
            if content_y >= viewport_start + ta_h:
                break
            draw_y = ta_top + (content_y - viewport_start)

            if block.msg_type == MessageType.SEPARATOR:
                sy = draw_y + block.height // 2
                pygame.draw.line(s, block.color, (PAD, sy), (ta_w - PAD, sy), 1)
                content_y += block.height; continue

            if block.bg:
                pygame.draw.rect(s, block.bg, (0, draw_y, ta_w, block.height))
            if block.accent:
                pygame.draw.rect(s, block.accent,
                                 pygame.Rect(ACCENT_MARG, draw_y + 4, ACCENT_W, block.height - 8),
                                 border_radius=2)
            ty = draw_y + MSG_PAD_Y
            if block.label:
                badge = self._font_label.render(block.label, True, block.accent or block.color)
                s.blit(badge, (text_x0, ty))
                ty += label_lh
            extra_x = 8 if block.msg_type == MessageType.PERCEPTUAL else 0
            for line in block.lines:
                if line:
                    s.blit(self._font_body.render(line, True, block.color), (text_x0 + extra_x, ty))
                ty += line_h
            content_y += block.height

        s.set_clip(None)
        pygame.draw.line(s, CHROME_LINE, (ta_w, ta_top), (ta_w, ta_top + ta_h), 1)
        sb_x = ta_w + 1
        pygame.draw.rect(s, BAR_BG, (sb_x, ta_top, SCROLLBAR_W, ta_h))
        if total_h > ta_h:
            ratio   = ta_h / total_h
            thumb_h = max(20, int(ta_h * ratio))
            frac    = self._scroll_px / max(1, max_scroll)
            thumb_y = ta_top + int((ta_h - thumb_h) * (1.0 - frac))
            pygame.draw.rect(s, BAR_FG,
                             (sb_x + 1, thumb_y, SCROLLBAR_W - 2, thumb_h),
                             border_radius=3)

    def _draw_input(self, w, h):
        s = self._screen
        pygame.draw.rect(s, BG_HEADER, (0, h - INPUT_H, w, INPUT_H))
        pygame.draw.line(s, CHROME_LINE, (0, h - INPUT_H), (w, h - INPUT_H), 1)
        box_l, box_r = PAD, w - PAD
        box_t, box_b = h - INPUT_H + 10, h - 10
        box_h = box_b - box_t
        border = BORDER_ACTIVE if self._waiting_for_input else BORDER_IDLE
        pygame.draw.rect(s, BG_INPUT,  (box_l, box_t, box_r - box_l, box_h), border_radius=4)
        pygame.draw.rect(s, border,    (box_l, box_t, box_r - box_l, box_h), 1, border_radius=4)
        pc = TYPE_COLORS[MessageType.PROMPT] if self._waiting_for_input else (60, 56, 88)
        ps = self._font_input.render(">", True, pc)
        baseline = box_t + (box_h - ps.get_height()) // 2
        s.blit(ps, (box_l + 10, baseline))

        input_x = box_l + 28
        avail_w = box_r - input_x - 12
        s.set_clip(pygame.Rect(input_x, box_t, avail_w, box_h))
        full = self._font_input.render(self._input_text, True, TYPE_COLORS[MessageType.USER_INPUT])
        cursor_px = self._font_input.size(self._input_text[:self._input_cursor])[0]
        text_scroll = max(0, cursor_px - avail_w + 20)
        s.blit(full, (input_x - text_scroll, baseline))
        if int(time.time() * 2) % 2 == 0:
            cx = input_x + cursor_px - text_scroll
            pygame.draw.rect(s, TYPE_COLORS[MessageType.USER_INPUT],
                             (cx, baseline, 2, self._font_input.get_height()))
        s.set_clip(None)


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT  (runs in the game process — imported by redesigned_main.py)
# ═══════════════════════════════════════════════════════════════════════════════

class NarrativeDisplayClient:
    """
    Thin client that talks to the display server subprocess via TCP.
    All public methods are thread-safe (send is best-effort, get_input blocks).
    """

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._port: int = 0
        self._lock = threading.Lock()
        self._input_sock: Optional[socket.socket] = None  # persistent connection for input

    def start(self) -> bool:
        # Prefer pmap's embedded narrative server (keeps map+narrative in one window)
        try:
            from pygame_spatial_map import get_pygame_map
            pmap = get_pygame_map()
            if pmap and pmap.running:
                # Wait up to 4 s for pmap to open the narrative TCP server
                deadline = time.time() + 4.0
                while time.time() < deadline:
                    port = getattr(pmap, '_nar_port', 0)
                    if port > 0:
                        try:
                            _s = socket.create_connection(("127.0.0.1", port), timeout=0.5)
                            _s.close()
                            self._port = port
                            self._proc = None   # no subprocess needed
                            print(f"[NarrativeDisplay] Connected to pmap integrated server (port {port})")
                            return True
                        except (ConnectionRefusedError, OSError):
                            pass
                    time.sleep(0.05)
        except Exception:
            pass

        # Fallback: spawn our own subprocess window
        port = self._find_free_port()
        self._port = port
        try:
            self._proc = subprocess.Popen(
                [sys.executable, __file__, "--server", str(port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"[NarrativeDisplay] Failed to start subprocess: {e}")
            return False
        # Wait for server to be ready
        deadline = time.time() + 6.0
        while time.time() < deadline:
            try:
                s = socket.create_connection(("127.0.0.1", port), timeout=0.5)
                s.close()
                break
            except (ConnectionRefusedError, OSError):
                time.sleep(0.1)
        else:
            print("[NarrativeDisplay] Server did not start in time")
            return False
        print("[NarrativeDisplay] Frontend display (subprocess) started OK")
        return True

    def stop(self):
        self._send_raw({"type": "stop"})
        if self._proc:
            try:
                self._proc.wait(timeout=2)
            except Exception:
                self._proc.kill()
            self._proc = None
        if self._input_sock:
            try: self._input_sock.close()
            except Exception: pass
            self._input_sock = None

    @property
    def is_running(self) -> bool:
        if self._proc is not None:
            return self._proc.poll() is None
        # Subprocess-less mode: connected to pmap's narrative server
        return self._port > 0

    def send(self, text: str, msg_type: MessageType = MessageType.NARRATOR):
        if text:
            self._send_raw({"type": msg_type.value, "text": text})

    def set_vessel_name(self, name: str):
        self._send_raw({"type": "vessel_name", "name": name})

    def send_map_state(self, state_dict: dict):
        """Push current map state to the display server for rendering in the map panel."""
        self._send_raw({"type": "map_state", "state": state_dict})

    def separator(self):
        self._send_raw({"type": "separator"})

    def get_input(self, prompt: str = "") -> str:
        """Block until user submits text in the display window."""
        if not self.is_running:
            if prompt: print(prompt, end="", flush=True)
            return input().strip()
        # Open a dedicated connection for this request (keeps response matched)
        try:
            conn = socket.create_connection(("127.0.0.1", self._port), timeout=10)
        except Exception:
            if prompt: print(prompt, end="", flush=True)
            return input().strip()

        req = json.dumps({"type": "input_request", "prompt": prompt}) + "\n"
        conn.sendall(req.encode("utf-8"))

        # Read response (may take a while — user is typing)
        buf = b""
        conn.settimeout(None)  # wait indefinitely
        try:
            while b"\n" not in buf:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                buf += chunk
            if b"\n" in buf:
                line = buf.split(b"\n")[0]
                resp = json.loads(line.decode("utf-8"))
                return resp.get("text", "")
        except Exception:
            pass
        finally:
            conn.close()
        return ""

    # ── internal helpers ─────────────────────────────────────────────────────

    def _find_free_port(self) -> int:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def _send_raw(self, obj: dict):
        if not self.is_running:
            return
        with self._lock:
            try:
                conn = socket.create_connection(("127.0.0.1", self._port), timeout=2)
                conn.sendall((json.dumps(obj) + "\n").encode("utf-8"))
                conn.close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE & CONVENIENCE API
# ═══════════════════════════════════════════════════════════════════════════════

_client: Optional[NarrativeDisplayClient] = None


def get_narrative_display() -> Optional[NarrativeDisplayClient]:
    return _client


def start_narrative_display() -> bool:
    global _client
    if not PYGAME_AVAILABLE:
        return False
    _client = NarrativeDisplayClient()
    return _client.start()


def stop_narrative_display():
    global _client
    if _client:
        _client.stop()
        _client = None


def send_to_display(text: str, msg_type: MessageType = MessageType.NARRATOR):
    if _client and _client.is_running:
        _client.send(text, msg_type)


def send_scene(text: str):          send_to_display(text, MessageType.SCENE)
def send_narrator(text: str):       send_to_display(text, MessageType.NARRATOR)
def send_perceptual(text: str):     send_to_display(text, MessageType.PERCEPTUAL)
def send_internal_voice(text: str): send_to_display(text, MessageType.INTERNAL_VOICE)
def send_iv_exchange_iv(text: str): send_to_display(text, MessageType.IV_VOICE)
def send_iv_exchange_ua(text: str): send_to_display(text, MessageType.IV_UA)

def set_vessel_name(name: str):
    if _client and _client.is_running:
        _client.set_vessel_name(name)

def send_separator():
    if _client and _client.is_running:
        _client.separator()

send_display_separator = send_separator

def send_map_state(state_dict: dict):
    """Push map state to the display window for rendering in the top map panel."""
    if _client and _client.is_running:
        _client.send_map_state(state_dict)

def send_system(text: str): send_to_display(text, MessageType.SYSTEM)
send_display_system = send_system


def get_input_from_display(prompt: str = "") -> Optional[str]:
    if _client and _client.is_running:
        return _client.get_input(prompt)
    return None


def make_input_func():
    def _prompt(prompt_str: str = "") -> str:
        result = get_input_from_display(prompt_str)
        if result is None:
            return input(prompt_str)
        return result
    return _prompt


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT — subprocess server mode
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--server":
        port = int(sys.argv[2])
        server = NarrativeDisplayServer(port)
        server.run()
    else:
        # Standalone test
        print("Testing NarrativeDisplay (subprocess mode)...")
        if not PYGAME_AVAILABLE:
            print("pygame not installed.")
            sys.exit(1)

        ok = start_narrative_display()
        if not ok:
            print("Failed to start.")
            sys.exit(1)

        time.sleep(0.3)
        send_separator()
        send_scene(
            "You stand in a narrow hallway, the wallpaper peeling in long strips. "
            "A single bulb flickers overhead. At the far end, a door — slightly ajar. "
            "The air carries the faint smell of old wood and cold stone."
        )
        time.sleep(0.3)
        send_narrator(
            "You step forward. Your footsteps echo against the bare floorboards. "
            "The door swings open at your touch with a low creak."
        )
        time.sleep(0.2)
        send_perceptual("Your fingers brush the cold wood. The door gives under the lightest pressure.")
        time.sleep(0.3)
        send_separator()
        send_internal_voice("Something about this room feels wrong. We have been here before — haven't we?")
        time.sleep(0.3)
        send_separator()
        send_iv_exchange_iv("What have we done... this is not who we are. The choice was ours alone.")

        text = get_input_from_display("What do you want to do?")
        print(f"[Test] Input: {repr(text)}")

        send_perceptual("You push the thought aside, eyes fixed on the doorway ahead.")
        send_iv_exchange_iv("Moving away from this doesn't move it. Every step you take, we take with you.")

        text2 = get_input_from_display("Your final position?")
        print(f"[Test] Final: {repr(text2)}")

        send_separator()
        send_system("Exchange complete. Spirit impact calculated.")
        time.sleep(2)
        stop_narrative_display()
        print("Done.")
