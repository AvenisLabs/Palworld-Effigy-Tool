# Pal Effigy Grant Tool

Grants Pal Effigies (Lifmunk Effigies and the other 11 effigy types) to a
player in a Palworld world save — exactly as if the player had walked up and
collected each one:

- they count as **collected** (map/completion, no double pickup),
- they are **spendable at the Statue of Power**,
- the in-game capture-power bookkeeping stays consistent.

Works on dedicated-server world saves from Palworld 1.0+ (the current
Oodle-compressed `.sav` format). Nothing to install — the `.exe` files are
fully self-contained (no Python, no game files needed).

---

## Quick start (GUI)

1. **Close the game / stop the Palworld server.** The game rewrites its
   save continuously; editing a save that's in use will lose your changes.
2. Find your world save folder:
   - **Local / co-op (Steam on Windows):** Browse… opens straight at
     `%LOCALAPPDATA%\Pal\Saved\SaveGames` — go into your Steam-ID folder,
     then select the world folder (32-character name). **Select the folder
     that contains `Players`, not any of the files inside.**
   - **Dedicated server:** copy the world save folder to your PC first; on
     a typical Linux server it lives at
     `.../Pal/Saved/SaveGames/0/<32-character-world-id>/`.
     You need the `Players` subfolder; grab `Level.sav` too if you want
     player names shown (recommended — it's what lets you pick by name).
3. Run **`effigy-grant-gui.exe`**, click **Browse…**, select the world
   folder. Players appear by in-game name, e.g. `Alice  (1A2B3C4D)`.
   Stuck? The **?** buttons in the app open a help page that covers where
   saves live and what to do if yours isn't there.
4. Click a player, tick the effigy categories to grant (each row shows
   `collected/total`), or **All**.
5. Click **Grant N NEW**. You'll get a confirmation with a per-category
   breakdown before anything is written.
6. Copy the **edited player file** (`Players/<uid>.sav` — the tool tells
   you which) back to the server, then start the server again.

**The player being edited must be logged out** the whole time — if they're
online, their in-game state overwrites your edit when they log off.

## Console version

`effigy-grant.exe <save_folder>` does the same thing as a step-by-step
text menu (player number → categories like `1,3-5` or `all` → type `YES`).

## Safety / undo

- Before writing, the tool always saves a backup next to the original:
  `<uid>.sav.bak-<date>-<time>`. To undo, copy that file back over the
  edited one (server stopped).
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
