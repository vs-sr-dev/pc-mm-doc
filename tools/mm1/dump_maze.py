#!/usr/bin/env python3
"""Print a map's wall plane as ASCII, with X across and Y up.

  python tools/mm1/dump_maze.py sorpigal [plane]

plane 0 (default) is the physical wall plane; plane 1 is the second, per-side
plane. Per side: 0 open, 1 wall, 2 door, 3 special/solid.
Squares carrying an event (from the map's overlay) are marked with a *.
"""
import os, sys, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mmlib

name = sys.argv[1] if len(sys.argv) > 1 else 'sorpigal'
pl = int(sys.argv[2]) if len(sys.argv) > 2 else 0
p = mmlib.read_maze(name)[pl]

events = set()
try:
    from ovr_text import blocks
    data = blocks(name)[1]
    n = data[0xC972 - 0xC940]
    events = {(i >> 4, i & 15) for i in data[0xC973 - 0xC940:][:n]}
except Exception:
    pass

H = {0: '   ', 1: '---', 2: '=D=', 3: '###'}
V = {0: ' ', 1: '|', 2: 'D', 3: '#'}
sd = mmlib.side
print(f'{name}  (map {mmlib.MAPS.index(name)})  plane {pl}'
      + (f'  -- * = one of {len(events)} event squares' if events and pl == 0 else ''))
for y in range(15, -1, -1):
    print('    ' + ''.join('+' + H[sd(p, x, y, mmlib.S_PLUS_Y)] for x in range(16)) + '+')
    print(f'{y:2d}  ' + ''.join(V[sd(p, x, y, mmlib.S_MINUS_X)] + (' * ' if (x, y) in events else '   ')
                                for x in range(16)) + V[sd(p, 15, y, mmlib.S_PLUS_X)])
print('    ' + ''.join('+' + H[sd(p, x, 0, mmlib.S_MINUS_Y)] for x in range(16)) + '+')
print('    ' + ''.join(f'{x:<4d}' for x in range(16)))
