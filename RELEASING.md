# Release Process v1.0

Follow this checklist for **every release**. The iron rule: **any change
that affects `PalworldEffigyTool.exe` produces a new binary and therefore a
NEW SHA-256 hash — the release notes must always publish the hash of the
exact exe attached to that release.** Never reuse a hash from a previous
build; never hash before the final rebuild.

## When is a release needed?

- **Code changed** (`grant_*.py`, the spec, bundled `relic_master.json`):
  the exe changes → full checklist below, new release.
- **Docs-only change** (`README.md`, `RELEASING.md`, post drafts): commit
  and push, no release needed. Exception: `EFFIGY_README.md` ships as a
  release asset — if it changes materially, re-upload it to the current
  release (`gh release upload <tag> dist\EFFIGY_README.md --clobber`);
  the exe hash is unaffected.

## Checklist (exe changed)

Order matters — the hash must be computed from the FINAL binary
(the exe can never contain its own hash, and any edit after hashing
invalidates the published value).

1. **Finish all code/help changes first.** Remember: in-app Help text
   lives in `grant_gui.py` — editing it changes the exe.
2. **Bump versions** in every modified file's header + `README.md` title,
   with changelog lines.
3. **Smoke test** (imports + scripted GUI checks; see summarylog for
   examples).
4. **Rebuild** from the spec (never ad-hoc PyInstaller flags):
   ```powershell
   python -m PyInstaller --distpath dist --workpath build --noconfirm build\palworld-effigy-tool.spec
   ```
   Check `$LASTEXITCODE` is 0 and review `build\palworld-effigy-tool\warn-*.txt`
   for NEW warnings (known-benign set is documented in README.md).
5. **Sync the player readme**: `Copy-Item EFFIGY_README.md dist\ -Force`.
6. **Hash the final exe** (only now — after the last rebuild):
   ```powershell
   (Get-FileHash dist\PalworldEffigyTool.exe -Algorithm SHA256).Hash
   ```
7. **Commit and push** all source/doc changes.
8. **Create the release** — tag matches the README version at release
   time (e.g. `v1.12`):
   ```powershell
   gh release create v<X.Y> dist\PalworldEffigyTool.exe dist\EFFIGY_README.md --title "Palworld Effigy Tool v<X.Y>" --notes "<use template below>"
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

## Why the hash lives ONLY in release notes

A checksum shipped in a file next to the exe (readme, txt) is security
theater — whoever tampers with the exe edits the neighboring files too.
The reference value must come from the channel the attacker doesn't
control: the GitHub release page. Readmes and the in-app Help teach *how*
to verify; the release notes publish *what* the value is.

---

© 2026 [AvenisLabs](https://avenislabs.com) · built for
[KarasWorlds.com](https://karasworlds.com). All rights reserved.
