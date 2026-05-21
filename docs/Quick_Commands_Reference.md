# Quick Commands Reference

## 🎮 **AVAILABLE COMMANDS**

These commands can be typed at any time during gameplay and **do not advance time**.

---

## 📋 **INFORMATION COMMANDS**

### **`ua` or `sheet`**
**View your character sheet**
```
> ua

Displays:
- Name, archetype, goals
- S-Factors (Sociability, Smarts, etc.)
- Status values (Spirit, Stamina, Stability)
- Skills and their levels
- Inventory and equipment
- Supplements (equipment bonuses)
```

---

### **`people` or `npcs` or `who`**
**List people in the area**
```
> people

Displays:
- All NPCs currently present
- Their names
- Brief descriptions
- Current status (if visible)
```

---

### **`look` or `l` or `scan`**
**Reprint the scene description**
```
> look

Displays:
- Full scene description
- Current environment
- Notable features
- Atmosphere and details
```

---

### **`map` or `show map` or `view map`**
**View spatial layout (NEW!)**
```
> map

Displays:
- ASCII art map of location
- Your position (@)
- NPC positions (●)
- Obstacles (█)
- Grid coordinates
- Zone information
- Distance categories
- Line of sight status
```

**Example Output:**
```
============================================================
MAP: Joe's Garage
Type: interior | Size: 20x15 units
============================================================

Y-axis
  ^
  15 ┌────────────┐
     │    ●       │  ● = Vince
  10 │            │
     │  @         │  @ = You
   5 │  ████      │  ████ = Counter
   0 └────────────┘
      0    5   10  → X-axis

ACTORS:
  @ You at (3.0, 5.0) in Front Area
  ● Vince at (8.0, 12.0) in Bay 1

ZONES:
  • Front Area (room)
  • Bay 1 (area)

OBSTACLES:
  █ Reception Desk (furniture)
```

---

### **`compact map` or `small map` or `mini map`**
**View condensed spatial layout**
```
> compact map

Displays:
- Smaller, more compact map
- Less detail, better overview
- Useful for large locations
```

---

## 🚪 **SYSTEM COMMANDS**

### **`quit` or `exit` or `q`**
**Exit the simulation**
```
> quit

- Saves your progress
- Saves spatial context
- Saves actor sheets
- Exits gracefully
```

---

## 📊 **COMMAND SUMMARY TABLE**

| Command | Aliases | Purpose | Time Cost |
|---------|---------|---------|-----------|
| `ua` | `sheet` | View character sheet | None |
| `people` | `npcs`, `who` | List people here | None |
| `look` | `l`, `scan` | Reprint scene | None |
| `map` | `show map`, `view map` | View spatial layout | None |
| `compact map` | `small map`, `mini map` | View condensed map | None |
| `quit` | `exit`, `q` | Exit simulation | None |

---

## 🎯 **USAGE TIPS**

### **Before Acting:**
```
> look          # What's here?
> people        # Who's here?
> map           # Where is everyone?
> ua            # Check my status
```

### **During Exploration:**
```
> map           # See spatial layout
> people        # Check for NPCs
> look          # Refresh scene details
```

### **During Combat:**
```
> map           # See positions and distances
> people        # Check enemy status
> ua            # Check my health
```

### **Planning Movement:**
```
> map           # See obstacles and distances
# Plan your path around obstacles
# Check distance to target
```

---

## 💡 **TIPS**

1. **Use `map` frequently** - Spatial awareness is key
2. **Check `people` before acting** - Know who's around
3. **Use `look` to refresh** - Scene details matter
4. **Check `ua` regularly** - Monitor your status
5. **Commands are instant** - No time penalty for checking info

---

## 🎉 **SUMMARY**

**Quick commands provide:**
- 📊 **Information access** without time cost
- 🗺️ **Spatial awareness** with map visualization
- 👥 **Social awareness** with people listing
- 📋 **Status checking** with character sheet
- 🔄 **Scene refresh** with look command

**All commands are instant and don't advance time!**
