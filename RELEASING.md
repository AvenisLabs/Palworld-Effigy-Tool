# Release Process v1.2

*(v1.2: notes-handling warning added after a mangling incident.
v1.1: file renames — `README.md` is now the player-facing help and ships
as a release asset; developer notes/version history live in `history.md`.)*

Follow this checklist for **every release**. The iron rule: **any change
that affects `PalworldEffigyTool.exe` produces a new binary and therefore a
NEW SHA-256 hash — the release notes must always publish the hash of the
exact exe attached to that release.** Never reuse a hash from a previous
build; never hash before the final rebuild.

## When is a release needed?

- **Code changed** (`grant_*.py`, the spec, bundled `relic_master.json`):
  the exe changes → full checklist below, new release.
- **Docs-only change** (`history.md`, `RELEASING.md`, post drafts): commit
  and push, no release needed. Exception: `README.md` (the player-facing
  help) ships as a release asset — if it changes materially, re-upload it
  to the current release (`gh release upload <tag> dist\README.md
  --clobber`); the exe hash is unaffected.

## Checklist (exe changed)

Order matters — the hash must be computed from the FINAL binary
(the exe can never contain its own hash, and any edit after hashing
invalidates the published value).

1. **Finish all code/help changes first.** Remember: in-app Help text
   lives in `grant_gui.py` — editing it changes the exe.
2. **Bump versions** in every modified file's header + the `history.md`
   title, with changelog lines.
3. **Smoke test** (imports + scripted GUI checks; see summarylog for
   examples).
4. **Rebuild** from the spec (never ad-hoc PyInstaller flags):
   ```powershell
   python -m PyInstaller --distpath dist --workpath build --noconfirm build\palworld-effigy-tool.spec
   ```
   Check `$LASTEXITCODE` is 0 and review `build\palworld-effigy-tool\warn-*.txt`
   for NEW warnings (known-benign set is documented in `history.md`).
5. **Sync the player help**: `Copy-Item README.md dist\ -Force`.
6. **Hash the final exe** (only now — after the last rebuild):
   ```powershell
   (Get-FileHash dist\PalworldEffigyTool.exe -Algorithm SHA256).Hash
   ```
7. **Commit and push** all source/doc changes.
8. **Create the release** — tag matches the `history.md` version at
   release time (e.g. `v1.12`):
   ```powershell
   gh release create v<X.Y> dist\PalworldEffigyTool.exe dist\README.md --title "Palworld Effigy Tool v<X.Y>" --notes "<use template below>"
   ```
   If replacing an unannounced release, delete it first:
   `gh release delete v<old> --cleanup-tag --yes`. Once a release has been
   publicly announced, do NOT delete it — cut a new one on top.
9. **Round-trip verify** — download the asset back from GitHub and
   confirm the hash matches the published value exactly:
   ```powershell
   gh release download v<X.Y> -p "*.exe" -D <temp-dir> --clobber
   (Get-FileHash <temp-dir>\PalworldEffigyTool.exe).Hash
   ```
   If it doesn't match, the release is broken — fix before telling anyone.
10. **Log it** in `summarylog.md` (date+time, version, hash).

## Release notes template

Keep the structure: bug → fix → important → official source → verify
(with THIS release's hash) → details → copyright. Copy from the previous
release (`gh release view <tag> --json body`) and replace:

- the version number in the title,
- the SHA-256 in the "Verify your download" code block — **this is the
  step that must never be skipped or copied stale**,
- any feature bullets that changed.

The "Verify your download" section must always include the
beginner-friendly 4 steps (right-click Start → Terminal →
`Get-FileHash "$env:USERPROFILE\Downloads\PalworldEffigyTool.exe"` →
compare, case-insensitive, every character).

**Notes are edited on GitHub too — never round-trip them through
PowerShell strings.** The release description may contain manual edits
made on the web (e.g. the "Scroll DOWN" banner) — before recreating a
release, capture the CURRENT body and diff it against the template.
PowerShell pitfall (caused a mangled release once): capturing
`gh release view --jq .body` yields an ARRAY of lines, and
`Set-Content -NoNewline` concatenates array elements WITHOUT newlines,
destroying all markdown structure. Always author notes as a real file
(Write/Edit tools or an editor) and pass `--notes-file`; verify with
`gh release view` afterwards.

## Why the hash lives ONLY in release notes

A checksum shipped in a file next to the exe (readme, txt) is security
theater — whoever tampers with the exe edits the neighboring files too.
The reference value must come from the channel the attacker doesn't
control: the GitHub release page. Readmes and the in-app Help teach *how*
to verify; the release notes publish *what* the value is.

---

© 2026 [AvenisLabs](https://avenislabs.com) · built for
[KarasWorlds.com](https://karasworlds.com). All rights reserved.
