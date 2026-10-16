"""Everything that depends on how big a tile is, in one place.

A tile is one metre (the island map in murder/maps/, built by gridmap.py). The distances below were first written for the old schematic, whose tiles were also
about a metre, so `MAP_SCALE` is 1.0: a whisper carries 2 m, normal speech 8, a shout 18; you see 18 m in light and 2 in the dark. Change MAP_SCALE (or set
MC_MAP_SCALE) to scale all of them together. How fast people walk is set in sim.py.
"""
import os

MAP_SCALE = float(os.environ.get("MC_MAP_SCALE", "1.0"))


def tiles(v, lo=1.0):
    """A distance that used to be `v` tiles on the 1.0 map."""
    return max(lo, round(v * MAP_SCALE, 1))


def area(v):
    """An interior area (in tiles) that used to be `v` on the 1.0 map."""
    return int(v * MAP_SCALE * MAP_SCALE)
