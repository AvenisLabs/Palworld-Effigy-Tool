#!/usr/bin/env python3
"""grant_savio.py v1.5 — PlM save decode/encode for the effigy grant tool.

v1.5: relocation-aware fork lookup — the tool now lives in its own repo
      (F:/Workspace/Palworld_effigy), so the fork is probed at: EFFIGY_FORK_DIR,
      a repo-local cache/PalworldSaveTools, the old tools/-sibling layout, then
      the original palworld repo's cache as a machine-specific fallback.
v1.4: FIX — GvasFile.read's 2nd positional arg is type_hints, NOT
      custom_properties; we were passing the custom-props dict into the
      hints slot. Harmless for player saves (no custom paths, byte-identical
      round-trip regardless) but fatal for Level.sav, whose map key/value
      struct types come from PALWORLD_TYPE_HINTS — this, not torn copies,
      is why player_names always failed. Both are now passed correctly.
v1.3: frozen-aware bootstrap — in a PyInstaller bundle, palsav/palooz are
      collected into the exe, so the fork-path sys.path insertion is skipped.
v1.2: silence palsav INFO chatter (compress/decompress progress lines).
v1.1: player_names tolerates a torn/unreadable Level.sav (returns {}).

The ONLY module that imports the cached PalworldSaveTools fork (palsav +
palooz Oodle ext). Bootstraps sys.path before the palsav imports because
palsav.core instantiates its Oodle compressor at import time.
"""
import datetime
import logging
import os
import re
import shutil
import sys
from pathlib import Path

# palsav logs every compress/decompress at INFO; keep the tool's output clean.
logging.getLogger("palsav").setLevel(logging.WARNING)

_HERE = Path(__file__).resolve().parent
_ENV_FORK = os.environ.get("EFFIGY_FORK_DIR")
if _ENV_FORK:
    _FORK = Path(_ENV_FORK)  # explicit override always wins (and names the error)
else:
    # Probe order: repo-local vendor dir (standalone layout), old palworld-repo
    # layout (tool once lived at tools/effigy_grant/), then the original repo's
    # cache on this machine as a last-resort convenience fallback.
    _CANDIDATES = [
        _HERE / "cache" / "PalworldSaveTools",
        _HERE.parent / "paldex_import" / "cache" / "PalworldSaveTools",
        Path("F:/Workspace/palworld/tools/paldex_import/cache/PalworldSaveTools"),
    ]
    _FORK = next((c for c in _CANDIDATES if (c / "src" / "palsav").is_dir()),
                 _CANDIDATES[0])
_PALSAV = _FORK / "src" / "palsav"
# Prebuilt Windows palooz (cp312). On Linux, palooz comes from the rig's venv
# (pip install ./PalworldSaveTools/src/palsav/palooz) so the dir just won't exist.
_PALOOZ_WIN = _PALSAV / "palooz" / "build" / "lib.win-amd64-cpython-312"

if not getattr(sys, "frozen", False):  # frozen exe ships palsav+palooz inside
    if not _PALSAV.is_dir():
        raise FileNotFoundError(
            f"PalworldSaveTools fork not found at {_FORK} — set EFFIGY_FORK_DIR")
    for _p in (str(_PALSAV), str(_PALOOZ_WIN)):
        if os.path.isdir(_p) and _p not in sys.path:
            sys.path.insert(0, _p)

from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav  # noqa: E402
from palsav.gvas import GvasFile                                      # noqa: E402
from palsav.paltypes import (PALWORLD_CUSTOM_PROPERTIES,              # noqa: E402
                             PALWORLD_TYPE_HINTS)
from palsav.archive import UUID as _UUID                              # noqa: E402

decompress = decompress_sav_to_gvas  # re-export for tests

_SAVE_NAME = re.compile(r"^([0-9A-Fa-f]{32})\.sav$")


def player_uid_from_filename(name: str) -> str | None:
    """'023E18B2...0.sav' -> dashed uid; None for _dps sidecars/non-players."""
    m = _SAVE_NAME.match(name)
    if not m:
        return None
    h = m.group(1).lower()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def list_player_saves(save_dir: Path) -> list[Path]:
    players = Path(save_dir) / "Players"
    if not players.is_dir():
        return []
    return sorted(p for p in players.glob("*.sav")
                  if player_uid_from_filename(p.name))


def zero_uuid():
    return _UUID(b"\x00" * 16)


def read_player(path: Path):
    gvas, save_type = decompress_sav_to_gvas(Path(path).read_bytes())
    return GvasFile.read(gvas, PALWORLD_TYPE_HINTS,
                         PALWORLD_CUSTOM_PROPERTIES), save_type


def record_data(gvas_file) -> dict:
    try:
        return gvas_file.properties["SaveData"]["value"]["RecordData"]["value"]
    except KeyError:
        raise ValueError("save has no RecordData — the player must have "
                         "logged in at least once") from None


def write_player(path: Path, gvas_file, save_type: int) -> Path:
    """Backup the original, then atomically replace it with the edited save."""
    path = Path(path)
    sav = compress_gvas_to_sav(gvas_file.write(PALWORLD_CUSTOM_PROPERTIES),
                               save_type)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{ts}")
    shutil.copy2(path, backup)
    tmp = path.with_name(path.name + ".new")
    tmp.write_bytes(sav)
    os.replace(tmp, path)
    return backup


def restore_backup(path: Path, backup: Path) -> None:
    shutil.copy2(backup, path)


def _skip_decode(reader, type_name, size, path):
    """Read-and-carry raw bytes for sections we never touch (read-only use;
    Level.sav is never re-encoded by this tool). Copy of the fork's
    palobject.skip_decode minus the encode half."""
    if type_name == "ArrayProperty":
        return {"skip_type": type_name, "array_type": reader.fstring(),
                "id": reader.optional_guid(), "value": reader.read(size)}
    if type_name == "MapProperty":
        return {"skip_type": type_name, "key_type": reader.fstring(),
                "value_type": reader.fstring(), "id": reader.optional_guid(),
                "value": reader.read(size)}
    if type_name == "StructProperty":
        return {"skip_type": type_name, "struct_type": reader.fstring(),
                "struct_id": reader.guid(), "id": reader.optional_guid(),
                "value": reader.read(size)}
    raise Exception(f"unexpected skip type {type_name} at {path}")


# Level.sav sections irrelevant to name lookup — skipping them makes the
# decode tractable (CharacterSaveParameterMap alone is most of the file).
_LEVEL_SKIP_PATHS = (
    ".worldSaveData.CharacterSaveParameterMap",
    ".worldSaveData.MapObjectSaveData",
    ".worldSaveData.FoliageGridSaveDataMap",
    ".worldSaveData.MapObjectSpawnerInStageSaveData",
    ".worldSaveData.ItemContainerSaveData",
    ".worldSaveData.DynamicItemSaveData",
    ".worldSaveData.CharacterContainerSaveData",
    ".worldSaveData.WorkSaveData",
    ".worldSaveData.BaseCampSaveData",
)


def player_names(save_dir: Path) -> dict[str, str]:
    """uid (32-hex upper) -> player name via Level.sav GroupSaveDataMap.
    Returns {} when Level.sav is absent OR unparseable — copies taken while
    the game autosaves are often torn (names are cosmetic, never fail on them).
    Slow (tens of seconds)."""
    level = Path(save_dir) / "Level.sav"
    if not level.is_file():
        return {}
    props = dict(PALWORLD_CUSTOM_PROPERTIES)
    for p in _LEVEL_SKIP_PATHS:
        props[p] = (_skip_decode, None)
    try:
        gvas, _ = decompress_sav_to_gvas(level.read_bytes())
        gf = GvasFile.read(gvas, PALWORLD_TYPE_HINTS, props)
    except Exception as e:
        # e.g. a copy torn by the game's continuous autosave
        print(f"warning: Level.sav unreadable, no names: {e!r:.120}",
              file=sys.stderr)
        return {}
    out: dict[str, str] = {}
    wsd = gf.properties["worldSaveData"]["value"]
    for g in (wsd.get("GroupSaveDataMap", {}).get("value") or []):
        raw = ((g.get("value") or {}).get("RawData") or {}).get("value") or {}
        if raw.get("guild_name") is None:
            continue
        for m in raw.get("players", []):
            uid = str(m.get("player_uid", "")).replace("-", "").upper()
            name = (m.get("player_info") or {}).get("player_name")
            if len(uid) == 32 and name:
                out[uid] = str(name)
    return out
