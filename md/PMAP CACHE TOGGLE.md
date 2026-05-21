# PMAP CACHE TOGGLE

## What this does

The Pygame map uses a persisted layout cache:

- `sessions/<session_id>/pmap_layout_cache.json`

While testing map/layout code changes, the cache can make you keep seeing old layouts.

This toggle forces the map to **ignore the cache** and **regenerate layouts** every time.

## The one thing to remember

Turn cache OFF (for testing) by setting:

- `PMAP_DISABLE_LAYOUT_CACHE=1`

## Step-by-step (Windows PowerShell)

### 1) Open PowerShell

Open a PowerShell terminal.

### 2) Enable cache bypass (testing mode)

Run:

```powershell
$env:PMAP_DISABLE_LAYOUT_CACHE="1"
```

### 3) Start the game from that same PowerShell

Run your normal start command (example):

```powershell
python MAIN/redesigned_main.py
```

### 4) Disable cache bypass (return to normal)

When you’re done testing, run:

```powershell
Remove-Item Env:PMAP_DISABLE_LAYOUT_CACHE
```

## Alternative env var name

This does the same thing:

- `PMAP_DISABLE_SNAPSHOTS=1`

## Notes

- This does **not** delete any files.
- It simply skips loading/saving cached layouts while the env var is set.
