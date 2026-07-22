#!/usr/bin/env python3
"""grant_cli.py v1.4 — interactive effigy grant tool for Palworld player saves.

Copyright © 2026 AvenisLabs (https://avenislabs.com)
for KarasWorlds.com (https://karasworlds.com). All rights reserved.

v1.4: copyright notice added.
v1.3: sanitized — server-specific references removed from docs and output.
v1.2: docs — tool moved to its own repo root (was tools/effigy_grant/).
v1.1: player names load automatically when Level.sav is present (fast since
      grant_savio v1.4 passes type_hints correctly) — no prompt.

Usage: python grant_cli.py <save_dir> [--master PATH] [--no-union]

<save_dir> is a COPY of the world save folder containing Players/*.sav (and
optionally Level.sav for player names). Never point this at a live save while
the server is running — the game autosaves continuously. See README.md for
the stop -> copy -> edit -> copy back -> start workflow.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # dual-mode contract
import grant_edits as ge
import grant_master as gm
import grant_savio as sio


def parse_selection(text: str, n: int) -> list[int]:
    """'all' | '1' | '1,3-5' -> sorted unique 1-based indices within [1, n]."""
    text = text.strip().lower()
    if not text:
        raise ValueError("empty selection")
    if text == "all":
        return list(range(1, n + 1))
    picked: set[int] = set()
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            lo_s, _, hi_s = part.partition("-")
            lo, hi = int(lo_s), int(hi_s)   # ValueError propagates on junk
            if lo > hi:
                raise ValueError(f"backwards range: {part}")
            picked.update(range(lo, hi + 1))
        else:
            picked.add(int(part))
    if not picked or min(picked) < 1 or max(picked) > n:
        raise ValueError(f"selection out of range 1-{n}")
    return sorted(picked)


def _ask(msg: str) -> str:
    try:
        return input(msg)
    except EOFError:
        return ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Grant Pal Effigies by category")
    ap.add_argument("save_dir", type=Path,
                    help="copied save folder containing Players/*.sav")
    ap.add_argument("--master", type=Path, default=gm.DEFAULT_MASTER,
                    help="override relic_master.json")
    ap.add_argument("--no-union", action="store_true",
                    help="skip unioning GUIDs observed in sibling player saves")
    args = ap.parse_args(argv)

    saves = sio.list_player_saves(args.save_dir)
    if not saves:
        print(f"no player saves under {args.save_dir / 'Players'}", file=sys.stderr)
        return 2

    names = sio.player_names(args.save_dir)  # {} when Level.sav absent/unreadable

    print("\nPlayers:")
    for i, p in enumerate(saves, 1):
        uid = p.stem.upper()
        label = names.get(uid)
        print(f"  {i:2}. {label}  ({uid[:8]})" if label else f"  {i:2}. {uid}")
    try:
        idx = parse_selection(_ask("Pick a player [number]: "), len(saves))
    except ValueError as e:
        print(f"invalid selection: {e}", file=sys.stderr)
        return 2
    if len(idx) != 1:
        print("pick exactly one player", file=sys.stderr)
        return 2
    target = saves[idx[0] - 1]
    print(f"target: {target.name}")

    # Decode target + siblings (siblings feed the observed-GUID union).
    gf, save_type = sio.read_player(target)
    rd = sio.record_data(gf)
    master = gm.load_master(args.master)
    sets, types_meta = master["sets"], master["types"]
    if not args.no_union:
        others = []
        for p in saves:
            if p == target:
                others.append(rd)
                continue
            try:
                others.append(sio.record_data(sio.read_player(p)[0]))
            except Exception as e:  # one bad sibling must not stall the tool
                print(f"  warning: skipping {p.name}: {e}", file=sys.stderr)
        sets, extras = gm.union_observed(sets, others)
        if extras:
            n = sum(len(v) for v in extras.values())
            print(f"union: +{n} observed GUID(s) not in master "
                  f"({', '.join(sorted(extras))})")

    ordered = [k for k in ge.RELIC_ENUM_BY_KEY if k in sets]
    already = ge.collected_by_type(rd)
    print("\nCategories:")
    for i, key in enumerate(ordered, 1):
        meta = types_meta.get(key, {})
        have = len(already.get(key, set()) & sets[key])
        print(f"  {i:2}. {meta.get('name', key):18} ({meta.get('effect', '?')}): "
              f"{have}/{len(sets[key])} collected")
    try:
        picks = parse_selection(_ask("Grant which categories? (e.g. 1,3-5 or all): "),
                                len(ordered))
    except ValueError as e:
        print(f"invalid selection: {e}", file=sys.stderr)
        return 2
    grant_sets = {ordered[i - 1]: sets[ordered[i - 1]] for i in picks}

    newly = ge.count_new(rd, grant_sets)
    print("\nDry run:")
    for key in grant_sets:
        meta = types_meta.get(key, {})
        total = len(grant_sets[key])
        print(f"  {meta.get('name', key):18} total {total:3}  "
              f"already {total - newly[key]:3}  NEW {newly[key]:3}"
              + ("  (+legacy capture mirror)" if key == "capture_power" else ""))
    total_new = sum(newly.values())
    if total_new == 0:
        print("nothing to grant — everything already collected.")
        return 0
    print(f"  -> {total_new} effigies will be granted (collected + spendable)")

    if _ask("Type YES to write the save: ").strip() != "YES":
        print("aborted, nothing written.")
        return 1

    # Expected post-write balances for self-verification.
    pm_before = ge.possess_map_values(rd)
    num_before = ge.possess_num(rd)
    ge.apply_grants(rd, grant_sets, zero_uuid=sio.zero_uuid())
    expect_pm = {ge.RELIC_ENUM_BY_KEY[k]:
                 pm_before.get(ge.RELIC_ENUM_BY_KEY[k], 0) + newly[k]
                 for k in grant_sets}
    expect_num = num_before + newly.get("capture_power", 0)

    backup = sio.write_player(target, gf, save_type)
    print(f"backup: {backup.name}")

    # Self-verify: re-decode the file we just wrote.
    try:
        rd2 = sio.record_data(sio.read_player(target)[0])
        got = ge.collected_by_type(rd2)
        for key, guids in grant_sets.items():
            assert guids <= got.get(key, set()), f"flags missing in {key}"
        pm2 = ge.possess_map_values(rd2)
        for enum_name, want in expect_pm.items():
            assert pm2.get(enum_name, 0) == want, f"balance wrong for {enum_name}"
        if "capture_power" in grant_sets:
            assert ge.possess_num(rd2) == expect_num, "RelicPossessNum wrong"
    except Exception as e:
        sio.restore_backup(target, backup)
        print(f"VERIFY FAILED — original restored from backup: {e}", file=sys.stderr)
        return 1

    print(f"OK: wrote {target.name} and verified {total_new} new effigies.")
    print("Copy the file back with the server STOPPED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
