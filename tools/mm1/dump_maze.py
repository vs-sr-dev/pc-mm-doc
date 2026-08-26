#!/usr/bin/env python3
"""Print a map's wall plane as ASCII, oriented with north up.

The engine calls the north/south axis Y and the east/west axis X (doc 4), so
Y runs up the page and X across it.

  python tools/mm1/dump_maze.py sorpigal [plane]

plane 0 (default) is the physical wall plane; plane 1 is the second, per-side
plane. Per side: 0 open, 1 wall, 2 door, 3 special/solid.
Squares carrying an event (from the map's overlay) are marked with a *.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib

name = sys.argv[1] if len(sys.argv) > 1 else 'sorpigal'
pl = int(sys.argv[2]) if len(sys.argv) > 2 else 0
p = mmlib.read_maze(name)[pl]

events = set()
try:
    from ovr_text import blocks, has_events, NPARAM
    code, data = blocks(name)
    if has_events(code):
        n = data[NPARAM]
        events = {(i >> 4, i & 15) for i in data[NPARAM+1:NPARAM+1+n]}
except Exception:
    pass

H = {0: '   ', 1: '---', 2: '=D=', 3: '###'}
V = {0: ' ', 1: '|', 2: 'D', 3: '#'}
sd = mmlib.side
print(f'{name}  (map {mmlib.MAPS.index(name)})  plane {pl}'
      + (f'   * = one of {len(events)} event squares' if events and pl == 0 else ''))
print('    north is up (+Y), east is right (+X)\n')
for y in range(15, -1, -1):                       # north at the top
    print('     ' + ''.join('+' + H[sd(p, y, x, mmlib.S_NORTH)] for x in range(16)) + '+')
    print(f'Y={y:<2d} ' + ''.join(V[sd(p, y, x, mmlib.S_WEST)]
                                  + (' * ' if (y, x) in events else '   ')
                                  for x in range(16)) + V[sd(p, y, 15, mmlib.S_EAST)])
print('     ' + ''.join('+' + H[sd(p, 0, x, mmlib.S_SOUTH)] for x in range(16)) + '+')
print('     ' + ''.join(f'{x:<4d}' for x in range(16)) + '  X')
