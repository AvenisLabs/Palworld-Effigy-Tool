# Palworld Effigy Tool — project instructions

- **Releases: follow `RELEASING.md` exactly.** Any change that affects
  `PalworldEffigyTool.exe` (code in `grant_*.py`, the spec,
  `relic_master.json` — including in-app Help text, which lives in
  `grant_gui.py`) requires: rebuild from the spec → hash the FINAL exe →
  new GitHub release whose notes publish that exact SHA-256 → round-trip
  verify the uploaded asset. Never publish or reuse a stale hash.
- The public GitHub repo (`AvenisLabs/Palworld-Effigy-Tool`) is the ONLY
  distribution point — keep the official-source warnings in the readmes,
  in-app Help, and release notes intact.
- `README.md` is the player-facing help (GitHub landing page) and ships as
  a release asset; keep `dist\README.md` in sync when it changes.
  Developer notes and the version history live in `history.md` — bump its
  title version on tool changes.
- Keep docs single-player-first; dedicated-server usage is an advanced,
  secondary workflow.
- No private info anywhere (server hosts/IPs/usernames/domains, real
  player names/UIDs) — this repo is public.
