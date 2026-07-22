#!/usr/bin/env python3
"""grant_master.py v1.2 — grant-source GUID sets for the effigy grant tool.

Copyright © 2026 AvenisLabs (https://avenislabs.com)
for KarasWorlds.com (https://karasworlds.com). All rights reserved.

v1.2: copyright notice added.
v1.1: sanitized — server-specific references removed from docs.

Vendored relic_master.json (405 GUIDs, derived from palworld-save-pal's relic
data) plus a union with GUIDs observed as collected in sibling player saves —
the data list is provably missing at least one effigy that exists in-world.
"""
import json
from pathlib import Path

from grant_edits import RELIC_ENUM_BY_KEY, collected_by_type

DEFAULT_MASTER = Path(__file__).resolve().with_name("relic_master.json")


def load_master(path: Path = DEFAULT_MASTER) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cats = data.get("categories") or {}
    unknown = set(cats) - set(RELIC_ENUM_BY_KEY)
    if unknown:
        raise ValueError(f"master lists ungrantable categories: {sorted(unknown)}")
    return {"sets": {k: {g.upper() for g in v} for k, v in cats.items()},
            "types": data.get("types") or {},
            "version": data.get("version")}


def union_observed(sets: dict, record_datas: list) -> tuple[dict, dict]:
    """Union collected GUIDs seen in decoded RecordData dicts into a COPY of
    sets. Returns (merged, extras) where extras holds only GUIDs absent from
    the master — covers effigies missing from the vendored data list."""
    merged = {k: set(v) for k, v in sets.items()}
    extras: dict = {}
    for rd in record_datas:
        for key, got in collected_by_type(rd).items():
            new = got - merged.get(key, set())
            if new:
                merged.setdefault(key, set()).update(new)
                extras.setdefault(key, set()).update(new)
    return merged, extras
