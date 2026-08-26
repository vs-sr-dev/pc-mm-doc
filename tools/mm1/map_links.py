#!/usr/bin/env python3
"""Resolve where each map's four edges lead.

Parameter bytes 8..19 of an overlay hold four (key-low, key-high, map type)
triples, one per edge. The engine turns a triple into a map number in the
helper at 0x0D71: it builds the 16-bit key (high << 8) | low and scans the
per-map key table at DS:0x017B, starting at the first map of the given type
(DS:0x0173 holds those three start offsets). See doc 7.

  python tools/mm1/map_links.py            # every map's four neighbours
  python tools/mm1/map_links.py --check    # reciprocity test
  python tools/mm1/map_links.py --grid     # the 5x4 outdoor grid
"""
import os, sys, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib

KEYTAB, TYPETAB = 0x017B, 0x0173
# parameter index of each edge triple, and the engine routine that reads it
EDGES = [('N', 8, 'yplus'), ('E', 11, 'xplus'), ('S', 14, 'ymin'), ('W', 17, 'xmin')]
OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}


def _tables():
    d = open(mmlib.path('MM.EXE'), 'rb').read()
    b = mmlib.DATA_SEG_FILE_BASE
    word = lambda o: struct.unpack('<H', d[b+o:b+o+2])[0]
    keys = [word(KEYTAB + 2*i) for i in range(len(mmlib.MAPS))]
    starts = {t: word(TYPETAB + 2*t) // 2 for t in (1, 2, 3)}
    return keys, starts

KEYS, STARTS = _tables()


def resolve(lo, hi, maptype):
    """A (key-low, key-high, map type) triple -> map number, or None."""
    if maptype not in STARTS:
        return None
    key = (hi << 8) | lo
    for i in range(STARTS[maptype], len(KEYS)):
        if KEYS[i] == key:
            return i
    return None


def params(name):
    d = open(mmlib.path(name.upper() + '.OVR'), 'rb').read()
    csz = struct.unpack('<H', d[4:6])[0]
    return d[14 + csz:14 + csz + 50]


def links(name):
    p = params(name)
    return {d: resolve(p[i], p[i+1], p[i+2]) for d, i, _ in EDGES}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ''
    names = mmlib.MAPS[14:34] if arg == '--grid' else mmlib.MAPS
    if arg == '--check':
        ok, edge, oneway, unresolved = 0, 0, [], []
        for m in mmlib.MAPS:
            here = mmlib.MAPS.index(m)
            for d, _, _ in EDGES:
                t = links(m)[d]
                if t is None:
                    unresolved.append(f'{m} {d}')
                elif t == here:
                    edge += 1            # points at itself: the world stops here
                elif links(mmlib.MAPS[t])[OPPOSITE[d]] == here:
                    ok += 1
                else:
                    oneway.append(f'{m} {d} -> {mmlib.MAPS[t]}')
        total = len(mmlib.MAPS) * 4
        print(f'{ok} reciprocal, {edge} self (map edge), '
              f'{len(oneway)} one-way, {len(unresolved)} unresolved, of {total}')
        for x in oneway:
            print(f'  one-way:    {x}')
        for x in unresolved:
            print(f'  unresolved: {x}')
        return
    for m in names:
        l = links(m)
        cell = lambda d: mmlib.MAPS[l[d]] if l[d] is not None else '?'
        print(f'  {m:<9s} N={cell("N"):<9s} E={cell("E"):<9s} '
              f'S={cell("S"):<9s} W={cell("W"):<9s}')


if __name__ == '__main__':
    main()
