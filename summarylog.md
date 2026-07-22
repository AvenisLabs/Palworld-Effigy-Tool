# Summary Log

## 2026-07-22 04:56 — Steam Community post drafted
- Verified repo is now PUBLIC.
- Wrote `steam_post.txt` (v1.0): BBCode post explaining the effigy-achievement bug (achievement never triggers when points are allocated on pickup), the must-use-on-unallocated-save requirement, usage steps, safety, and the public GitHub releases link.

## 2026-07-22 04:48 — GitHub Release v1.9
- Working tree was clean and pushed; created release `v1.9` on `AvenisLabs/Palworld-Effigy-Tool` with assets `PalworldEffigyTool.exe` (11.7 MB) and `EFFIGY_README.md`; verified both uploaded.
- https://github.com/AvenisLabs/Palworld-Effigy-Tool/releases/tag/v1.9

## 2026-07-22 04:44 — Readmes refocused on single-player
- `EFFIGY_README.md`: quick start is now a pure single-player flow (close game → browse → grant → play); dedicated-server + console CLI demoted to one "Advanced" section at the bottom; intro says "made for your own single-player / co-op saves".
- `README.md` v1.9: intro states single-player is the primary use case; sections reordered GUI (primary) → CLI (advanced); dedicated-server workflow retitled "(advanced — not the primary use case)"; fixed stale `effigy-grant-gui.exe` reference → `PalworldEffigyTool.exe`.
- Synced dist copy. No code changes — no rebuild needed.

## 2026-07-22 04:35 — Branding + single-player polish
- `grant_gui.py` v1.4: done dialog no longer tells players to copy the file back to a server (single-player focus; server guidance stays in Help/readme); title bar now "Effigy Grant Tool — © 2026 AvenisLabs for KarasWorlds.com"; new About help section with links to avenislabs.com and karasworlds.com.
- Copyright headers added to all code files: grant_cli v1.4, grant_edits v1.2, grant_master v1.2, grant_savio v1.6, spec v1.1.
- `README.md` v1.8 and `EFFIGY_README.md`: © footer with links to both sites; synced to `dist\`.
- Rebuild was blocked by a running exe instance (user launched it); paused per locked-file rule, user approved close — instance was already gone, rebuilt clean (exit 0).
- Verified: scripted smoke test (title, About links, no copy-back text) + rebuilt exe window title confirmed live.

## 2026-07-22 04:22 — Single-exe distribution
- New `build\palworld-effigy-tool.spec` (v1.0): one windowed `PalworldEffigyTool.exe` (11.7 MB) replaces the separate console + GUI exes; CLI remains available from source (`python grant_cli.py`). Rationale: Windows PEs are console- or windowed-subsystem at link time; dual-mode hacks break the CLI's interactive stdin.
- Deleted old specs/exes and stale build dirs; `dist\` now holds only the exe + readme.
- Docs: `README.md` v1.7 (single-exe section, spec-based rebuild command), `EFFIGY_README.md` updated (single exe; console = source checkout); synced to `dist\`.
- Verified: build exit 0, warnings all benign (same documented set), exe launches OK.

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
