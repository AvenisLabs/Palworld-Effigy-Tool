# Pal Effigy Grant Tool

Grants Pal Effigies (Lifmunk Effigies and the other 11 effigy types) to a
player in a Palworld world save — exactly as if the player had walked up and
collected each one:

- they count as **collected** (map/completion, no double pickup),
- they are **spendable at the Statue of Power**,
- the in-game capture-power bookkeeping stays consistent.

Made for your own single-player / co-op saves on Windows (Steam, Palworld
1.0+ — the current Oodle-compressed `.sav` format). Nothing to install —
the single `PalworldEffigyTool.exe` is fully self-contained (no Python, no
game files needed).

## Why this tool exists — the broken effigy achievement

Palworld's Steam effigy achievement only triggers when your collected
effigy points are **unallocated**. If you spend effigy points at the Statue
of Power as you collect them — which is how almost everyone plays — the
achievement check never sees the numbers it expects and it silently never
fires, no matter how many effigies you collect afterwards.

This tool grants effigies as collected with the points landing **unspent**,
so the achievement logic finally sees what it expects.

> **Important:** for the achievement fix to work, use the tool on a save
> where you have **not allocated any effigy points yet** (e.g. a new
> world). Allocated points are exactly what breaks the achievement —
> granting on top of an already-broken save will not un-break it.

## ⚠️ Official source — beware of copies

The **only** source for this tool is the public open-source GitHub
repository:

**https://github.com/AvenisLabs/Palworld-Effigy-Tool**

It is **not** distributed anywhere else — no other download sites, no
mirrors, no reuploads. If you got this tool from anywhere other than that
repository's Releases page, **it could be compromised** (tampered with or
bundled with malware). Delete it and download a fresh copy from the
official repository.

---

## Quick start

1. **Close Palworld completely.** The game rewrites its save continuously;
   editing a save that's in use will lose your changes.
2. Run **`PalworldEffigyTool.exe`** and click **Browse…** — it opens right
   at the Windows save location (`%LOCALAPPDATA%\Pal\Saved\SaveGames`).
   Go into your Steam-ID folder and select your world folder (the
   32-character name). **Select the folder that contains `Players`, not any
   of the files inside.**
   Stuck? The **?** buttons in the app open a help page that covers where
   saves live and what to do if yours isn't there.
3. Click your player (shown by in-game name, e.g. `Alice  (1A2B3C4D)`),
   tick the effigy categories to grant (each row shows `collected/total`),
   or **All**.
4. Click **Grant N NEW**. You'll get a confirmation with a per-category
   breakdown before anything is written.
5. Start the game — the effigies are waiting as unspent points at the
   Statue of Power.

## Safety / undo

- Before writing, the tool always saves a backup next to the original:
  `<uid>.sav.bak-<date>-<time>`. To undo, copy that file back over the
  edited one (game closed).
- After writing, the tool re-opens the file it just wrote and verifies
  every granted effigy and balance. If anything doesn't match, it restores
  the backup automatically and tells you.
- Nothing but the selected `Players/<uid>.sav` is ever modified.
  `Level.sav` is only read (for names), never written.

## What the categories are

| Effigy | Boost |
|---|---|
| Lifmunk Effigy | Capture Power |
| Lamball Effigy | Satiety Duration |
| Pengullet Effigy | Swimming |
| Munchill Effigy | Food Preservation |
| Rooby Effigy | Jump Power |
| Herbil Effigy | Gliding |
| Tanzee Effigy | Climb Speed |
| Depresso Effigy | Status Resistance |
| Cattiva Effigy | Mounted Stamina |
| Lunaris Effigy | Sphere Tracking |
| Relaxaurus Effigy | EXP Gain |
| Yakumo Effigy | Wild Pal Passives |

Granted effigies land as **unspent** points — the player still visits a
Statue of Power to spend them, same as normal pickups.

## Good to know

- The tool knows every placed effigy in the game (405 of them) and also
  scans the other player files in the folder for any effigy the game data
  list misses — so "all" really means all.
- Running it again on the same player is harmless: it reports
  "nothing to grant" and writes nothing.
- Files ending in `_dps.sav` are ignored (they're not player saves).
- If `Level.sav` is missing or unreadable, everything still works — players
  are just listed by their UID instead of name.

## Advanced: dedicated servers & console

Not the focus of this tool, but it works on dedicated-server world saves
too: stop the server, copy the world folder to your PC (on a typical Linux
server it's `.../Pal/Saved/SaveGames/0/<32-character-world-id>/`), edit it
here, copy only the **edited** `Players/<uid>.sav` back, then start the
server. The player being edited must stay logged out the whole time —
their in-game state would overwrite the edit.

There is also a step-by-step console version for scripted use, run from a
source checkout: `python grant_cli.py <save_folder>`.

---

© 2026 [AvenisLabs](https://avenislabs.com) · built for
[KarasWorlds.com](https://karasworlds.com). All rights reserved.
