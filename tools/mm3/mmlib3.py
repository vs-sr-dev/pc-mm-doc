"""
mmlib3 -- readers for Might & Magic III: Isles of Terra (PC / MS-DOS, New World
Computing, 1991).

The whole game is two `.CC` archives. Everything here was derived from the
shipped files; see docs/mm3/ for how. Paths default to gamedata/mm3 and can be
overridden with the MM3_DATA environment variable.
"""
import os, struct, collections

DATA = os.environ.get('MM3_DATA', os.path.join('gamedata', 'mm3'))

# The directory is obfuscated: rotate each byte left by two, then subtract a
# key that starts at 0x54 and advances by 0x99 for every byte of the directory.
# Both constants were solved for, not assumed -- see docs/mm3/01.
ROT, KEY0, KEY_STEP, ENTRY = 2, 0x54, 0x99, 8


def path(name):
    return os.path.join(DATA, name)


Member = collections.namedtuple('Member', 'id offset size')


def read_directory(fname='MM3.CC'):
    """[Member] in stored order. `id` is a 16-bit hash of the member's
    original filename; the hash function is not solved, so members have no
    names here."""
    d = open(path(fname), 'rb').read()
    n = struct.unpack('<H', d[:2])[0]
    raw = d[2:2 + ENTRY * n]
    plain, key = bytearray(len(raw)), KEY0
    for i, b in enumerate(raw):
        plain[i] = ((((b << ROT) | (b >> (8 - ROT))) & 0xFF) - key) & 0xFF
        key = (key + KEY_STEP) & 0xFF
    out = []
    for i in range(n):
        e = plain[ENTRY * i:ENTRY * (i + 1)]
        out.append(Member(int.from_bytes(e[0:2], 'little'),
                          int.from_bytes(e[2:5], 'little'),
                          int.from_bytes(e[5:7], 'little')))
    return out


def read_member(member, fname='MM3.CC'):
    """The stored bytes of one member. In MM3.CC these are compressed; in
    MM3.CUR they are not. The compression is not solved."""
    d = open(path(fname), 'rb').read()
    return d[member.offset:member.offset + member.size]


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
