#!/usr/bin/env python3
"""grant_gui.py v1.2 — minimal tkinter GUI for the effigy grant tool.

v1.2: sanitized — server-specific references removed from the done dialog.

Thin window over grant_edits/grant_master/grant_savio (all logic lives
there): pick save folder -> pick player -> tick categories -> Grant.
Same safety rails as the CLI: timestamped backup, post-write re-decode
verification with automatic restore on mismatch.

v1.1: player list shows names, not UIDs — Level.sav is decoded automatically
      in the background on folder load; UID is the fallback when no name is
      available (no Level.sav, or a torn copy).
"""
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
        root.title("Effigy Grant Tool")
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
        ttk.Entry(top, textvariable=self.dir_var).pack(side="left", fill="x",
                                                       expand=True)
        ttk.Button(top, text="Browse…", command=self.browse).pack(side="left", padx=4)
        ttk.Button(top, text="Load", command=self.load_dir).pack(side="left")

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
        ttk.Button(btns, text="All", command=lambda: self.set_all(True)).pack(
            side="left", expand=True, fill="x")
        ttk.Button(btns, text="None", command=lambda: self.set_all(False)).pack(
            side="left", expand=True, fill="x")

        bottom = ttk.Frame(root, padding=6)
        bottom.pack(fill="x")
        self.grant_btn = ttk.Button(bottom, text="Grant", command=self.grant,
                                    state="disabled")
        self.grant_btn.pack(side="right")
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
        d = filedialog.askdirectory(title="Save folder (contains Players/)")
        if d:
            self.dir_var.set(d)
            self.load_dir()

    # ---------- load flow ----------
    def load_dir(self):
        save_dir = Path(self.dir_var.get().strip())
        self.saves = sio.list_player_saves(save_dir)
        self.player_list.delete(0, "end")
        self.gf = None
        if not self.saves:
            messagebox.showerror("Effigy Grant",
                                 f"No player saves under {save_dir / 'Players'}")
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
            f"Done — {total} effigies granted and verified.\n\n"
            "Copy the file back with the server STOPPED.")
        # Refresh state so a second grant shows correct counts.
        self.pick_player()


def main() -> int:
    root = tk.Tk()
    app = App(root)
    if len(sys.argv) > 1:  # optional: launch with a folder pre-filled
        app.dir_var.set(sys.argv[1])
        app.load_dir()
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
