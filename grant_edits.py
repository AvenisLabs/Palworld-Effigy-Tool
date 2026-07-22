#!/usr/bin/env python3
"""grant_edits.py v1.2 — pure GVAS-dict edit logic for the effigy grant tool.

Copyright © 2026 AvenisLabs (https://avenislabs.com)
for KarasWorlds.com (https://karasworlds.com). All rights reserved.

v1.2: copyright notice added.
v1.1: sanitized — server-specific references removed from docs.

Pure functions over already-decoded GVAS dicts, no palsav import,
unit-testable without the Oodle extension.

Field semantics (verified on real dedicated-server saves, 2026-07-22):
- RelicObtainForInstanceFlagByType: authoritative collected flags per category.
- RelicPossessNumMap / RelicPossessNum: UNSPENT Statue of Power balances.
- RelicObtainForInstanceFlag: legacy flat map, set-equal to the CapturePower
  bucket on every player save examined — kept mirrored on capture grants.
MoveSpeed has no placed instances and is never grantable.
"""

# Insertion order here is the canonical menu order (matches relicdata types).
RELIC_ENUM_BY_KEY = {
    "capture_power":         "EPalRelicType::CapturePower",
    "hunger_reduction":      "EPalRelicType::HungerReduction",
    "swim_speed":            "EPalRelicType::SwimSpeed",
    "food_decay_reduction":  "EPalRelicType::FoodDecayReduction",
    "jump_power":            "EPalRelicType::JumpPower",
    "glider_speed":          "EPalRelicType::GliderSpeed",
    "climb_speed":           "EPalRelicType::ClimbSpeed",
    "status_ailment_resist": "EPalRelicType::StatusAilmentResist",
    "stamina_reduction":     "EPalRelicType::StaminaReduction",
    "sphere_homing":         "EPalRelicType::SphereHoming",
    "exp_bonus":             "EPalRelicType::ExpBonus",
    "rainbow_passive_rate":  "EPalRelicType::RainbowPassiveRate",
}
RELIC_KEY_BY_ENUM = {v: k for k, v in RELIC_ENUM_BY_KEY.items()}


def _map_property(key_type: str, value_type: str) -> dict:
    """Empty MapProperty matching the parsed GVAS shape exactly."""
    return {"key_type": key_type, "value_type": value_type,
            "key_struct_type": None, "value_struct_type": None,
            "id": None, "type": "MapProperty", "value": []}


def collected_by_type(record_data: dict) -> dict[str, set[str]]:
    """{type_key: set of UPPERCASE GUIDs flagged true}. Missing property or
    unknown enums mean empty — UE omits properties still at default."""
    prop = record_data.get("RelicObtainForInstanceFlagByType")
    if not isinstance(prop, dict):
        return {}
    out: dict[str, set[str]] = {}
    for entry in ((prop.get("value") or {}).get("values") or []):
        enum = (((entry.get("Type") or {}).get("value") or {}).get("value"))
        key = RELIC_KEY_BY_ENUM.get(enum)
        if key is None:
            continue
        got = {str(f["key"]).upper()
               for f in ((entry.get("Flags") or {}).get("value") or [])
               if f.get("value")}
        if got:
            out[key] = got
    return out


def count_new(record_data: dict, grant_sets: dict[str, set[str]]) -> dict[str, int]:
    """Newly-granted counts apply_grants would produce, without mutating."""
    already = collected_by_type(record_data)
    return {k: len({g.upper() for g in v} - already.get(k, set()))
            for k, v in grant_sets.items()}


def possess_map_values(record_data: dict) -> dict[str, int]:
    prop = record_data.get("RelicPossessNumMap")
    if not isinstance(prop, dict):
        return {}
    return {str(e["key"]): int(e["value"]) for e in (prop.get("value") or [])}


def possess_num(record_data: dict) -> int:
    prop = record_data.get("RelicPossessNum")
    return int(prop["value"]) if isinstance(prop, dict) else 0


def _bytype_values(record_data: dict, zero_uuid) -> list:
    """Entry list of the by-type array, creating the ArrayProperty if absent.
    zero_uuid (palsav UUID(b'\\x00'*16)) is caller-supplied so this module
    stays palsav-free; it is only needed when creating from scratch."""
    prop = record_data.get("RelicObtainForInstanceFlagByType")
    if prop is None:
        if zero_uuid is None:
            raise ValueError("save has no relic array; zero_uuid is required to create it")
        prop = {"array_type": "StructProperty", "id": None, "type": "ArrayProperty",
                "value": {"prop_name": "RelicObtainForInstanceFlagByType",
                          "prop_type": "StructProperty",
                          "type_name": "PalRelicObtainFlagSaveEntry",
                          "id": zero_uuid, "values": []}}
        record_data["RelicObtainForInstanceFlagByType"] = prop
    return prop["value"]["values"]


def _bucket_flags(values: list, enum_name: str) -> list:
    """Flags entry list for a category bucket, creating the bucket if absent."""
    for entry in values:
        if (((entry.get("Type") or {}).get("value") or {}).get("value")) == enum_name:
            return entry["Flags"]["value"]
    entry = {"Type": {"id": None, "type": "EnumProperty",
                      "value": {"type": "EPalRelicType", "value": enum_name}},
             "Flags": _map_property("NameProperty", "BoolProperty")}
    values.append(entry)
    return entry["Flags"]["value"]


def _set_true(entries: list, guids: set[str]) -> None:
    """Force every GUID true in a NameProperty->BoolProperty entry list."""
    by_key = {e["key"]: e for e in entries}
    for g in sorted(guids):
        if g in by_key:
            by_key[g]["value"] = True
        else:
            entries.append({"key": g, "value": True})


def _bump_possess_map(record_data: dict, enum_name: str, newly: int) -> None:
    prop = record_data.get("RelicPossessNumMap")
    if prop is None:
        prop = _map_property("EnumProperty", "IntProperty")
        record_data["RelicPossessNumMap"] = prop
    for e in prop["value"]:
        if str(e["key"]) == enum_name:
            e["value"] = int(e["value"]) + newly
            return
    prop["value"].append({"key": enum_name, "value": newly})


def apply_grants(record_data: dict, grant_sets: dict[str, set[str]],
                 zero_uuid=None) -> dict[str, int]:
    """Grant every GUID in grant_sets as if picked up in the world.

    Sets collection flags, bumps unspent balances by the newly-granted count,
    and for capture_power mirrors the legacy flat map + RelicPossessNum.
    Mutates record_data; returns {type_key: newly_granted}.
    """
    bad = set(grant_sets) - set(RELIC_ENUM_BY_KEY)
    if bad:
        raise ValueError(f"unknown or ungrantable categories: {sorted(bad)}")
    newly_by_key = count_new(record_data, grant_sets)
    values = _bytype_values(record_data, zero_uuid) if grant_sets else []
    for key in sorted(grant_sets):
        enum_name = RELIC_ENUM_BY_KEY[key]
        guids = {g.upper() for g in grant_sets[key]}
        _set_true(_bucket_flags(values, enum_name), guids)
        newly = newly_by_key[key]
        if newly:
            _bump_possess_map(record_data, enum_name, newly)
        if key == "capture_power":
            flat = record_data.get("RelicObtainForInstanceFlag")
            if flat is None:
                flat = _map_property("NameProperty", "BoolProperty")
                record_data["RelicObtainForInstanceFlag"] = flat
            _set_true(flat["value"], guids)
            if newly:
                num = record_data.get("RelicPossessNum")
                if num is None:
                    num = {"id": None, "value": 0, "type": "IntProperty"}
                    record_data["RelicPossessNum"] = num
                num["value"] = int(num["value"]) + newly
    return newly_by_key
