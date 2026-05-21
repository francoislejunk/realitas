"""
Tests for axis-aligned adjacency positioning fix.
Rule: when moving to obstacle/actor at (cx, cy), the final position must be
exactly 1 unit away on ONE axis only — the dominant approach axis.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))

from agents.architect_agent import _axis_adjacent

PASS = []
FAIL = []

def check(name, condition, detail=""):
    if condition:
        print(f"  PASS  {name}")
        PASS.append(name)
    else:
        print(f"  FAIL  {name}" + (f"  [{detail}]" if detail else ""))
        FAIL.append(name)

def is_axis_aligned_adjacent(result, center_x, center_y, tol=0.001):
    """Return True if result is exactly 1 unit from center on ONE axis."""
    rx, ry = result
    dx = abs(rx - center_x)
    dy = abs(ry - center_y)
    # One axis diff = 1.0, other = 0.0
    return (abs(dx - 1.0) < tol and dy < tol) or (dx < tol and abs(dy - 1.0) < tol)

def dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

print("\n=== _axis_adjacent: approach direction ===")

W, H = 50.0, 50.0
cx, cy = 12.0, 12.0

# Approach from the LEFT (actor is to the left of obstacle at same Y)
r = _axis_adjacent(cx, cy, curr_x=0.0, curr_y=12.0, width=W, height=H)
check("Approach from LEFT → land at (cx-1, cy)", r == (11.0, 12.0), str(r))

# Approach from the RIGHT
r = _axis_adjacent(cx, cy, curr_x=25.0, curr_y=12.0, width=W, height=H)
check("Approach from RIGHT → land at (cx+1, cy)", r == (13.0, 12.0), str(r))

# Approach from ABOVE (lower Y = above in this coordinate system)
r = _axis_adjacent(cx, cy, curr_x=12.0, curr_y=0.0, width=W, height=H)
check("Approach from ABOVE → land at (cx, cy-1)", r == (12.0, 11.0), str(r))

# Approach from BELOW (higher Y = below)
r = _axis_adjacent(cx, cy, curr_x=12.0, curr_y=25.0, width=W, height=H)
check("Approach from BELOW → land at (cx, cy+1)", r == (12.0, 13.0), str(r))

# Diagonal approach - dominant axis determines placement
# Coming from (0, 0) → cx=12, cy=12 → abs(dx)=abs(dy)=12 → X wins (>=)
r = _axis_adjacent(cx, cy, curr_x=0.0, curr_y=0.0, width=W, height=H)
check("Diagonal (equal dx/dy) → X axis wins → (cx-1, cy)", r == (11.0, 12.0), str(r))

# Mostly horizontal approach
r = _axis_adjacent(cx, cy, curr_x=0.0, curr_y=10.0, width=W, height=H)
check("Mostly horizontal (dx=12 > dy=2) → X axis → (cx-1, cy)", r == (11.0, 12.0), str(r))

# Mostly vertical approach
r = _axis_adjacent(cx, cy, curr_x=11.0, curr_y=0.0, width=W, height=H)
check("Mostly vertical (dx=1 < dy=12) → Y axis → (cx, cy-1)", r == (12.0, 11.0), str(r))

print("\n=== All results are axis-aligned and exactly 1 unit away ===")
test_cases = [
    (_axis_adjacent(cx, cy, 0.0, 12.0, W, H), "left"),
    (_axis_adjacent(cx, cy, 25.0, 12.0, W, H), "right"),
    (_axis_adjacent(cx, cy, 12.0, 0.0, W, H), "above"),
    (_axis_adjacent(cx, cy, 12.0, 25.0, W, H), "below"),
    (_axis_adjacent(cx, cy, 0.0, 0.0, W, H), "diagonal"),
    (_axis_adjacent(cx, cy, 0.0, 10.0, W, H), "mostly-horiz"),
    (_axis_adjacent(cx, cy, 11.0, 0.0, W, H), "mostly-vert"),
]
for r, label in test_cases:
    aligned = is_axis_aligned_adjacent(r, cx, cy)
    d = dist(r, (cx, cy))
    check(f"{label}: axis-aligned AND 1 unit away", aligned and abs(d - 1.0) < 0.001,
          f"pos={r}, dist={d:.3f}")

print("\n=== Wall clamping ===")
# Obstacle at (1, 1) approached from (25, 25) - dominant axis X
# cx-1 = 0.0, clamped to min 1.0
r = _axis_adjacent(1.0, 1.0, curr_x=25.0, curr_y=25.0, width=W, height=H)
check("Near-corner clamp: result stays within [1, W-1] x [1, H-1]",
      r[0] >= 1.0 and r[0] <= W-1 and r[1] >= 1.0 and r[1] <= H-1, str(r))

print(f"\n{'='*50}")
print(f"Results: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:")
    for f in FAIL:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All tests passed!")
