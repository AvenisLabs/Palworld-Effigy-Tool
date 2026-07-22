# Summary Log

## 2026-07-22 04:14 — GitHub remote recreated
- Created private repo `AvenisLabs/Palworld-Effigy-Tool`, pushed `main` (4 commits, sanitized history only), upstream tracking set.
- Verified remote tree: 12 clean files — no exes, save data, or build output.

## 2026-07-22 04:10 — GUI: default browse location + in-app help; exes rebuilt
- `grant_gui.py` v1.3: Browse now opens at `%LOCALAPPDATA%\Pal\Saved\SaveGames` when the path box is empty (keeps the user's current folder otherwise); added `?` button on the folder row (jumps to "Finding your save") and `? Help` in the bottom bar; new Help page (Toplevel) with sections: How to use, Finding your save, Safety/undo — covers select-the-folder-not-files and fallback locations if Browse fails; "No player saves" error now explains folder-vs-file and points at `?`.
- Docs: `README.md` v1.6 (GUI section), `EFFIGY_README.md` quick start rewritten for local/co-op vs dedicated-server saves; synced to `dist\`.
- Verified: scripted GUI smoke test (help window builds, all sections render, default resolves); rebuilt both exes from kept specs (exit 0, all analysis warnings benign Unix/platform stubs + the two documented ones); `effigy-grant.exe --help` OK; GUI exe launches OK.

## 2026-07-22 03:56 — Cleanup confirmed
- User deleted `dist\Pal-effigy-Fix.7z` (contained pre-sanitize readme); verified gone.
- Verified `AvenisLabs/Palworld-Effigy-Fix` no longer exists on GitHub (user deleted it).
- Local repo remains: single sanitized commit on `main`, no remotes. Ready to recreate + push on request.

## 2026-07-22 03:52 — Sensitive-data clean sweep + history flush
- Scrubbed all private info from every file: SSH user/IP/hostname, server paths, world save GUID, tracker domain, portal project references, real player name/UID example. Replaced with generic placeholders.
- Files touched: `README.md` (v1.5, workflow now placeholder-based), `EFFIGY_README.md` (+ synced copy in `dist\`), `relic_master.json` (provenance genericized), `grant_cli.py` (v1.3), `grant_gui.py` (v1.2), `grant_edits.py` (v1.1), `grant_master.py` (v1.1).
- Verified clean: repo-wide grep for IPs/hosts/usernames/domains/GUIDs returns only placeholders. All modules import OK.
- Flushed git history completely (deleted `.git`, re-init on `main`) — old commits contained the sensitive README. User is deleting the GitHub repo separately.
- NOTE: `dist\Pal-effigy-Fix.7z` (local, gitignored) still contains the OLD readme inside the archive — repack before redistributing.

## 2026-07-22 03:42 — GitHub remote created
- Created private repo `AvenisLabs/Palworld-Effigy-Fix` (user confirmed AvenisLabs; spaces in requested name "Palworld Effigy Fix" became hyphens).
- Pushed `main` (3 commits) and set upstream tracking.

## 2026-07-22 03:38 — Flattened source to repo root
- Moved all `effigy_grant/` contents to the repo root; removed the now-empty subfolder.
- Updated `.gitignore` paths for the flat layout.
- `grant_savio.py` v1.5: fork lookup now probes `EFFIGY_FORK_DIR` → repo-local `cache\PalworldSaveTools` → old `tools\`-sibling layout → `F:\Workspace\palworld\...\cache\PalworldSaveTools` (machine fallback). Verified it resolves via the fallback.
- `grant_cli.py` v1.2: docstring usage path updated.
- Both `.spec` files: `pathex`/`datas` updated to the new repo root + absolute fork paths.
- `README.md` v1.4: all `tools\effigy_grant\` paths flattened; rebuild command rewritten for this repo; noted tests still live in the original palworld repo.
- Verified: `grant_savio`/`grant_edits`/`grant_master`/`grant_gui` import OK; `grant_cli.py --help` runs.

## 2026-07-22 03:28 — Repository initialized
- Established `F:\Workspace\Palworld_effigy` as the dedicated home for the effigy grant tool (copied from earlier work; source lives in `effigy_grant/`).
- Initialized git repo on branch `main`.
- Added `.gitignore`: excludes `__pycache__/`, PyInstaller `build/` output (keeps `.spec` files), `dist/`, all Palworld save data (`*.sav`, `save/`), and `.7z` archives.
- Initial commit `a403c60`: 11 files (5 Python modules, 2 READMEs, 2 spec files, relic_master.json, .gitignore).
