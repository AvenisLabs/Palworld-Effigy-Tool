# Effigy Grant Tool v1.7

> v1.7: single-exe distribution — one windowed `PalworldEffigyTool.exe`
> (GUI) replaces the separate console + GUI exes; the CLI remains available
> from source (`python grant_cli.py`).

> v1.6: GUI — Browse defaults to `%LOCALAPPDATA%\Pal\Saved\SaveGames`;
> added ? help buttons and an in-app help page (usage, finding your save,
> select-the-folder-not-files, safety/undo).
> v1.5: sanitized — all server/host-specific details removed; workflow is
> now documented with placeholders.
> v1.4: moved to its own repo — source now lives at the repo root of
> `F:\Workspace\Palworld_effigy` (was `tools\effigy_grant\` inside the
> palworld repo). The PalworldSaveTools fork is still consumed from the old
> repo's cache by default; see Requirements.

Standalone interactive CLI that edits a Palworld player save
(`Players/<uid>.sav`) to grant Pal Effigies by category — exactly as if the
player picked each one up in the world:

- sets the collection flags in `RelicObtainForInstanceFlagByType`
  (the game's authoritative collected state; prevents double-pickup),
- bumps the **unspent** balances (`RelicPossessNumMap`) so the effigies are
  spendable at the Statue of Power,
- for Lifmunk (capture power) also mirrors the legacy flat
  `RelicObtainForInstanceFlag` map and `RelicPossessNum`, keeping an
  invariant observed on every real player save examined.

GUID source: vendored `relic_master.json` (405 effigies, derived from
palworld-save-pal's relic data) **plus** a union with GUIDs observed as
collected across the other player saves in the same folder — this catches
at least one effigy that exists in the world but is missing from the data
list (the union shows up as Lifmunk 154/153 in practice).

## Save files needed

| File | Required | Why |
|---|---|---|
| `Players/<uid>.sav` | yes | the edit target — ALL effigy state lives here |
| sibling `Players/*.sav` | recommended | observed-GUID union (missing-effigy coverage) |
| `Level.sav` | optional | player names in the picker (unreadable copies are tolerated and just skip names) |

`_dps.sav` sidecars are ignored. `Level.sav` is never modified.

## Requirements

- Windows, Python 3.12 (the cached PalworldSaveTools fork ships a prebuilt
  `palooz` Oodle extension for cp312-win64 — nothing to install).
- Fork lookup order (`grant_savio.py`): `EFFIGY_FORK_DIR` env var →
  `cache\PalworldSaveTools` in this repo → old `tools\`-sibling layout →
  `F:\Workspace\palworld\tools\paldex_import\cache\PalworldSaveTools`
  (machine-specific fallback to the original repo's cache).
- On Linux, build palooz first (`pip install
  <fork>/src/palsav/palooz`) and/or point `EFFIGY_FORK_DIR` at a fork
  checkout with a working palooz.

## Usage

```powershell
python grant_cli.py <save_dir> [--master PATH] [--no-union]
```

The tool walks you through: player pick → category pick (`1,3-5` or `all`)
→ dry-run summary → type `YES` → write. It always creates a timestamped
`.bak-*` beside the file first, then re-decodes what it wrote and verifies
every flag and balance; on any mismatch it restores the backup and exits 1.

## GUI

```powershell
python grant_gui.py [save_dir]     # or effigy-grant-gui.exe
```

Minimal tkinter window over the same modules: Browse to the save folder
(opens at `%LOCALAPPDATA%\Pal\Saved\SaveGames` when the path box is empty) →
pick a player (listed by in-game name when `Level.sav` is present, decoded
automatically in ~0.1s; UID fallback otherwise) → tick categories (each
shows collected/total) → **Grant N NEW**. The ? buttons open an in-app help
page (usage, finding your save, safety/undo). Confirmation dialog shows the
per-category dry run; backup + post-write verification + auto-restore
behave exactly like the CLI, which also lists players by name.

## Standalone exe (PyInstaller)

`dist\PalworldEffigyTool.exe` is the single distribution build — a windowed
GUI with palsav, the palooz Oodle extension, and `relic_master.json`
bundled, so it runs on any 64-bit Windows box with no Python and no repo
checkout:

```powershell
PalworldEffigyTool.exe [save_dir]      # windowed GUI; optional pre-filled folder
python grant_cli.py <save_dir>         # console workflow needs a source checkout
```

Rebuild (from repo root; requires PyInstaller and the cached fork):

```powershell
python -m PyInstaller --distpath dist --workpath build --noconfirm build\palworld-effigy-tool.spec
```

`build/` and `dist/` are gitignored (the exe stays local). Benign analysis
warnings: `palworld_aio` (unused palsav backup command) and `recordclass`
(optional palsav fallback, not installed in the tested env either).

## Dedicated-server workflow

The game autosaves continuously — never edit a save the server is using,
and keep the target player OFFLINE for the whole procedure (their in-memory
state would overwrite the edit).

```powershell
# 1. stop the Palworld server (e.g. systemctl on a Linux host)
ssh <user>@<server> "sudo systemctl stop <palworld-service>"

# 2. copy the world save folder down
scp -r <user>@<server>:<save-root>/Saved/SaveGames/0/<world-id> .\work-save

# 3. run the tool
python grant_cli.py .\work-save

# 4. copy ONLY the edited player file back (the tool prints which)
scp .\work-save\Players\<uid>.sav <user>@<server>:<save-root>/Saved/SaveGames/0/<world-id>/Players/

# 5. start the server
ssh <user>@<server> "sudo systemctl start <palworld-service>"
```

To undo, copy the `.bak-*` file back the same way.

## Layout

| File | Responsibility |
|---|---|
| `grant_cli.py` | interactive menu, dry-run, confirm, self-verify orchestration |
| `grant_edits.py` | pure GVAS-dict edit logic (no palsav import) |
| `grant_master.py` | vendored master list + observed-GUID union |
| `grant_savio.py` | PlM decode/encode via the cached fork, backup/restore |
| `relic_master.json` | vendored GUID master (405, provenance in header) |

Tests: `tests/test_effigy_grant_*.py` live in the original palworld repo
(`F:\Workspace\palworld`) — not yet migrated here. Save-dependent ones
auto-skip without `savedata/`; set `EFFIGY_SLOW_TESTS=1` to include the
Level.sav name test.
