# Snapshot restore point

## Saved snapshot (tag)
- `snapshot-working-2026-02-01`

## Saved restore branch
- `restore-point-snapshot-2026-02-01`

## Restore commands

### Option B (recommended): create/use a branch from the snapshot
If you just want to get back to the saved version and keep working from there:

```powershell
git switch -c restore-point snapshot-working-2026-02-01
```

Or, if you want to switch to the already-created restore branch:

```powershell
git switch restore-point-snapshot-2026-02-01
```

### Detached checkout (view snapshot without branching)

```powershell
git checkout snapshot-working-2026-02-01
```

### Hard reset current branch back to snapshot (destructive)
WARNING: This will discard uncommitted changes.

```powershell
git reset --hard snapshot-working-2026-02-01
```
