#!/usr/bin/env python3
"""Print a map's wall plane as ASCII.

  python tools/mm1/dump_maze.py sorpigal [plane]

plane 0 (default) is the physical wall plane; plane 1 is the second,
per-side attribute plane. Values per side: 0 open, 1/2/3 wall variants.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]   # this game's lib, then shared tools/
import mmlib

name = sys.argv[1] if len(sys.argv) > 1 else 'sorpigal'
pl = int(sys.argv[2]) if len(sys.argv) > 2 else 0
planes = mmlib.read_maze(name)
p = planes[pl]
H = {0: '   ', 1: '---', 2: '=2=', 3: '=3='}
V = {0: ' ', 1: '|', 2: '2', 3: '3'}
print(f'{name}  (map {mmlib.MAPS.index(name)})  plane {pl}')
for y in range(15, -1, -1):
    print('    ' + ''.join('+' + H[mmlib.side(p, x, y, mmlib.W_PLUS_Y)] for x in range(16)) + '+')
    print(f'{y:2d}  ' + ''.join(V[mmlib.side(p, x, y, mmlib.W_MINUS_X)] + '   ' for x in range(16))
          + V[mmlib.side(p, 15, y, mmlib.W_PLUS_X)])
print('    ' + ''.join('+' + H[mmlib.side(p, x, 0, mmlib.W_MINUS_Y)] for x in range(16)) + '+')
print('    ' + ''.join(f'{x:<4d}' for x in range(16)))
