# Effigy Grant Tool v1.16 — developer notes & version history

*(formerly `README.md` — the repo's `README.md` is now the player-facing
help; this file keeps the developer documentation and version history.)*

> v1.16: doc restructure — player helpfile is now `README.md` (the GitHub
> landing page); this file renamed to `history.md`.
> v1.15: launch-notice text reflows cleanly; Help opens automatically
> beside the main window on startup (top of the page).
> v1.14: GUI shows an official-source notice popup on every launch,
> acknowledged with OK before the main window opens.
> v1.13: release process documented in `RELEASING.md` (docs only — exe,
> hash, and release v1.12 unchanged).

> **⚠️ Official source:** this public repository
> (`github.com/AvenisLabs/Palworld-Effigy-Tool`) is the **only**
> distribution point for this tool. It is not distributed anywhere else —
> copies found on other sites may be compromised. Download only from this
> repo's Releases page, and verify the exe's SHA-256 checksum against the
> one published in the release notes
> (`Get-FileHash PalworldEffigyTool.exe` in PowerShell; beginner
> walk-through in `README.md` and the in-app Help).

> v1.12: SHA-256 verification — hash published per release, beginner
> instructions in readmes and in-app help.
> v1.11: official-source warning added to readmes and in-app help.
> v1.10: documented the Steam effigy-achievement bug this tool works
> around (readmes + in-app help): the achievement only triggers with
> unallocated effigy points, so the grant must run on a save where no
> points have been allocated yet.
> v1.9: docs refocused on single-player saves — the primary audience;
> dedicated-server use is documented as an advanced/secondary workflow.

> v1.8: single-player focus (done dialog no longer mentions copying back to
> a server); © 2026 AvenisLabs branding in title bar, code headers, and an
> About help section with site links.

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

Standalone tool (windowed GUI + interactive CLI) that edits a Palworld
player save (`Players/<uid>.sav`) to grant Pal Effigies by category —
exactly as if the player picked each one up in the world. The primary use
case is a player's own local single-player / co-op save; dedicated-server
saves work too but are a secondary, advanced workflow.

**Why:** Palworld's Steam effigy achievement only triggers when collected
effigy points are unallocated — players who spend points as they collect
(i.e. nearly everyone) can never earn it. Granting effigies as collected
+ **unspent** lets the achievement logic see what it expects; for that to
work the grant must run on a save with no effigy points allocated yet.

What a grant does:

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

## GUI (primary)

```powershell
python grant_gui.py [save_dir]     # or PalworldEffigyTool.exe
```

Minimal tkinter window over the shared modules: Browse to the save folder
(opens at `%LOCALAPPDATA%\Pal\Saved\SaveGames` when the path box is empty) →
pick a player (listed by in-game name when `Level.sav` is present, decoded
automatically in ~0.1s; UID fallback otherwise) → tick categories (each
shows collected/total) → **Grant N NEW**. The ? buttons open an in-app help
page (usage, finding your save, safety/undo). Confirmation dialog shows the
per-category dry run; backup + post-write verification + auto-restore
behave exactly like the CLI, which also lists players by name.

## CLI (advanced)

```powershell
python grant_cli.py <save_dir> [--master PATH] [--no-union]
```

Same grant flow as a step-by-step text menu: player pick → category pick
(`1,3-5` or `all`) → dry-run summary → type `YES` → write. It always
creates a timestamped `.bak-*` beside the file first, then re-decodes what
it wrote and verifies every flag and balance; on any mismatch it restores
the backup and exits 1.

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

**Releasing:** any change to the exe means a new SHA-256 — follow the
checklist in [`RELEASING.md`](RELEASING.md) (rebuild → hash the final
binary → publish the hash in the release notes → round-trip verify).

`build/` and `dist/` are gitignored (the exe stays local). Benign analysis
warnings: `palworld_aio` (unused palsav backup command) and `recordclass`
(optional palsav fallback, not installed in the tested env either).

## Dedicated-server workflow (advanced — not the primary use case)

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

---

© 2026 [AvenisLabs](https://avenislabs.com) · built for
[KarasWorlds.com](https://karasworlds.com). All rights reserved.
