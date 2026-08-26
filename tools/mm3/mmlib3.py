"""
mmlib3 -- readers for Might & Magic III: Isles of Terra (PC / MS-DOS, New World
Computing, 1991).

The whole game is two `.CC` archives plus a doubly packed loader. Everything
here was derived from the shipped files; see docs/mm3/ for how. Paths default
to gamedata/mm3 and can be overridden with the MM3_DATA environment variable.
"""
import os, struct, collections

import lzhuf
import exeunpack

DATA = os.environ.get('MM3_DATA', os.path.join('gamedata', 'mm3'))

# The directory is obfuscated: rotate each byte left by two, then add a key
# that starts at 0xAC and advances by 0x67 for every byte of the directory.
# The routine that does it is in the unpacked MM3.EXE -- see docs/mm3/03.
ROT, KEY0, KEY_STEP, ENTRY = 2, 0xAC, 0x67, 8

# Members whose name starts with these four characters are stored verbatim;
# every other member is LZHUF-compressed. The game decides by name, comparing
# against this literal in the archive module.
RAW_PREFIX = 'MAZE'


def path(name):
    return os.path.join(DATA, name)


Member = collections.namedtuple('Member', 'id offset size')


def hash_name(name):
    """The 16-bit value the directory stores in place of a filename: swap the
    halves of a 16-bit accumulator, rotate it left one, add the next character
    folded to upper case. Verified against every driver name in the binary."""
    v = 0
    for ch in name.encode():
        c = ch & 0x7F
        if c >= 0x60:
            c -= 0x20
        v = ((v >> 8) | (v << 8)) & 0xFFFF
        v = ((v << 1) | (v >> 15)) & 0xFFFF
        v = (v + c) & 0xFFFF
    return v


def read_directory(fname='MM3.CC'):
    """[Member] in stored order. `id` is hash_name() of the member's original
    filename; the archive stores no names."""
    d = open(path(fname), 'rb').read()
    n = struct.unpack('<H', d[:2])[0]
    raw = d[2:2 + ENTRY * n]
    plain, key = bytearray(len(raw)), KEY0
    for i, b in enumerate(raw):
        plain[i] = ((((b << ROT) | (b >> (8 - ROT))) & 0xFF) + key) & 0xFF
        key = (key + KEY_STEP) & 0xFF
    out = []
    for i in range(n):
        e = plain[ENTRY * i:ENTRY * (i + 1)]
        out.append(Member(int.from_bytes(e[0:2], 'little'),
                          int.from_bytes(e[2:5], 'little'),
                          int.from_bytes(e[5:7], 'little')))
    return out


def read_stored(member, fname='MM3.CC'):
    """The member exactly as it sits in the archive."""
    d = open(path(fname), 'rb').read()
    return d[member.offset:member.offset + member.size]


def compressed_header(stored):
    """(ring-buffer fill byte, uncompressed size) for a compressed member, or
    None. The header is four bytes: the fill byte twice, then the size as a
    big-endian word -- the one big-endian field in the whole format."""
    if len(stored) < 4 or stored[0] != stored[1]:
        return None
    size = (stored[2] << 8) | stored[3]
    return (stored[0], size) if size >= len(stored) else None


def read_member(member, fname='MM3.CC'):
    """A member's content, decompressed if it is compressed.

    The game itself decides by name -- names beginning with RAW_PREFIX are
    stored verbatim -- but the archive holds no names, so this decides by
    measurement instead: a member is compressed when it carries a plausible
    header *and* decoding it consumes the stored bytes exactly. That separates
    the two archives cleanly (556 of 558 in MM3.CC, none of the 65 header-
    shaped members of MM3.CUR).
    """
    stored = read_stored(member, fname)
    head = compressed_header(stored)
    if head is None:
        return stored
    fill, size = head
    try:
        out, bits = lzhuf.decompress(stored[4:], size, fill, want_bits=True)
    except (IndexError, ValueError):
        return stored
    return out if 0 <= (len(stored) - 4) * 8 - bits <= 8 else stored


def tiling(fname='MM3.CC'):
    """(overlapping members, bytes not covered by any member).

    Both are zero for both shipped archives, which is what confirms the
    directory has been decoded correctly.
    """
    d_len = os.path.getsize(path(fname))
    ents = read_directory(fname)
    body = 2 + ENTRY * len(ents)
    spans = sorted((m.offset, m.size) for m in ents)
    unused = spans[0][0] - body + d_len - (spans[-1][0] + spans[-1][1])
    over = 0
    for a, b in zip(spans, spans[1:]):
        gap = b[0] - (a[0] + a[1])
        if gap < 0:
            over += 1
        else:
            unused += gap
    return over, unused


def unpack_exe(fname='MM3.EXE'):
    """The running program image, its relocations and its overlay pool."""
    return exeunpack.unpack(open(path(fname), 'rb').read())
