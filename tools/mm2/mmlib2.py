"""
mmlib2 -- readers for the data files of Might & Magic II: Gates to Another World
(PC / MS-DOS, New World Computing, 1988).

Everything here was derived by inspecting the shipped files; see docs/mm2/ for
how each format was established. Paths default to gamedata/mm2 and can be
overridden with the MM2_DATA environment variable.

This module is Might & Magic 2 only; anything shared across the series lives in
the parent tools/ directory.
"""
import os, struct

DATA = os.environ.get('MM2_DATA', os.path.join('gamedata', 'mm2'))


def path(name):
    return os.path.join(DATA, name)


# --- the fourteen code overlays ----------------------------------------------
# Named by *function*, not by map -- the single biggest break from Might &
# Magic 1, where there were 55 overlays, one per map. They are raw code images
# with no header: thirteen of the fourteen begin `55 8B EC`, push bp / mov
# bp,sp, the entry to a C function.
OVERLAYS = """1MENU1 1MENU2 1RETINN 2BRAIN 2CAST1 2CAST2 2CAVES
2CMDS 2COMBAT 2MISC 2MISC2 2PLAY 2SMITH 2TEMPLE""".split()


def overlay(name):
    return open(path(name.upper() + '.OVL'), 'rb').read()


# --- ITEMS.DAT ---------------------------------------------------------------
# 5,120 bytes = 256 records of 20: a 12-byte space-padded name, then 8 bytes of
# stats. Stored uncompressed and in plain ASCII, unlike most of the .DAT files.
ITEM_RECORD, ITEM_NAME = 20, 12


def read_items():
    """[(name, stats)] -- 256 entries, index 0 is the empty slot."""
    d = open(path('ITEMS.DAT'), 'rb').read()
    return [(d[i:i + ITEM_NAME].decode('latin1').rstrip(),
             d[i + ITEM_NAME:i + ITEM_RECORD])
            for i in range(0, len(d), ITEM_RECORD)]


# --- MM2.CH ------------------------------------------------------------------
# 1,024 bytes = 128 glyphs of 8 bytes, one 8x8 bitmap each, one bit per pixel,
# most significant bit leftmost, indexed by ASCII code.
GLYPHS, GLYPH_H = 128, 8


def read_font():
    """[[row bits]] -- 128 glyphs, each 8 rows of 8 booleans."""
    d = open(path('MM2.CH'), 'rb').read()
    return [[[bool(b >> (7 - x) & 1) for x in range(8)]
             for b in d[g * GLYPH_H:(g + 1) * GLYPH_H]] for g in range(GLYPHS)]


# --- ROSTER.DAT and DEFAULT.DAT ----------------------------------------------
# Character records of 130 bytes, name first. DEFAULT.DAT is exactly six of
# them -- the pre-generated starting party the game ships with.
CHAR_RECORD = 130


def read_characters(fname='DEFAULT.DAT'):
    """[(name, rest)] -- one entry per 130-byte slot."""
    d = open(path(fname), 'rb').read()
    out = []
    for i in range(0, len(d) - CHAR_RECORD + 1, CHAR_RECORD):
        r = d[i:i + CHAR_RECORD]
        out.append((r[:r.find(0) if 0 in r[:16] else 16].decode('latin1').rstrip(), r))
    return out


# --- the picture files -------------------------------------------------------
# Every picture ships twice, `NAME.4` for four-colour CGA and `NAME.16` for
# sixteen-colour EGA, 31 pairs in all. Both are compressed -- the byte
# histogram is close to uniform, so it is not Might & Magic 1's run-length
# codec -- and both open with a size-like word. The codec is not solved.
def picture(name, colours=4):
    return open(path(f'{name}.{colours}'), 'rb').read()


def picture_header(name, colours=4):
    """The leading word. It tracks the picture's size but is not a plain
    decompressed length: across the 31 pairs the .16/.4 ratio runs 1.00 to
    2.00, where a straight 2-bit to 4-bit widening would give exactly 2."""
    return struct.unpack('<H', picture(name, colours)[:2])[0]
