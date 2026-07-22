#!/usr/bin/env python3
"""grant_gui.py v1.13 — minimal tkinter GUI for the effigy grant tool.

v1.13: top row simplified — Load button and its ? removed (Browse loads
       automatically; pressing Enter in the path box loads a hand-typed
       path).
v1.12: layout — Grant button moved into the Categories button row, left of
       All/None, which are now fixed-width instead of half the row each.

v1.11: Help window widened to 740px — the monospace body text is
       hard-wrapped at ~74 columns and the old 620px width soft-wrapped
       the last word of many lines (ragged display).

v1.10: Cattiva app icon — window/taskbar icon set from bundled
       cattiva.ico (assets\\ in source runs, _MEIPASS in the frozen exe).

v1.9: launch-notice text reflows naturally (one string per paragraph — the
      hard-wrapped version fought the dialog's own wrapping); Help window
      now opens automatically beside the main window on startup, at the top.

v1.8: official-source notice popup on launch — must be acknowledged (OK)
      before the main window opens.

v1.7: official-source help section now includes step-by-step SHA-256
      verification instructions (Get-FileHash vs the release-page hash).

v1.6: Help gains an "Official source" section — the public GitHub repo is
      the ONLY distribution point; copies found elsewhere may be
      compromised.

v1.5: Help gains a leading "The achievement bug" section — why the Steam
      effigy achievement breaks (points allocated on pickup) and why the
      grant must run on a save with no effigy points allocated.

Copyright © 2026 AvenisLabs (https://avenislabs.com)
for KarasWorlds.com (https://karasworlds.com). All rights reserved.

v1.4: single-player focus — done dialog no longer tells players to copy the
      file back to a server (that guidance lives in Help / the readme);
      © notice in the title bar; About section (with site links) in Help.
v1.3: Browse now opens at %LOCALAPPDATA%\\Pal\\Saved\\SaveGames (the default
      Windows save location) when the path box is empty; added ? help buttons
      and a Help page (usage, finding your save, folder-not-files, safety).
v1.2: sanitized — server-specific references removed from the done dialog.

Thin window over grant_edits/grant_master/grant_savio (all logic lives
there): pick save folder -> pick player -> tick categories -> Grant.
Same safety rails as the CLI: timestamped backup, post-write re-decode
verification with automatic restore on mismatch.

v1.1: player list shows names, not UIDs — Level.sav is decoded automatically
      in the background on folder load; UID is the fallback when no name is
      available (no Level.sav, or a torn copy).
"""
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))  # dual-mode contract
import grant_edits as ge
import grant_master as gm
import grant_savio as sio


def _resource(name: str) -> Path:
    """Bundled-data path: PyInstaller extracts datas to sys._MEIPASS; source
    runs read from the repo's assets\\ folder."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / name
    return Path(__file__).resolve().parent / "assets" / name


def default_save_root() -> Path | None:
    """The standard Windows local-save location, if it exists.

    Steam stores local/co-op world saves under
    %LOCALAPPDATA%\\Pal\\Saved\\SaveGames\\<steam-id>\\<world-id>\\.
    """
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    root = Path(local) / "Pal" / "Saved" / "SaveGames"
    return root if root.is_dir() else None


# Shown as a modal popup on every launch, before the main window opens.
# Each paragraph is ONE string — the dialog does its own word-wrapping, and
# embedded newlines mid-sentence produce ragged breaks.
OFFICIAL_SOURCE_NOTICE = (
    "The ONLY official source for this tool is the public open-source "
    "GitHub repository:"
    "\n\ngithub.com/AvenisLabs/Palworld-Effigy-Tool\n\n"
    "It is NOT distributed anywhere else. If you downloaded it from "
    "anywhere other than that repository's Releases page, it could be "
    "COMPROMISED (tampered with or bundled with malware) — delete it and "
    "download a fresh copy from the official repository."
    "\n\n"
    "You can verify your download's SHA-256 checksum against the one "
    "published on the release page: see \"? Help → Official source\" for "
    "step-by-step instructions.")


# (section title, body) pairs — rendered into the Help window; section titles
# are also jump anchors for the context-sensitive ? buttons.
HELP_SECTIONS = [
    ("The achievement bug (read first)", """\
Palworld's Steam effigy achievement is designed so it only triggers when
your collected effigy points are UNALLOCATED. If you spend effigy points at
the Statue of Power as you collect them — which is how almost everyone
plays — the achievement check never sees the numbers it expects and it
silently never fires. No amount of further collecting fixes it.

This tool works around that: it grants effigies as collected with the
points landing UNSPENT, so the achievement logic finally sees what it
expects.

IMPORTANT: for the achievement fix to work, run the grant on a save where
you have NOT allocated any effigy points yet (e.g. a new world). Allocated
points are exactly what breaks the achievement — granting on top of an
already-broken save will not un-break it."""),
    ("How to use", """\
1. Click Browse… and select your WORLD SAVE FOLDER (see "Finding your save"
   below). Select the folder itself — NOT the .sav files inside it.
2. Pick a player from the list (shown by in-game name when Level.sav is
   present, otherwise by UID).
3. Tick the effigy categories to grant — each row shows collected/total —
   or use All / None.
4. Click "Grant N NEW". You get a per-category confirmation first; a
   timestamped backup (<uid>.sav.bak-<date>-<time>) is written before any
   change, and the result is re-checked after writing (auto-restore on any
   mismatch).
5. Playing on a dedicated server? Copy the edited Players\\<uid>.sav back to
   the server with the server STOPPED and the player logged out."""),
    ("Finding your save", """\
Browse opens at the usual Windows save location:

    %LOCALAPPDATA%\\Pal\\Saved\\SaveGames

Inside it: one folder per Steam account (a long number), then one folder per
world (a 32-character name like 0123ABCD...). SELECT THAT WORLD FOLDER —
the one that directly contains a "Players" subfolder (and usually
Level.sav). Do not select Level.sav or any other file.

If Browse doesn't open there, or the folder doesn't exist:
- Paste  %LOCALAPPDATA%\\Pal\\Saved\\SaveGames  into File Explorer's address
  bar and press Enter. If you have several worlds, the right one is usually
  the most recently modified folder.
- Steam users can also check:
  C:\\Users\\<you>\\AppData\\Local\\Pal\\Saved\\SaveGames
- Dedicated server: the world folder lives on the server under
  .../Pal/Saved/SaveGames/0/<world-id>. Stop the server, copy that whole
  folder to this PC, edit it here, then copy the edited
  Players\\<uid>.sav back.
- Xbox app / Microsoft Store (Game Pass) installs keep saves in a protected
  package container — those saves are not directly editable by this tool.

Wrong folder selected? The tool will say "No player saves under ...\\Players"
— go one level down (into the world folder) or up until the selected folder
directly contains "Players"."""),
    ("Safety / undo", """\
- A backup is always written next to the original before any change:
  <uid>.sav.bak-<date>-<time>. To undo, copy it back over the edited file
  (game/server not running).
- After writing, the tool re-opens the file and verifies every flag and
  balance; on any mismatch the backup is restored automatically.
- Only the selected Players\\<uid>.sav is ever written. Level.sav is only
  read (for player names).
- The player being edited must not be in the game while you edit — their
  live state would overwrite the change."""),
    ("Official source — beware of copies", """\
The ONLY source for this tool is the public open-source GitHub repository:

    https://github.com/AvenisLabs/Palworld-Effigy-Tool

It is NOT distributed anywhere else — no other download sites, no mirrors,
no reuploads. If you got this tool from anywhere other than that
repository's Releases page, it could be COMPROMISED (tampered with or
bundled with malware). Delete it and download a fresh copy from the
official repository.

HOW TO VERIFY YOUR DOWNLOAD (no experience needed):
Every release page publishes the file's SHA-256 checksum — a long
fingerprint that changes if the file is altered in any way.
1. Right-click the Windows Start button and choose "Terminal" (or
   "Windows PowerShell").
2. Type the following and press Enter (adjust the path if you saved the
   file somewhere other than Downloads):
      Get-FileHash "$env:USERPROFILE\\Downloads\\PalworldEffigyTool.exe"
3. Compare the Hash value it prints with the SHA256 on the official
   release page. Every character must match (upper/lower case doesn't
   matter).
4. Match = genuine download. No match = delete the file and download
   again from the official repository only."""),
    ("About", """\
Effigy Grant Tool
© 2026 AvenisLabs — https://avenislabs.com
Built for KarasWorlds.com — https://karasworlds.com
Official source: https://github.com/AvenisLabs/Palworld-Effigy-Tool"""),
]


def dry_run_lines(types_meta: dict, sets: dict, already: dict,
                  picked: list[str]) -> tuple[list[str], int]:
    """Display lines + total NEW for the picked category keys (pure, tested)."""
    lines, total = [], 0
    for key in picked:
        guids = sets[key]
        new = len(guids - already.get(key, set()))
        total += new
        name = (types_meta.get(key) or {}).get("name", key)
        lines.append(f"{name}: {len(guids) - new}/{len(guids)} collected, NEW {new}")
    return lines, total


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Effigy Grant Tool — © 2026 AvenisLabs for KarasWorlds.com")
        ico = _resource("cattiva.ico")
        if ico.is_file():  # default= also applies to Toplevels (Help window)
            root.iconbitmap(default=str(ico))
        root.geometry("640x560")
        self.saves: list[Path] = []
        self.names: dict[str, str] = {}
        self.sets: dict = {}
        self.types_meta: dict = {}
        self.already: dict = {}
        self.gf = None           # decoded GvasFile of the selected player
        self.save_type = 0
        self.rd: dict = {}       # its RecordData
        self.cat_vars: dict[str, tk.BooleanVar] = {}

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")
        self.dir_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.dir_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.load_dir())  # hand-typed paths
        ttk.Button(top, text="Browse…", command=self.browse).pack(
            side="left", padx=(4, 0))

        mid = ttk.Frame(root, padding=6)
        mid.pack(fill="both", expand=True)
        left = ttk.LabelFrame(mid, text="Player", padding=4)
        left.pack(side="left", fill="both", expand=True)
        self.player_list = tk.Listbox(left, exportselection=False)
        self.player_list.pack(fill="both", expand=True)
        self.player_list.bind("<<ListboxSelect>>", lambda e: self.pick_player())

        right = ttk.LabelFrame(mid, text="Categories", padding=4)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.cat_frame = ttk.Frame(right)
        self.cat_frame.pack(fill="both", expand=True)
        btns = ttk.Frame(right)
        btns.pack(fill="x")
        # Grant takes the leftover row width; All/None are compact.
        self.grant_btn = ttk.Button(btns, text="Grant", command=self.grant,
                                    state="disabled")
        self.grant_btn.pack(side="left", expand=True, fill="x")
        ttk.Button(btns, text="All", width=5,
                   command=lambda: self.set_all(True)).pack(side="left", padx=(4, 0))
        ttk.Button(btns, text="None", width=5,
                   command=lambda: self.set_all(False)).pack(side="left", padx=(4, 0))

        bottom = ttk.Frame(root, padding=6)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="? Help", command=self.show_help).pack(side="left")
        self.help_win: tk.Toplevel | None = None  # reused if already open
        self.status = tk.Text(root, height=8, state="disabled")
        self.status.pack(fill="x", padx=6, pady=(0, 6))

    # ---------- helpers ----------
    def log(self, msg: str):
        self.status.configure(state="normal")
        self.status.insert("end", msg + "\n")
        self.status.see("end")
        self.status.configure(state="disabled")
        self.root.update_idletasks()

    def browse(self):
        # Start where the user already is; otherwise the standard save root.
        cur = Path(self.dir_var.get().strip()) if self.dir_var.get().strip() else None
        initial = cur if (cur and cur.is_dir()) else default_save_root()
        d = filedialog.askdirectory(
            title="Select the WORLD SAVE FOLDER (contains Players\\) — not a file",
            initialdir=str(initial) if initial else None)
        if d:
            self.dir_var.set(d)
            self.load_dir()

    # ---------- help ----------
    def show_help(self, section: str | None = None):
        """Open (or focus) the Help page; optionally jump to a section."""
        if self.help_win is None or not self.help_win.winfo_exists():
            self.help_win = tk.Toplevel(self.root)
            self.help_win.title("Effigy Grant — Help")
            self.help_win.geometry("740x540")
            txt = tk.Text(self.help_win, wrap="word", padx=10, pady=8)
            sb = ttk.Scrollbar(self.help_win, command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
            txt.pack(fill="both", expand=True)
            txt.tag_configure("h", font=("TkDefaultFont", 11, "bold"),
                              spacing1=10, spacing3=4)
            for title, body in HELP_SECTIONS:
                txt.insert("end", title + "\n", ("h", f"sec:{title}"))
                txt.insert("end", body + "\n")
            txt.configure(state="disabled")
            self.help_text = txt
        self.help_win.deiconify()
        self.help_win.lift()
        if section:  # scroll the section heading to the top of the window
            rng = self.help_text.tag_ranges(f"sec:{section}")
            if rng:
                self.help_text.see("end")       # force from bottom so the
                self.help_text.see(rng[0])      # target lands at the top
                self.help_text.yview(f"{rng[0]} linestart")

    # ---------- load flow ----------
    def load_dir(self):
        save_dir = Path(self.dir_var.get().strip())
        self.saves = sio.list_player_saves(save_dir)
        self.player_list.delete(0, "end")
        self.gf = None
        if not self.saves:
            messagebox.showerror(
                "Effigy Grant",
                f"No player saves under {save_dir / 'Players'}\n\n"
                "Make sure you selected the world save FOLDER — the one that "
                "directly contains a Players subfolder — not a file inside "
                "it.\n\nClick the ? button for help finding your save.")
            return
        self.log(f"loaded {len(self.saves)} player save(s) from {save_dir}")
        # Master list + observed union across every player save in the folder.
        master = gm.load_master()
        self.types_meta = master["types"]
        rds = []
        for p in self.saves:
            try:
                rds.append(sio.record_data(sio.read_player(p)[0]))
            except Exception as e:
                self.log(f"warning: skipping {p.name}: {e}")
        self.sets, extras = gm.union_observed(master["sets"], rds)
        if extras:
            n = sum(len(v) for v in extras.values())
            self.log(f"union: +{n} observed GUID(s) not in master")
        self.names = {}
        self.refresh_players()
        if (save_dir / "Level.sav").is_file():
            self.load_names()  # automatic; list refreshes when names arrive

    def display_name(self, save_path: Path) -> str:
        """Player name with a short UID suffix to disambiguate; UID fallback."""
        uid = save_path.stem.upper()
        name = self.names.get(uid)
        return f"{name}  ({uid[:8]})" if name else uid

    def refresh_players(self):
        sel = self.player_list.curselection()
        self.player_list.delete(0, "end")
        for p in self.saves:
            self.player_list.insert("end", self.display_name(p))
        if sel:
            self.player_list.selection_set(sel[0])

    def load_names(self):
        # Fast (~0.1s) since savio v1.4, but a thread keeps big saves painless.
        # tk is main-thread-only: read the tk var here, and let the worker
        # hand its result back through a queue the main thread polls.
        save_dir = Path(self.dir_var.get().strip())
        self.log("decoding Level.sav for player names…")
        result: queue.Queue = queue.Queue(maxsize=1)
        threading.Thread(target=lambda: result.put(sio.player_names(save_dir)),
                         daemon=True).start()

        def poll():
            try:
                names = result.get_nowait()
            except queue.Empty:
                self.root.after(100, poll)
                return
            self.names = names
            self.refresh_players()
            self.log(f"names: {len(names)} found"
                     if names else "names: Level.sav unreadable — showing UIDs")

        self.root.after(100, poll)

    def pick_player(self):
        sel = self.player_list.curselection()
        if not sel:
            return
        target = self.saves[sel[0]]
        try:
            self.gf, self.save_type = sio.read_player(target)
            self.rd = sio.record_data(self.gf)
        except Exception as e:
            messagebox.showerror("Effigy Grant", f"cannot read {target.name}: {e}")
            self.gf = None
            return
        self.already = ge.collected_by_type(self.rd)
        self.build_category_checks()
        self.grant_btn.configure(state="normal")
        self.log(f"selected {self.display_name(target)} [{target.name}]")
        self.update_summary()

    def build_category_checks(self):
        for w in self.cat_frame.winfo_children():
            w.destroy()
        self.cat_vars = {}
        for key in ge.RELIC_ENUM_BY_KEY:
            if key not in self.sets:
                continue
            meta = self.types_meta.get(key, {})
            have = len(self.already.get(key, set()) & self.sets[key])
            total = len(self.sets[key])
            var = tk.BooleanVar(value=False)
            self.cat_vars[key] = var
            ttk.Checkbutton(
                self.cat_frame, variable=var, command=self.update_summary,
                text=f"{meta.get('name', key)} ({meta.get('effect', '?')}) "
                     f"{have}/{total}").pack(anchor="w")

    def picked_keys(self) -> list[str]:
        return [k for k, v in self.cat_vars.items() if v.get()]

    def set_all(self, value: bool):
        for v in self.cat_vars.values():
            v.set(value)
        self.update_summary()

    def update_summary(self):
        picked = self.picked_keys()
        _, total = dry_run_lines(self.types_meta, self.sets, self.already, picked)
        self.grant_btn.configure(
            text=f"Grant {total} NEW" if picked else "Grant",
            state="normal" if (self.gf and total) else "disabled")

    # ---------- grant flow ----------
    def grant(self):
        sel = self.player_list.curselection()
        if not sel or self.gf is None:
            return
        target = self.saves[sel[0]]
        picked = self.picked_keys()
        grant_sets = {k: self.sets[k] for k in picked}
        lines, total = dry_run_lines(self.types_meta, self.sets, self.already, picked)
        if total == 0:
            messagebox.showinfo("Effigy Grant", "Nothing to grant.")
            return
        if not messagebox.askyesno(
                "Effigy Grant",
                f"Grant {total} new effigies to\n{self.display_name(target)}?\n\n"
                + "\n".join(lines)
                + "\n\nA timestamped backup is created first."):
            return

        newly = ge.count_new(self.rd, grant_sets)
        pm_before = ge.possess_map_values(self.rd)
        num_before = ge.possess_num(self.rd)
        ge.apply_grants(self.rd, grant_sets, zero_uuid=sio.zero_uuid())
        backup = sio.write_player(target, self.gf, self.save_type)
        self.log(f"backup: {backup.name}")

        # Same self-verify as the CLI: re-decode what we wrote.
        try:
            rd2 = sio.record_data(sio.read_player(target)[0])
            got = ge.collected_by_type(rd2)
            for key, guids in grant_sets.items():
                assert guids <= got.get(key, set()), f"flags missing in {key}"
            pm2 = ge.possess_map_values(rd2)
            for k in grant_sets:
                enum_name = ge.RELIC_ENUM_BY_KEY[k]
                want = pm_before.get(enum_name, 0) + newly[k]
                assert pm2.get(enum_name, 0) == want, f"balance wrong for {enum_name}"
            if "capture_power" in grant_sets:
                want_num = num_before + newly["capture_power"]
                assert ge.possess_num(rd2) == want_num, "RelicPossessNum wrong"
        except Exception as e:
            sio.restore_backup(target, backup)
            messagebox.showerror("Effigy Grant",
                                 f"VERIFY FAILED — original restored:\n{e}")
            self.log(f"VERIFY FAILED, restored: {e}")
            return

        self.log(f"OK: wrote {target.name}, verified {total} new effigies")
        messagebox.showinfo(
            "Effigy Grant",
            f"Done — {total} effigies granted and verified.")
        # Refresh state so a second grant shows correct counts.
        self.pick_player()


def main() -> int:
    root = tk.Tk()
    # Official-source notice must be acknowledged before the main window
    # opens: keep the root hidden until OK is clicked.
    root.withdraw()
    messagebox.showinfo("Official Source Notice", OFFICIAL_SOURCE_NOTICE,
                        parent=root)
    app = App(root)
    root.deiconify()
    # Open Help beside the main window on startup, scrolled to the top.
    root.update_idletasks()  # realize geometry so winfo_* is accurate
    app.show_help()
    app.help_text.yview_moveto(0.0)
    app.help_win.geometry(
        f"+{root.winfo_x() + root.winfo_width() + 12}+{root.winfo_y()}")
    root.lift()
    root.focus_force()  # keep keyboard focus on the main window
    if len(sys.argv) > 1:  # optional: launch with a folder pre-filled
        app.dir_var.set(sys.argv[1])
        app.load_dir()
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
