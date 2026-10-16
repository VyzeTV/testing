"""Everything that depends on how big a tile is, in one place.

The island is one section made of 4x4-tile rooms, so a tile is roughly a metre and a half. The old schematic had rooms of about twelve tiles; `MAP_SCALE` (0.35) is the ratio, and every distance that used
to be measured on the old scale is multiplied by it: how far a whisper or a shout carries, how far you can see in light and in the dark, what blocks sound, and when a space is big enough to hold
two separate conversations. How fast people walk is set in livetimeline.py (a stroll of a few tiles a minute, a hurry of twelve). Change MAP_SCALE (or set MC_MAP_SCALE) and everything below follows;
the map itself is laid out in gridmap.py (LAYOUT) and regenerated with `python -m murder.gridmap`.
"""
import os

MAP_SCALE = float(os.environ.get("MC_MAP_SCALE", "0.35"))


def tiles(v, lo=1.0):
    """A distance that used to be `v` tiles on the 1.0 map."""
    return max(lo, round(v * MAP_SCALE, 1))


def area(v):
    """An interior area (in tiles) that used to be `v` on the 1.0 map."""
    return int(v * MAP_SCALE * MAP_SCALE)
