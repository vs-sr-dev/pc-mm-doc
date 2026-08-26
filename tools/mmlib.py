"""
mmlib -- readers for the data files of Might & Magic: Secret of the Inner Sanctum
(PC / MS-DOS, New World Computing, 1987).

Everything here was derived by inspecting the shipped files; see docs/ for how
each format was established. Paths are relative to the repository root by
default and can be overridden with the MM1_DATA environment variable.
"""
import os, struct

DATA = os.environ.get('MM1_DATA', 'gamedata')

# --- map / overlay index ------------------------------------------------------
# The 55 map names, in the order they appear in the table at DS:0x0A07 in MM.EXE.
# This order is the map index used by MAZEDATA.DTA; name + ".OVR" is the map's
# event-code overlay.
MAPS = """sorpigal portsmit algary dusk erliquin
cave1 cave2 cave3 cave4 cave5 cave6 cave7 cave8 cave9
areaa1 areaa2 areaa3 areaa4 areab1 areab2 areab3 areab4
areac1 areac2 areac3 areac4 aread1 aread2 aread3 aread4
areae1 areae2 areae3 areae4
doom blackrn blackrs qvl1 qvl2 rwl1 rwl2 enf1 enf2 whitew
dragad udrag1 udrag2 udrag3 demon alamar pp1 pp2 pp3 pp4 astral""".split()

def path(name):
    return os.path.join(DATA, name)

# --- RLE ----------------------------------------------------------------------
ESC = 0x7B

def unrle(buf):
    """0x7B <count> <value> -> (count+1) copies; anything else is a literal.
    A literal 0x7B is encoded as 0x7B 0x00 0x7B."""
    out = bytearray(); i = 0
    while i < len(buf):
        if buf[i] == ESC and i + 2 < len(buf):
            out.extend(bytes([buf[i+2]]) * (buf[i+1] + 1)); i += 3
        else:
            out.append(buf[i]); i += 1
    return bytes(out)

def enrle(buf):
    """Inverse of unrle. Runs of 4+ become escapes; that is the break-even point."""
    out = bytearray(); i = 0
    while i < len(buf):
        v = buf[i]; n = 1
        while n < 256 and i + n < len(buf) and buf[i+n] == v:
            n += 1
        if n >= 4 or v == ESC:
            out += bytes([ESC, n - 1, v]); i += n
        else:
            out += bytes([v]); i += 1
    return bytes(out)

# --- picture containers -------------------------------------------------------
def read_screen(n):
    """SCREEN0..SCREEN9 -> 16000 raw bytes (one full CGA 320x200 frame)."""
    d = open(path(f'SCREEN{n}'), 'rb').read()
    return unrle(d[2:2 + struct.unpack('<H', d[:2])[0]])

def read_library(fname):
    """WALLPIX.DTA / MONPIX.DTA.

    word0        = size of the offset table in bytes (4 * image count)
    dword[k]     = offset of image k, relative to the end of the table
    each image   = word length, then that many RLE bytes
    """
    d = open(path(fname), 'rb').read()
    n = struct.unpack('<H', d[:2])[0] // 4
    offs = [struct.unpack('<I', d[2+4*k:6+4*k])[0] for k in range(n)]
    base = 2 + n * 4
    imgs = []
    for o in offs:
        ln = struct.unpack('<H', d[base+o:base+o+2])[0]
        imgs.append(unrle(d[base+o+2 : base+o+2+ln]))
    return imgs

# --- CGA ----------------------------------------------------------------------
PAL = [(0, 0, 0), (85, 255, 255), (255, 85, 255), (255, 255, 255)]

def to_rgb(buf, cols, height, pal=PAL):
    """Decode a column-major CGA buffer: byte index = column * height + row,
    4 pixels per byte, 2 bits each, most significant pair leftmost."""
    return [[pal[(buf[c*height + y] >> s) & 3] for c in range(cols) for s in (6,4,2,0)]
            for y in range(height)]

# --- MAZEDATA.DTA -------------------------------------------------------------
# 55 blocks of 512 bytes, one per map, in MAPS order.
#   bytes   0..255  wall plane   (physical walls: what blocks movement)
#   bytes 256..511  second plane (per-side attribute; see docs/03)
# Each plane is a 16x16 grid, row-major, one byte per tile holding four 2-bit
# fields:  bits 0-1 = -X side, 2-3 = -Y side, 4-5 = +X side, 6-7 = +Y side.
W_MINUS_X, W_MINUS_Y, W_PLUS_X, W_PLUS_Y = 0, 1, 2, 3

def read_maze(which):
    i = MAPS.index(which) if isinstance(which, str) else which
    d = open(path('MAZEDATA.DTA'), 'rb').read()
    blk = d[i*512:(i+1)*512]
    return blk[:256], blk[256:]

def side(plane, x, y, k):
    return (plane[y*16 + x] >> (2*k)) & 3

# --- MM.RSM (linker symbol map) ----------------------------------------------
def read_symbols():
    """Yields (name, type, cls, offset). type 0x02 = code segment,
    0x03 = data segment. The data segment starts at file offset 0x10200."""
    import re
    d = open(path('MM.RSM'), 'rb').read()
    out, i = [], 0x23
    while i < len(d) - 6:
        m = re.match(rb'[A-Za-z_][A-Za-z0-9_$.]*\x00', d[i:i+64])
        if not m:
            i += 1; continue
        p = i + m.end()
        out.append((m.group()[:-1].decode(), d[p], d[p+1],
                    int.from_bytes(d[p+2:p+4], 'little')))
        i = p + 4
    return out

DATA_SEG_FILE_BASE = 0x10200   # file offset of DS:0000 in MM.EXE
