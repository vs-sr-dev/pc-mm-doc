#!/usr/bin/env python3
"""Which WALLPIX.DTA sets each map uses.

Parameter bytes 2..7 of an overlay are three 16-bit wall-set keys, in the same
(low, high) form as the map destination keys of doc 7. `loadtype` (0x4639)
feeds each one to `getshape` (0x128C) together with the map type from
parameter 1, and getshape resolves it: the type picks one of three key lists
(pointers at DS:0x043B, starting numbers at DS:0x0441) and the position in that
list, plus the starting number, gives the set.

An index past the end of the 18 sets is clamped to set 0 and raises a flag that
makes getshape AND the whole loaded set with 0xAA -- which forces every pixel's
low bit off, so the same artwork is drawn in a two-colour variant.

  python tools/mm1/wallsets.py            # every map's three sets
  python tools/mm1/wallsets.py --usage    # which maps use each set
"""
import os, sys, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib
from map_links import params

LISTPTRS, STARTNOS, NSETS = 0x043B, 0x0441, 18


def _exe():
    d = open(mmlib.path('MM.EXE'), 'rb').read()
    b = mmlib.DATA_SEG_FILE_BASE
    return d, b, (lambda o: struct.unpack('<H', d[b+o:b+o+2])[0])

EXE, BASE, WORD = _exe()


def resolve(key, maptype):
    """(key, map type) -> (set number, recoloured?)."""
    n = EXE[BASE + STARTNOS + maptype - 1]
    lst = WORD(LISTPTRS + 2 * (maptype - 1))
    i = 0
    while WORD(lst + 2*i) != key:
        i += 1
        if i > 64:
            return None, False
    n += i
    return (0, n > 0x13) if n >= 0x13 else (n - 1, False)


def sets(name):
    p = params(name)
    return [resolve((p[k+1] << 8) | p[k], p[1]) for k in (2, 4, 6)]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--usage':
        use = collections.defaultdict(list)
        for m in mmlib.MAPS:
            for s, _ in sets(m):
                if m not in use[s]:
                    use[s].append(m)
        for s in range(NSETS):
            print(f'  set {s:2d}  {len(use[s]):2d} maps  {" ".join(use[s][:8])}'
                  f'{" ..." if len(use[s]) > 8 else ""}')
        return
    for m in mmlib.MAPS:
        p = params(m)
        keys = ' '.join('%04X' % ((p[k+1] << 8) | p[k]) for k in (2, 4, 6))
        got = ' '.join(f'{s:2d}{"*" if r else " "}' for s, r in sets(m))
        print(f'  {m:<9s} type {p[1]}  keys {keys}  -> sets {got}')
    print('  (* = clamped and recoloured)')


if __name__ == '__main__':
    main()
