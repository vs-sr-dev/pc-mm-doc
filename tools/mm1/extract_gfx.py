#!/usr/bin/env python3
"""Extract every picture in the game to PNG.

  python tools/mm1/extract_gfx.py [outdir]

SCREEN0..9 are full 320x200 CGA frames. MONPIX.DTA holds 76 monster/scene
portraits, each 26 bytes (104 px) wide by 96 rows. Each WALLPIX.DTA set is
twelve wall sprites; the geometry comes from the tables getshape reads (doc 5).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]   # this game's lib, then shared tools/
import mmlib, png

out = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(out, exist_ok=True)

for n in range(10):
    png.write(f'{out}/screen{n}.png', 320, 200,
              mmlib.to_rgb(mmlib.read_screen(n), 80, 200))
print(f'{out}/screen0..9.png   10 frames, 320x200')

mons = mmlib.read_library('MONPIX.DTA')
imgs = [mmlib.to_rgb(m, 26, 96) for m in mons]
for k, im in enumerate(imgs):
    png.write(f'{out}/mon{k:02d}.png', 104, 96, im)
png.sheet(f'{out}/monsters.png', imgs, 10)
print(f'{out}/mon00..{len(mons)-1:02d}.png  {len(mons)} portraits, 104x96 (+ contact sheet)')

walls = mmlib.read_library('WALLPIX.DTA')
for k, w in enumerate(walls):
    for j, (bw, h, raw) in enumerate(mmlib.split_wallset(w)):
        png.write(f'{out}/wall{k:02d}_{j:02d}.png', bw*4, h,
                  mmlib.to_rgb(raw, bw, h))
print(f'{out}/wall00_00..{len(walls)-1:02d}_11.png  '
      f'{len(walls)} sets x {len(mmlib.WALL_SHAPES)} sprites')
